import docker
import json
import sys, threading, time
import resource_alert
import scheduler_logger
import random, argparse

CORE_NUM = 4
img_prefix = 'anakli/cca:'

def parse_arguments():
    parser = argparse.ArgumentParser(description='Dynamic Scheduler Options')
    parser.add_argument('--count', help='Log number count', type=int)
    parser.add_argument('--interval', help='The monitoring interval', type=float, default=0.25)
    parser.add_argument('--seq', help='Use the sequential scheduler', action='store_true')
    parser.add_argument('--mul', help='Use the multi-switch scheduler', action='store_true')
    return parser.parse_args()


'''
    Dynamic Scheduler 
'''
class DynamicScheduler:

    # make these static
    client_ = docker.from_env()
    cpu_flag_ = 2    # 0-2, refers to core num
    full_cpu_set_ = '0-3'
    high_cpu_set_ = '1-3'
    default_cpu_set_ = '2-3'
    low_cpu_set_ = '3'
    cpu_flag_map_ = {4: full_cpu_set_,
                     3: high_cpu_set_,
                     2: default_cpu_set_,
                     1: low_cpu_set_}


    def __init__(self, tags: list[str], containers_info: dict, log_cnt: int) -> None:
        self.img_tags_ = tags
        self.containerId_dict = {}  # TODO: should i store the id or cache the obj?
        self.sched_logger = scheduler_logger.SchedulerLogger(f"logs/job_{log_cnt}.txt")

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

            self.sched_logger.job_start(scheduler_logger.Job(containerObj.name), scheduler_logger.cpu_flag2str(self.cpu_flag_), 4)
            print("[INFO]: start " + containerObj.name)

    # update the container
    def update_container(self, containerId, cpu_set: str):
        try:
            containerObj = self.client_.containers.get(containerId)
            if (containerObj.status != "exited"):
                containerObj.update(cpuset_cpus=cpu_set)
                print("[INFO]: update " + containerObj.name + " to " + cpu_set)
                self.sched_logger.update_cores(scheduler_logger.Job(containerObj.name), scheduler_logger.cpu_flag2str(self.cpu_flag_))
        except docker.errors.APIError as e:
            print(f"[DEBUG]: API error occurred - {e}, pass")
        except:
            print("[DEBUG]: update failed, pass")

    def pause_container(self, containerId):
        try:
            containerObj = self.client_.containers.get(containerId)
            if (containerObj.status == "paused" or containerObj.status == "exited"):
                return
            else:
                containerObj.pause()
                self.sched_logger.job_pause(scheduler_logger.Job(containerObj.name))
                print("[INFO]: pause " + containerObj.name)
        except docker.errors.APIError as e:
            print(f"[DEBUG]: API error occurred - {e}")
        except:
            print("[DEBUG]: pause container failed, pass")

    def unpause_contaier(self, containerId):
        try:
            containerObj = self.client_.containers.get(containerId)
            if (containerObj.status == "paused"):
                containerObj.unpause()

                self.sched_logger.job_unpause(scheduler_logger.Job(containerObj.name))
                print("[INFO]: unpause " + containerObj.name)
        except:
            print("[DEBUG]: unpause container failed, pass")

    def get_container_status(self, containerId) -> str:
        return self.client_.containers.get(containerId).status
    
    def get_container_stats(self, containerId):
        containerObj = self.client_.containers.get(containerId)
        try:
            if containerObj.status != "exited" or containerObj.status != "paused":
                return containerObj.stats(stream=False, one_shot=True)
            return None
        except:
            return None
    
    def calc_container_util(self, pre_util, cur_util) -> float:
        if (pre_util == None):
            return 0.0
        
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
        memcachedAlt = resource_alert.ResourceAlert("memcached", self.sched_logger, 300.0, 50.0)
        memcachedAlt_thread = threading.Thread(target=memcachedAlt.keep_alterting, args=(interval,), daemon=True)
        memcachedAlt_thread.start()

        # start sequential scheduling policy
        exec_start = time.time()
        loggerfd.write("Exec starts at: "+str(exec_start)+"\n")

        for img in order_list:
            job_start = time.time()

            self.start_container(self.containerId_dict[img])
            loggerfd.write(img+" starts at: "+str(job_start)+"\n")

            pre_util = self.get_container_stats(self.containerId_dict[img])
            time.sleep(interval)
            while (self.get_container_status(self.containerId_dict[img]) != "exited"):
                # collect system info
                cur_util = self.get_container_stats(self.containerId_dict[img])
                container_cpu_util = self.calc_container_util(pre_util, cur_util)
                pre_util = cur_util

                eval = memcachedAlt.evaluate(self.cpu_flag_, container_cpu_util)

                # if current container is paused
                if (self.get_container_status(self.containerId_dict[img]) == "paused"):
                    # check feasibility to unpause
                    if (eval == memcachedAlt.Eval.Medium or eval == memcachedAlt.Eval.Good or eval == memcachedAlt.Eval.Full):
                        self.cpu_flag_ = 2
                        self.update_container(self.containerId_dict[img], self.default_cpu_set_)
                        self.unpause_contaier(self.containerId_dict[img])
                        continue
                    time.sleep(interval)
                    continue

                # evaluate system situation
                if (eval == memcachedAlt.Eval.Full):
                    if (self.cpu_flag_ == 4):
                        time.sleep(interval)
                        continue
                    print("[DEBUG]:\thealthy 4")
                    self.update_container(self.containerId_dict[img], self.full_cpu_set_)
                    self.cpu_flag_ = 4
                
                if (eval == memcachedAlt.Eval.Good):
                    if (self.cpu_flag_ == 3):
                        time.sleep(interval)
                        continue
                    print("[DEBUG]:\thealthy 3")
                    self.update_container(self.containerId_dict[img], self.high_cpu_set_)
                    self.cpu_flag_ = 3

                if (eval == memcachedAlt.Eval.Medium):
                    if (self.cpu_flag_ == 2):
                        time.sleep(interval)
                        continue
                    print("[DEBUG]:\thealthy 2")
                    self.update_container(self.containerId_dict[img], self.default_cpu_set_)
                    self.cpu_flag_ = 2

                if (eval == memcachedAlt.Eval.Mild):
                    if (self.cpu_flag_ == 1):
                        time.sleep(interval)
                        continue
                    print("[DEBUG]:\thealthy 1")
                    self.update_container(self.containerId_dict[img], self.low_cpu_set_)
                    self.cpu_flag_ = 1

                if (eval == memcachedAlt.Eval.Bad):
                    print("[DEBUG]:\thealthy 0")
                    self.pause_container(self.containerId_dict[img])
                    self.cpu_flag_ = 0

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

