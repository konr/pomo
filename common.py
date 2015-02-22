import time
import os

def epoch():
    return int(time.time())

class Configurable:
    def __init__(self, config):
        self._config = config

class Config(Configurable):

    def get(self, attr):
        return self._config[attr]
        
    @classmethod
    def from_env_variables(_, env_dict):
        return Config(
            {k: os.environ.get(v)
             for k,v in env_dict.iteritems()
             if os.environ.get(v, None)})
