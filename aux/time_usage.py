import time


def time_usage(func):
    def wrapper(*args, **kwargs):
        beg_ts = time.time()
        retval = func(*args, **kwargs)
        end_ts = time.time()
        elapsed_time = "Elapsed time: %.2f" % (end_ts - beg_ts)
        return retval + '  ' + elapsed_time + ' sec'
    return wrapper


@time_usage
def test():
    for i in range(10000000):
        pass
    return ''

if __name__ == "__main__":
    print(test())
