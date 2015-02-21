import time
import os
import string
import json
from datetime import datetime
import subprocess
from abc import ABCMeta, abstractmethod
import sys

ONE_MINUTE = 60
ONE_HOUR = 60*ONE_MINUTE

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

    def start(self, goal):
        self._logger(self._entity, "status", "started")
        self._logger(self._entity, "started_at", epoch())
        self._logger(self._entity, "goal", goal)

    def tick(self, i, n):
        self._minutes_elapsed += 1
        self._logger(self._entity, "minutes_elapsed", "{}".format(self._minutes_elapsed))

    def end(self):
        self._logger(self._entity, "status", "ended")
        
class VisualAlerter(TimerHook):

    def start(self, goal):
        if goal:
            print "Good luck with '{}'!".format(goal)
        else:
            print "Starting."

    def tick(self, i, n):
        print "{}/{}".format(i, n)
        
    def end(self):
        print "Starting."

class AuralAlerter(TimerHook):

    def _play(self, file):
        subprocess.Popen([self._config.get("player"), file])

    def start(self, irrelevant):
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

    def __call__(self, goal=None):

        [x.start(goal) for x in self._hooks]

        n = self._config.get("minutes")
        for i in range(n):
            time.sleep(ONE_MINUTE)
            [x.tick(i+1, n) for x in self._hooks]

        [x.end() for x in self._hooks]

class Analyser:
    def __init__(self, config):
        self._config = config
        self._summary = {}
        self._data = []

    def _read(self):
        with open(os.environ["HOME"] + "/" + self._config.get("log_file"), "r") as f:
            data = f.read()
        data = "[" + data.replace("}{", "},{") + "]"
        # FIX sort by t
        self._data = json.loads(data)
        return self._data

    def __assert_exists(self, entity):
        data = self._summary.get(entity, {})
        self._summary[entity] = data

    def __process_status(self, datum):
        if datum["v"] == "started":
            self._summary[datum["e"]].update({"started": True, "started_at": datum["t"]}) # FIX backwards compat
        elif datum["v"] == "ended":
            self._summary[datum["e"]].update({"ended": True})
        else:
            raise Exception("unknown value '{}'".format(datum["v"]))
        
    def __process_minutes_elapsed(self, datum):
        self._summary[datum["e"]].update({"minutes_elapsed": int(datum["v"])})
        
    def __process_goal(self, datum):
        self._summary[datum["e"]].update({"goal": datum["v"]})

    def __process_started_at(self, datum):
        self._summary[datum["e"]].update({"started_at": datum["v"]})

    def _parse(self, datum):
        self.__assert_exists(datum["e"])
        if datum["a"] == "status":
            self.__process_status(datum)
        elif datum["a"] == "minutes_elapsed":
            self.__process_minutes_elapsed(datum)
        elif datum["a"] == "goal":
            self.__process_goal(datum)
        elif datum["a"] == "started_at":
            self.__process_started_at(datum)
        else:
            raise Exception("unknown attribute '{}'".format(datum["a"]))

    def summarize(self):
        now = epoch()

        pomodoros_list = [v for k,v in self._summary.iteritems()]
        not_aborted = [x for x in pomodoros_list if x.get("minutes_elapsed", 0) > 5]
        ended = [x for x in not_aborted if x.get("ended")]
        last_24h = [x for x in ended if x["started_at"] > (now - 24 * ONE_HOUR)]

        print "Attempted: {}".format(len(pomodoros_list))
        print "Not quickly aborted (5min): {}".format(len(not_aborted))
        print "Pomodoros: {}".format(len(ended))
        print "Last 24 hours: {}".format(len(last_24h))
        
        for p in sorted(last_24h, key=lambda x: x["started_at"]):
            print "  - {:%H:%M}: {}".format(datetime.fromtimestamp(p.get("started_at")),p.get("goal", "???"))

    def __call__(self):
        for datum in self._read():
            self._parse(datum)
        self.summarize()


        

if __name__ == '__main__':
    config = Config({
        "minutes": 25,
        "log_file": ".pomo_log",
        "minute_elapsed_sound": "resources/samples/chiming pottery02.wav",
        "timer_start_sound": "resources/samples/chiming pottery02.wav",
        "timer_end_sound": "resources/samples/applause.wav",
        "player": "paplay"})

    timer = Timer(config)

    if len(sys.argv) > 1 and sys.argv[1] == '-stats':
        # TODO divide in two executables, pomo and pomostats
        Analyser(config)()
    elif len(sys.argv) > 1:
        timer(string.join(sys.argv[1:], " "))
    else:
        timer()
