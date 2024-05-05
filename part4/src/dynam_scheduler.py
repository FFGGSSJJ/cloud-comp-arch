import docker
import json
import sys, threading, time
import resource_alert
import scheduler_logger

CORE_NUM = 4
img_prefix = 'anakli/cca:'

def cpu_flag2str(cpu_flag: int) -> list[str]:
    if (cpu_flag == 1):
        return ["3"]
    elif (cpu_flag == 2):
        return ["2", "3"]
    else:
        return ["1", "2", "3"]
    


'''
    Dynamic Scheduler 
'''
class DynamicScheduler:

    # make these static
    client_ = docker.from_env()
    cpu_flag_ = 2    # 0-2, refers to core num
    high_cpu_set_ = '1-3'
    default_cpu_set_ = '2-3'
    low_cpu_set_ = '3'


    def __init__(self, tags: list[str], containers_info: dict, log_cnt: int) -> None:
        self.img_tags_ = tags
        self.containerId_dict = {}  # TODO: should i store the id or cache the obj?
        self.sched_logger = scheduler_logger.SchedulerLogger(f"job_{log_cnt}.txt")

        try:
            self.init_scheduler(containers_info, True)
        except:
            self.delete_all()
            assert False, "DynamicScheduler Init Failed"

    def init_scheduler(self, containers_info: dict, imgInit: bool = True) -> None:
        """initialization for scheduler

        Args:
            imgInit (bool): whether to pull images, default True
            containersInfo (dict): the default info to create the containers
        """
        if (imgInit):
            self.pull_all()
        
        for img_tag in self.img_tags_:
            self.init_container(img_tag, containers_info[img_tag])
        
    def pull_all(self) -> None:
        for img_tag in self.img_tags_:
            print("[INFO]: pull", img_tag)
            self.client_.images.pull(img_prefix+img_tag)


    def init_container(self, img_tag: str, containers_info: dict) -> None:
        """create container using image with tag img_tag

        Args:
            imgTag (str): the image to use
            containers_info (dict): the default info to create the container
        """
        # create container, dont start yet
        containerObj = self.client_.containers.create(image=img_prefix+img_tag, name=img_tag, detach=True, auto_remove=False,
                                                      command=containers_info["command"],
                                                      cpuset_cpus=containers_info["cpu"])
        self.containerId_dict[img_tag] = containerObj.id
        return
    
    def delete_all(self) -> None:
        """remove all created or exited containers
        """
        for key in self.containerId_dict:
            try:
                print("[INFO]: remove "+key)
                self.client_.containers.get(self.containerId_dict[key]).remove(force=True)
            except:
                continue
    
    # start the container for running
    def start_container(self, containerId):
        containerObj = self.client_.containers.get(containerId)
        if (containerObj.status != "running" and containerObj.status != "exited"):
            containerObj.start()

            self.sched_logger.job_start(scheduler_logger.Job(containerObj.name), cpu_flag2str(self.cpu_flag_), 4)
            print("[INFO]: start " + containerObj.name)

    # update the container
    def update_container(self, containerId, cpu_set: str):
        containerObj = self.client_.containers.get(containerId)
        if (containerObj.status == "exited"):
            return
        containerObj.update(cpuset_cpus=cpu_set)

        self.sched_logger.update_cores(scheduler_logger.Job(containerObj.name), cpu_flag2str(self.cpu_flag_))
        print("[INFO]: update " + containerObj.name + " to " + cpu_set)
        

    def pause_container(self, containerId):
        containerObj = self.client_.containers.get(containerId)
        if (containerObj.status == "paused" or containerObj.status == "exited"):
            return
        else:
            containerObj.pause()

            self.sched_logger.job_pause(scheduler_logger.Job(containerObj.name))
            print("[INFO]: pause " + containerObj.name)

    def unpause_contaier(self, containerId):
        containerObj = self.client_.containers.get(containerId)
        if (containerObj.status == "paused"):
            containerObj.unpause()

            self.sched_logger.job_unpause(scheduler_logger.Job(containerObj.name))
            print("[INFO]: unpause " + containerObj.name)

    def get_container_status(self, containerId) -> str:
        return self.client_.containers.get(containerId).status
    
    def calc_container_util(self, pre_util, cur_util) -> float:
        try:
            delta_container_usage = cur_util['cpu_stats']['cpu_usage']['total_usage'] - pre_util['cpu_stats']['cpu_usage']['total_usage']
            delta_system_usage = cur_util['cpu_stats']['system_cpu_usage'] - pre_util['cpu_stats']['system_cpu_usage']
            percentage = round((delta_container_usage / delta_system_usage) * CORE_NUM * 100, 2)
            return percentage
        except:
            # in case of failure
            return 0.0
    
    def seq_dynamic_schedule(self, order_list: list[str], interval: float = 0.25):
        """ a dynamic scheduler for parsec jobs. 
        TODO: currently it is a sequential scheduler, upgrade/implement a parallel one

        Args:
            order_list (list): the list to execute job in order
            interval (float): update interval for resource alerter and job monitor
        """
        # open a logger
        loggerfd = open("./log", 'w')
        self.sched_logger.start()

        # start memcached process monitor thread
        memcachedAlt = resource_alert.ResourceAlert("memcached", 300.0, 50.0)
        memcachedAlt_thread = threading.Thread(target=memcachedAlt.keep_alterting, args=(interval,), daemon=True)
        memcachedAlt_thread.start()

        # start sequential scheduling policy
        exec_start = time.time()
        loggerfd.write("Exec starts at: "+str(exec_start)+"\n")

        for img in order_list:
            job_start = time.time()

            self.start_container(self.containerId_dict[img])
            loggerfd.write(img+" starts at: "+str(job_start)+"\n")

            pre_util = dSched.client_.api.stats(img, stream=False, one_shot=True)
            time.sleep(interval)
            while (self.get_container_status(self.containerId_dict[img]) != "exited"):
                # collect system info
                cur_util = dSched.client_.api.stats(img, stream=False, one_shot=True)
                container_cpu_util = self.calc_container_util(pre_util, cur_util)
                pre_util = cur_util

                eval = memcachedAlt.evaluate(self.cpu_flag_, container_cpu_util)

                # if current container is paused
                if (self.get_container_status(self.containerId_dict[img]) == "paused"):
                    # check feasibility to unpause
                    if (eval >= 2):
                        self.cpu_flag_ = 2
                        self.update_container(self.containerId_dict[img], self.default_cpu_set_)
                        self.unpause_contaier(self.containerId_dict[img])
                        continue
                    time.sleep(interval)
                    continue

                # evaluate system situation
                if (eval == 3):
                    if (self.cpu_flag_ == 3):
                        time.sleep(interval)
                        continue
                    print("[DEBUG]:\thealthy 3")
                    self.update_container(self.containerId_dict[img], self.high_cpu_set_)
                    self.cpu_flag_ = 3

                if (eval == 2):
                    if (self.cpu_flag_ == 2):
                        time.sleep(interval)
                        continue
                    print("[DEBUG]:\thealthy 2")
                    self.update_container(self.containerId_dict[img], self.default_cpu_set_)
                    self.cpu_flag_ = 2

                if (eval == 1):
                    if (self.cpu_flag_ == 1):
                        time.sleep(interval)
                        continue
                    print("[DEBUG]:\thealthy 1")
                    self.update_container(self.containerId_dict[img], self.low_cpu_set_)
                    self.cpu_flag_ = 1

                if (eval == 0):
                    print("[DEBUG]:\thealthy 0")
                    self.pause_container(self.containerId_dict[img])
                    self.cpu_flag_ = 0

                print("---")

            self.sched_logger.job_end(scheduler_logger.Job(img))

            job_end = time.time()
            job_time = job_end - job_start
            loggerfd.write(img+" ends at: "+str(job_start)+"\n")
            loggerfd.write(img+" takes: "+str(job_time)+"\n")
        
        self.sched_logger.end()

        exec_end = time.time()
        exec_time = exec_end - exec_start
        loggerfd.write("Exec ends at: "+str(exec_end)+"\n")
        loggerfd.write("Exec takes: "+str(exec_time)+"\n")

        # clean containers
        self.delete_all()

    # TODO
    def multi_dynamic_schedule():
        pass


if __name__ == "__main__":

    parsec_apps_tags = ['parsec_blackscholes', 'parsec_canneal', 'parsec_dedup', 'parsec_ferret', 'parsec_freqmine', 'splash2x_radix', 'parsec_vips']
    order_list = ['parsec_blackscholes', 'parsec_canneal', 'parsec_dedup', 'parsec_ferret', 'parsec_freqmine', 'splash2x_radix', 'parsec_vips']
    json_file = open("howto.json")
    containerJson = json.load(json_file)
    log_cnt = int(sys.argv[1])

    for key in containerJson:
        print(key)
        print(containerJson[key])

    dSched = DynamicScheduler(parsec_apps_tags, containerJson, log_cnt)
    try:
        dSched.seq_dynamic_schedule(order_list, 0.25)
    except Exception as e:
        print("[DEBUG]: Scheduler Failed")
        print(e.message) if hasattr(e, 'message') else print(e)
        dSched.delete_all()

    

    



        



