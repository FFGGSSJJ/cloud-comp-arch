import psutil, time, sys
import threading

'''
    Resource Alert
'''
class ResourceAlert:

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
        self.default_cpu_set_ = '0-3'
        self.low_cpu_set_ = '0-1'
        self.default_ = True

        #
        self.cpu_threshold_high_ = threshold_high
        self.cpu_threshold_low_ = threshold_low

    def get_pid(self) -> int:
        for proc in psutil.process_iter():
            if proc.name() == self.pname_:
                return proc.pid
        assert False, self.pname_+" process not found"
    
    def change_cpu_affinity(self, cpu_affinity: list[int]):
        """change cpu affinity of the process alterting, may not be necessary

        Args:
            cpu_affinity (list[int]): _description_
        """
        p = psutil.Process(self.pid_)
        p.cpu_affinity(cpu_affinity)
    
    def get_instant_proc_cpu_util(self) -> float:
        proc = psutil.Process(self.pid_)
        return proc.cpu_percent(interval=0.1)
    
    def get_avg_proc_cpu_util(self, interval: float) -> float:
        proc = psutil.Process(self.pid_)
        return proc.cpu_percent(interval=interval)

    def get_instant_total_cpu_util(self) -> float:
        utils = psutil.cpu_percent(interval=0.1, percpu=True)
        return sum(utils)
    
    def get_instant_avg_cpu_util(self) -> float:
        """instantly return the avg cpu util of the process being alterting

        Returns:
            float: _description_
        """
        with self.util_lock_:
            return self.proc_avg_cpu_util_
    
    def evaluate(self, other_core_num: int) -> int:
        cur_util = self.get_instant_avg_cpu_util()
        total_util = self.get_instant_total_cpu_util()

        print("memcached util: "+str(cur_util))
        print("total util: "+str(total_util))

        # TODO: potentially downgrade cpu set
        if (cur_util < self.cpu_threshold_low_):
            return 0
        
        # TODO: potentially upgrade cpu set
        if (cur_util > self.cpu_threshold_high_):
            return 3
        
        # memcached 50-250
        # TODO: dynamic adjust threshold
        if (cur_util >= self.cpu_threshold_low_ and cur_util < self.cpu_threshold_high_):
            # batch job takes the majority
            if (cur_util/total_util <= 0.33):
                return 2
            
            # memcached takes the majority
            if (cur_util/total_util >= 0.66):
                return 1
        
        return 3
    
    def keep_alterting(self, interval: float = 0.25):
        while True:
            avg_util = self.get_avg_proc_cpu_util(interval)
            with self.util_lock_:
                self.proc_avg_cpu_util_ = avg_util
            


    
# function for part4.1.c
def measure_cpu_util(interval: float, test_file: str):
    memcachedAlt = ResourceAlert("memcached")
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