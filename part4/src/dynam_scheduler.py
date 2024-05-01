import docker, psutil
import json
import sys, threading, time
import resource_alert

CORE_NUM = 4
img_prefix = 'anakli/cca:'


'''
    Dynamic Scheduler 
'''
class DynamicScheduler:

    # make these static
    client_ = docker.from_env()
    cpu_flag_ = 1    # 0-2, refers to evaluation level
    default_cpu_set_ = '2-3'
    high_cpu_set_ = '1-3'
    low_cpu_set_ = '3'


    def __init__(self, tags: list[str], containersInfo: dict) -> None:
        self.img_tags_ = tags
        self.containerId_dict = {}  # TODO: should i store the id or cache the obj?
        try:
            self.init_scheduler(containersInfo, True)
        except:
            self.delete_all()
            assert False, "DynamicScheduler Init Failed"

    def init_scheduler(self, containersInfo: dict, imgInit: bool = True) -> None:
        """initialization for scheduler

        Args:
            imgInit (bool): whether to pull images, default True
            containersInfo (dict): the default info to create the containers
        """
        if (imgInit):
            self.pull_all()
        
        for imgTag in self.img_tags_:
            self.init_container(imgTag, containersInfo[imgTag])
        
    def pull_all(self) -> None:
        for imgTag in self.img_tags_:
            print("pull", imgTag)
            ret = self.client_.images.pull(img_prefix+imgTag)


    def init_container(self, imgTag: str, containerInfo: dict) -> None:
        """create container using image with tag img_tag

        Args:
            imgTag (str): the image to use
            containerInfo (dict): the default info to create the container
        """
        # create container, dont start yet
        containerObj = self.client_.containers.create(image=img_prefix+imgTag, name=imgTag, detach=True, auto_remove=False,
                                                      command=containerInfo["command"],
                                                      cpuset_cpus=containerInfo["cpu"])
        self.containerId_dict[imgTag] = containerObj.id
        return
    
    def delete_all(self) -> None:
        """remove all created or exited containers
        """
        for key in self.containerId_dict:
            try:
                containerObj = self.client_.containers.get(self.containerId_dict[key])
                containerObj.remove(force=True)
            except:
                continue
    
    # start the container for running
    def start_container(self, containerId):
        containerObj = self.client_.containers.get(containerId)
        if (containerObj.status != "running" and containerObj.status != "exited"):
            containerObj.start()
            print("[INFO]: start " + containerObj.name)

    # update the container
    def update_container(self, containerId, cpu_set: str):
        containerObj = self.client_.containers.get(containerId)
        containerObj.update(cpuset_cpus=cpu_set)
        print("[INFO]: update " + containerObj.name + " to " + cpu_set)
        

    def pause_container(self, containerId):
        containerObj = self.client_.containers.get(containerId)
        if (containerObj.status == "paused" or containerObj.status == "exited"):
            return
        else:
            containerObj.pause()
            print("[INFO]: pause " + containerObj.name)

    def unpause_contaier(self, containerId):
        containerObj = self.client_.containers.get(containerId)
        if (containerObj.status == "paused"):
            containerObj.unpause()
            print("[INFO]: unpause " + containerObj.name)

    def get_container_status(self, containerId) -> str:
        containerObj = self.client_.containers.get(containerId)
        return containerObj.status
    
    def dynamic_schedule(self, orderList: list):
        """ a dynamic scheduler for parsec jobs. 
        TODO: currently it is a sequential scheduler, upgrade/implement to a parallel one

        Args:
            orderList (list): the list to execute job in order
        """
        # open a logger
        loggerfd = open("./log", 'w')

        # start memcached process monitor thread
        memcachedAlt = resource_alert.ResourceAlert("memcached", 150.0, 50.0)
        memcachedAltThread = threading.Thread(target=memcachedAlt.keep_alterting, args=(0.25,), daemon=True)
        memcachedAltThread.start()

        # TODO: parsec job monitor thread?

        # TODO: pause/unpause not supportted for bad-health system
        # start sequential scheduling policy
        execStart = time.time()
        loggerfd.write("Exec starts at: "+str(execStart)+"\n")

        for img in orderList:
            jobStart = time.time()
            self.start_container(self.containerId_dict[img])
            loggerfd.write(img+" starts at: "+str(jobStart)+"\n")

            while (self.get_container_status(self.containerId_dict[img]) != "exited"):
                time.sleep(0.25)

                eval = memcachedAlt.evaluate(self.cpu_flag_)

                # if paused container
                if (self.get_container_status(self.containerId_dict[img]) == "paused"):
                    # check feasibility to unpause
                    if (eval < 2):
                        self.cpu_flag_ = 1
                        self.update_container(self.containerId_dict[img], self.default_cpu_set_)
                        self.unpause_contaier(self.containerId_dict[img])
                        continue
                    continue

                # evaluate system situation
                if (eval == 0):
                    if (self.cpu_flag_ == 1):
                        continue
                    print("healthy: 0")
                    self.update_container(self.containerId_dict[img], self.default_cpu_set_)
                    self.cpu_flag_ = 1

                if (eval == 1):
                    if (self.cpu_flag_ == 1):
                        continue
                    print("healthy: 1")
                    self.update_container(self.containerId_dict[img], self.default_cpu_set_)
                    self.cpu_flag_ = 1

                if (eval == 2):
                    if (self.cpu_flag_ == 2):
                        continue
                    print("healthy: 2")
                    self.update_container(self.containerId_dict[img], self.low_cpu_set_)
                    self.cpu_flag_ = 2

                if (eval == 3):
                    print("healthy: 3")
                    self.pause_container(self.containerId_dict[img])

                print("---")
                # self.pause_container(self.containerId_dict[img])

            jobEnd = time.time()
            jobTime = jobEnd - jobStart

            loggerfd.write(img+" ends at: "+str(jobStart)+"\n")
            loggerfd.write(img+" takes: "+str(jobTime)+"\n")
            print("\n----- Job Exec Time -----\n")
            print(img+": "+str(jobTime)+"s")
            print("\n----- ------------- -----\n")
        
        execEnd = time.time()
        execTime = execEnd - execStart
        loggerfd.write("Exec ends at: "+str(execEnd)+"\n")
        loggerfd.write("Exec takes: "+str(execTime)+"\n")
        
        print("\n====== Total Exec Time ======\n")
        print(str(execTime)+"s")
        print("\n====== =============== ======\n")

        # clean containers
        self.delete_all()


if __name__ == "__main__":

    parsec_apps_tags = ['parsec_blackscholes', 'parsec_canneal', 'parsec_dedup', 'parsec_ferret', 'parsec_freqmine', 'splash2x_radix', 'parsec_vips']
    order_list = ['parsec_blackscholes', 'parsec_canneal', 'parsec_dedup', 'parsec_ferret', 'parsec_freqmine', 'splash2x_radix', 'parsec_vips']
    jsonFile = open("howto.json")
    containerJson = json.load(jsonFile)
    for key in containerJson:
        print(key)
        print(containerJson[key])

    dSched = DynamicScheduler(parsec_apps_tags, containerJson)
    try:
        dSched.dynamic_schedule(order_list)
    except:
        dSched.delete_all()

    

    



        



