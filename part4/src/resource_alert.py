import psutil, time, sys, enum
import threading


'''
    Resource Alert
'''
class ResourceAlert:

    class Eval(enum.Enum):
        Full = 4
        Good = 3
        Medium = 2
        Mild = 1
        Bad = 0
    
    HIGH_CPU_FLAG = 1
    LOW_CPU_FLAG = 0

    # cpu_threshold_high_: float
    # cpu_threshold_low_: float

    def __init__(self, pName: str, threshold_high: float, threshold_low: float) -> None:
        # basic info
        self.pname_ = pName
        self.pid_ = self.get_pid()

        # cpu util
        self.util_lock_ = threading.Lock()
        self.proc_avg_cpu_util_ = 0.0

        #
        self.default_cpu_set_ = self.HIGH_CPU_FLAG
        self.low_cpu_set_ = self.LOW_CPU_FLAG
        self.core_num_ = 4

        #
        self.cpu_threshold_high_ = threshold_high
        self.cpu_threshold_low_ = threshold_low

    def get_pid(self) -> int:
        for proc in psutil.process_iter():
            if proc.name() == self.pname_:
                return proc.pid
        assert False, self.pname_+" process not found"
    
    def _change_cpu_affinity(self, cpu_affinity: int):
        """change cpu affinity of the process alterting, may not be necessary

        Args:
            cpu_affinity (int): 0 for low cpu set (0-1) and 1 for default cpu set (0-3)
        """
        if (cpu_affinity == self.LOW_CPU_FLAG and self.core_num_ > 2):
            p = psutil.Process(self.pid_)   
            p.cpu_affinity([0, 1])
            self.core_num_ = 2
            print("[INFO]: update memcached to 2 cores")
        elif (cpu_affinity == self.HIGH_CPU_FLAG and self.core_num_ < 4):
            p = psutil.Process(self.pid_)
            p.cpu_affinity([0, 1, 2, 3])
            self.core_num_ = 4
            print("[INFO]: update memcached to 4 cores")
        else:
            return
    
    def get_instant_proc_cpu_util(self) -> float:
        proc = psutil.Process(self.pid_)
        return proc.cpu_percent(interval=0.1)
    
    def get_avg_proc_cpu_util(self, interval: float) -> float:
        proc = psutil.Process(self.pid_)
        return proc.cpu_percent(interval=interval)

    def get_instant_total_cpu_util(self) -> float:
        utils: float
        while (utils := sum(psutil.cpu_percent(interval=0.1, percpu=True))) <= 0.1:
            continue
        return utils
    
    def get_instant_avg_cpu_util(self) -> float:
        """instantly return the avg cpu util of the process being alterting

        Returns:
            float: _description_
        """
        with self.util_lock_:
            return self.proc_avg_cpu_util_
    
    def evaluate(self, used_core_num: int, other_cpu_util: float) -> int:
        """evaulate system condition

        Args:
            used_core_num (int): used core num by jobs
            other_cpu_util (float): cpu utils by jobs

        Returns:
            int: evaluation, the recommended cpu_flag for the jobs
                 0: bad, pause the container -> 0 core
                 1: intermediate bad, update job cpu set to low_cpu_set -> 1 core
                 2: intermediate good, update job cpu set to default_cpu_set -> 2 cores
                 3: good, update job cpu set to high_cpu_set -> 3 cores
                 4: TODO
        """

        # total util, job util and proc util do not follow a relation due to the different calculation methods
        total_util = self.get_instant_total_cpu_util()

        proc_util = self.get_instant_avg_cpu_util()  # TODO: which cpu util to use?
        proc_util_rate = proc_util/(self.core_num_*100.0)

        # use docker stats to monitor container cpu usage
        job_util = total_util - proc_util if used_core_num > 0 else 0
        job_util = other_cpu_util if other_cpu_util > 0 else job_util
        job_util_rate = job_util/(used_core_num*100.0) if used_core_num > 0 else 0

        print("[INFO]: memcached util:\t"+str(proc_util)+"/"+str(self.core_num_*100.0))
        print("[INFO]: total util:\t"+str(total_util)+"/"+str(4*100.0))
        print("[INFO]: job util:\t"+str(job_util)+"/"+str(used_core_num*100.0))

        # < 25
        if (proc_util < self.cpu_threshold_low_/2):
            self._change_cpu_affinity(self.low_cpu_set_)
            return self.Eval.Full


        # < 50
        if (proc_util < self.cpu_threshold_low_):
            self._change_cpu_affinity(self.low_cpu_set_)
            return self.Eval.Good
        
        # > 300 TODO: potentially upgrade proc cpu set
        if (proc_util >= self.cpu_threshold_high_):
            self._change_cpu_affinity(self.default_cpu_set_)
            return self.Eval.Bad
        
        # 50 - 300 TODO: dynamically adjust threshold?
        if (proc_util >= self.cpu_threshold_low_ and proc_util < self.cpu_threshold_high_):
            # 200 - 300
            if (proc_util >= 200.0):
                self._change_cpu_affinity(self.default_cpu_set_)
                return self.Eval.Mild
            
            # 150 - 200 TODO: optimize?
            elif (proc_util >= 150.0):
                self._change_cpu_affinity(self.default_cpu_set_)
                if (used_core_num > 2):
                    return self.Eval.Medium
                elif (used_core_num == 2):
                    return self.Eval.Medium if job_util_rate >= 0.75 else self.Eval.Mild
                elif (used_core_num == 1):
                    return self.Eval.Medium if job_util_rate >= 2.0 else self.Eval.Mild
                else:
                    return self.Eval.Mild
            
            # 100 - 150
            elif (proc_util >= 100):
                if (proc_util_rate >= 0.7):
                    self._change_cpu_affinity(self.default_cpu_set_)
                if (used_core_num > 2):
                    return self.Eval.Medium
                elif (used_core_num == 2):
                    return self.Eval.Medium if job_util_rate >= 0.65 else self.Eval.Mild
                elif (used_core_num == 1):
                    return self.Eval.Medium if job_util_rate >= 1.2 else self.Eval.Mild
                else:
                    return self.Eval.Mild

            # 50 - 100 TODO: optimize!
            elif (proc_util >= 50.0):
                if (used_core_num > 2):
                    return self.Eval.Good if job_util_rate >= 1.0 and proc_util <= 75.0 else self.Eval.Medium
                elif (used_core_num == 2):
                    return self.Eval.Good if job_util_rate >= 1.0 and proc_util <= 75.0 else self.Eval.Medium
                else:
                    return self.Eval.Medium
            else:
                pass

        # otherwise
        return self.Eval.Bad
    
    def keep_alterting(self, interval: float = 0.25):
        while True:
            avg_util = self.get_avg_proc_cpu_util(interval)
            with self.util_lock_:
                self.proc_avg_cpu_util_ = avg_util
            


    
# function for part4.1.c
def measure_cpu_util(interval: float, test_file: str):
    memcachedAlt = ResourceAlert("memcached", 100, 100)
    fd = open(test_file, 'w')

    # omit the idle time
    while (memcachedAlt.get_instant_proc_cpu_util() <= 1.0):
        continue

    while True:
        timeNow = time.time()
        avg_util = memcachedAlt.get_avg_proc_cpu_util(interval)
        if (avg_util < 1.0):
            break
        row = str(timeNow) + " " + str(avg_util) + "\n"
        print(row)
        fd.write(row)
    
    fd.close()


# for part4.1.c only
if __name__== "__main__":
    test_file = sys.argv[1]
    measure_cpu_util(5.0, test_file)