class MultiDynamicScheduler(DynamicScheduler):
    

    def __init__(self, tags: list[str], containers_info: dict, log_cnt: int, cpu_intensive_queue: list[str], cpu_friendly_queue: list[str]) -> None:
        super().__init__(tags, containers_info, log_cnt)
        
        self.active_container_: str
        self.idle_container_: str
        self.cpu_intensive_flag_ = False

        self.cpu_intensive_queue_ = cpu_intensive_queue
        self.cpu_friendly_queue_ = cpu_friendly_queue

    def launch_container(self, containerId, cpu_flag: int = 2):
        self.update_container(containerId, self.cpu_flag_map_[cpu_flag])
        self.cpu_flag_ = cpu_flag

        status = self.get_container_status(containerId)
        if (status == "created"):
            self.start_container(containerId)
        elif (status == "paused"):
            self.unpause_contaier(containerId)
        else:
            return

    def switch_container(self, cpu_flag: int = 2):
        if (self.idle_container_ != "empty" and self.active_container_ != self.idle_container_):
            self.pause_container(self.containerId_dict[self.active_container_])
            self.launch_container(self.containerId_dict[self.idle_container_], cpu_flag)
            # swap
            self.cpu_intensive_flag_ = not self.cpu_intensive_flag_
            self.active_container_, self.idle_container_ = self.idle_container_, self.active_container_
        else:
            return
        

    def multi_dynamic_schedule(self, interval: float = 0.25):
        # open a logger
        self.sched_logger.start()

        # start memcached process monitor thread
        memcachedAlt = resource_alert.ResourceAlert("memcached", self.sched_logger, 300.0, 50.0)
        memcachedAlt_thread = threading.Thread(target=memcachedAlt.keep_alterting, args=(0.1,), daemon=True)
        memcachedAlt_thread.start()

        # initialization
        self.active_container_ = self.cpu_friendly_queue_[0]
        self.idle_container_ = self.cpu_intensive_queue_[0]
        self.start_container(self.containerId_dict[self.active_container_])
        self.cpu_intensive_flag_ = False

        # start scheduler
        pre_util = self.get_container_stats(self.containerId_dict[self.active_container_])
        while (len(self.cpu_friendly_queue_) > 0 or len(self.cpu_intensive_queue_) > 0):
            # if current active container finishes
            if (self.get_container_status(self.containerId_dict[self.active_container_]) == "exited"):
                self.sched_logger.job_end(scheduler_logger.Job(self.active_container_))

                # pop out finished job
                if (self.cpu_intensive_flag_ and len(self.cpu_intensive_queue_) > 0):
                    self.cpu_intensive_queue_.pop(0)
                elif (not self.cpu_intensive_flag_ and len(self.cpu_friendly_queue_) > 0):
                    self.cpu_friendly_queue_.pop(0)
                else:
                    pass
                
                # check stop condition
                if (len(self.cpu_friendly_queue_) == 0 and len(self.cpu_intensive_queue_) == 0):
                    break

                # determine next active/idle container
                self.active_container_ = self.cpu_friendly_queue_[0] if len(self.cpu_friendly_queue_) > 0 else self.cpu_intensive_queue_[0]
                self.cpu_intensive_flag_ = (len(self.cpu_friendly_queue_) == 0)
                self.idle_container_ = self.cpu_intensive_queue_[0] if len(self.cpu_intensive_queue_) > 0 else "empty"
                self.launch_container(self.containerId_dict[self.active_container_])
                pre_util = self.get_container_stats(self.containerId_dict[self.active_container_])
                time.sleep(interval)
                continue
            
            # orchestration starts here

            # collect system info
            cur_util = self.get_container_stats(self.containerId_dict[self.active_container_])
            container_cpu_util = self.calc_container_util(pre_util, cur_util)
            pre_util = cur_util

            eval = memcachedAlt.evaluate(self.cpu_flag_, container_cpu_util)

            # if current container is paused
            if (self.get_container_status(self.containerId_dict[self.active_container_]) == "paused"):
                # check feasibility to unpause
                if (eval == memcachedAlt.Eval.Medium or eval == memcachedAlt.Eval.Good or eval == memcachedAlt.Eval.Full):
                    self.cpu_flag_ = 2
                    self.launch_container(self.containerId_dict[self.active_container_])
                time.sleep(interval)
                continue

            # evaluate system situation
            if (eval == memcachedAlt.Eval.Full):
                if (not self.cpu_intensive_flag_):
                    self.switch_container(3)
                if (self.cpu_flag_ == 3):
                    time.sleep(interval)
                    continue
                print("[DEBUG]:\thealthy 4")
                self.update_container(self.containerId_dict[self.active_container_], self.high_cpu_set_)
                self.cpu_flag_ = 3
            
            if (eval == memcachedAlt.Eval.Good):
                if (self.cpu_flag_ == 3):
                    time.sleep(interval)
                    continue

                print("[DEBUG]:\thealthy 3")
                self.update_container(self.containerId_dict[self.active_container_], self.high_cpu_set_)
                self.cpu_flag_ = 3
            
            if (eval == memcachedAlt.Eval.Medium):
                if (self.cpu_flag_ == 2):
                    time.sleep(interval)
                    continue

                print("[DEBUG]:\thealthy 2")
                self.update_container(self.containerId_dict[self.active_container_], self.default_cpu_set_)
                self.cpu_flag_ = 2

            if (eval == memcachedAlt.Eval.Mild):
                if (self.cpu_intensive_flag_):
                    self.switch_container(1)
                if (self.cpu_flag_ == 1):
                    time.sleep(interval)
                    continue

                print("[DEBUG]:\thealthy 1")
                self.update_container(self.containerId_dict[self.active_container_], self.low_cpu_set_)
                self.cpu_flag_ = 1
            
            if (eval == memcachedAlt.Eval.Bad):
                print("[DEBUG]:\thealthy 0")
                self.pause_container(self.containerId_dict[self.active_container_])
                self.cpu_flag_ = 0

        self.sched_logger.end()

         # clean containers
        self.delete_all()

