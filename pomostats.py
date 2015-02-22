import time
import os
import string
import json
from datetime import datetime
import subprocess
from abc import ABCMeta, abstractmethod
import sys
from common import epoch, Config

ONE_MINUTE = 60
ONE_HOUR = 60*ONE_MINUTE

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
    config = Config.from_env_variables({"log_file": "POMO_LOGFILE"})

    if len(sys.argv) > 1 and sys.argv[1] == '-stats':
        Analyser(config)()
