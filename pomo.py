import time
import subprocess

ONE_MINUTE = 60

class Config:
    def __init__(self, config):
        self._config = config

    def get(self, attr):
        return self._config[attr]
        

class Timer:
    def __init__(self, config):
        self._config = config

    def __call__(self):
        self._timer_start()
        for i in range(self._config.get("minutes")):
            time.sleep(ONE_MINUTE)
            self._minute_elapsed(i+1)
        return self._timer_end()

    def _play(self, file):
        subprocess.Popen([self._config.get("player"), file])

    def _minute_elapsed(self, i):
        self._play(self._config.get("minute_elapsed_sound"))
        print "{}/{}".format(i, self._config.get("minutes"))

    def _timer_start(self):
        self._play(self._config.get("timer_start_sound"))
        print "Starting."

    def _timer_end(self):
        self._play(self._config.get("timer_end_sound"))
        print "Done!"

if __name__ == '__main__':
    config = Config({
        "minutes": 25,
        "minute_elapsed_sound": "resources/samples/tick.wav",
        "timer_start_sound": "resources/samples/chiming pottery02.wav",
        "timer_end_sound": "resources/samples/applause.wav",
        "player": "paplay"})
    Timer(config)()