if __name__ == "__main__":

    parsec_apps_tags = ['parsec_blackscholes', 'parsec_canneal', 'parsec_dedup', 'parsec_ferret', 'parsec_freqmine', 'splash2x_radix', 'parsec_vips']
    order_list = ['parsec_blackscholes', 'parsec_canneal', 'parsec_dedup', 'parsec_ferret', 'parsec_freqmine', 'splash2x_radix', 'parsec_vips']
    time_order_list = ['parsec_freqmine', 'parsec_ferret', 'parsec_canneal', 'parsec_blackscholes', 'parsec_vips', 'parsec_dedup', 'splash2x_radix']

    # predetermined queues
    cpu_intensive_list = ['parsec_dedup', 'parsec_ferret', 'parsec_freqmine']
    cpu_friendly_list = ['parsec_canneal', 'parsec_blackscholes', 'parsec_vips', 'splash2x_radix']

    the_args = parse_arguments()
    log_cnt = the_args.count
    
    json_file = open("job_init.json")
    containerJson = json.load(json_file)

    print(the_args)
    pass

    if (the_args.seq):
        dSched = DynamicScheduler(parsec_apps_tags, containerJson, log_cnt)
        try:
            random.shuffle(order_list)
            dSched.seq_dynamic_schedule(order_list, float(the_args.interval))
        except Exception as e:
            print("[DEBUG]: Seq Scheduler Failed")
            print(e.message) if hasattr(e, 'message') else print(e)
            dSched.delete_all()
    else:
        mSched = MultiDynamicScheduler(parsec_apps_tags, containerJson, log_cnt, cpu_intensive_list, cpu_friendly_list)
        try:
            mSched.multi_dynamic_schedule(float(the_args.interval))
        except Exception as e:
            print("[DEBUG]: Mul Scheduler Failed")
            print(e.message) if hasattr(e, 'message') else print(e)
            mSched.delete_all()

    

    



        



