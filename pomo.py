import time
import subprocess

ONE_MINUTE = 1

def epoch():
    return int(time.time())

class Config:
    def __init__(self, config):
        self._config = config

    def get(self, attr):
        return self._config[attr]
        
class EAVTLogger:
    def __init__(self, config):
        self._config = config

    def __call__(self, e, a, v, t=None):
        pass

    def gen_entity(self, prefix):
        return "{}-{}".format(prefix, epoch())

class Pomodoro:
    def __init__(self, config):
        self._logger = EAVTLogger(config)
        self._entity = self._logger.gen_entity("pomodoro")
        self._minutes_elapsed = 0

    def start(self):
        self._logger(self._entity, "status", "started")

    def tick(self, i, n):
        self._minutes_elapsed += 1
        self._logger(self._entity, "minutes_elapsed", "{}".format(self._minutes_elapsed))

    def end(self):
        self._logger(self._entity, "status", "ended")
        
class VisualAlerter:
    def __init__(self, config):
        self._config = config

    def start(self):
        print "Starting."

    def tick(self, i, n):
        print "{}/{}".format(i, n)
        
    def end(self):
        print "Starting."

class AuralAlerter:
    def __init__(self, config):
        self._config = config

    def _play(self, file):
        subprocess.Popen([self._config.get("player"), file])

    def start(self):
        self._play(self._config.get("timer_start_sound"))

    def tick(self, i, n):
        self._play(self._config.get("minute_elapsed_sound"))
        
    def end(self):
        self._play(self._config.get("timer_end_sound"))
    

class Timer:
    def __init__(self, config):
        self._config = config

        pomodoro = Pomodoro(config)
        sound = AuralAlerter(config)
        video = VisualAlerter(config)

        self._hooks = [pomodoro, sound, video]

    def __call__(self):

        [x.start() for x in self._hooks]

        n = self._config.get("minutes")
        for i in range(n):
            time.sleep(ONE_MINUTE)
            [x.tick(i+1, n) for x in self._hooks]

        [x.end() for x in self._hooks]

if __name__ == '__main__':
    config = Config({
        "minutes": 25,
        "minute_elapsed_sound": "resources/samples/tick.wav",
        "timer_start_sound": "resources/samples/chiming pottery02.wav",
        "timer_end_sound": "resources/samples/applause.wav",
        "player": "paplay"})
    Timer(config)()
