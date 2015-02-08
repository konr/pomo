import time
import os
import json
import subprocess
from abc import ABCMeta, abstractmethod

ONE_MINUTE = 60

def epoch():
    return int(time.time())

class Configurable:
    def __init__(self, config):
        self._config = config

class TimerHook(object):
    __metaclass__ = ABCMeta

    def __init__(self, config):
        self._config = config

    @abstractmethod
    def start(self): pass

    @abstractmethod
    def tick(self, i, n): pass

    @abstractmethod
    def end(self): pass

class Config(Configurable):

    def get(self, attr):
        return self._config[attr]
        
class EAVTLogger(Configurable):

    def __call__(self, e, a, v, t=None):
        t = t or epoch()
        with open(os.environ["HOME"] + "/" + self._config.get("log_file"), "a") as f:
            f.write(json.dumps({"e": e, "a": a, "v": v, "t": t}))

    def gen_entity(self, prefix):
        return "{}-{}".format(prefix, epoch())

class Pomodoro(TimerHook):
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
        
class VisualAlerter(TimerHook):

    def start(self):
        print "Starting."

    def tick(self, i, n):
        print "{}/{}".format(i, n)
        
    def end(self):
        print "Starting."

class AuralAlerter(TimerHook):

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
        "log_file": ".pomo_log",
        "minute_elapsed_sound": "resources/samples/tick.wav",
        "timer_start_sound": "resources/samples/chiming pottery02.wav",
        "timer_end_sound": "resources/samples/applause.wav",
        "player": "paplay"})
    Timer(config)()
