from time import sleep

ONE_MINUTE = 1

class Timer:
    def __init__(self, time):
        self._time = time

    def __call__(self):
        self._timer_start()
        for i in range(self._time):
            sleep(ONE_MINUTE)
            self._minute_elapsed(i+1)
        return self._timer_done()

    def _minute_elapsed(self, i):
        print "{}/{}".format(i, self._time)

    def _timer_start(self):
        print "Starting."

    def _timer_end(self):
        print "Done!"

if __name__ == '__main__':
    Timer(25)()
