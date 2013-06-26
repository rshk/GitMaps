##==============================================================================
## Copyright 2013 Samuele Santi
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##==============================================================================

conf = {
    'server.host': '127.0.0.1',
    'server.port': 5000,
}

def load(settings_file):
    from ConfigParser import RawConfigParser
    import json
    cfgp = RawConfigParser()
    cfgp.read(settings_file)
    for section in cfgp.sections():
        for option in cfgp.options(section):
            conf['{}.{}'.format(section, option)] = \
                json.loads(cfgp.get(section, option))


DEFAULT = object()


def get(key, default=DEFAULT):
    if default is DEFAULT:
        return conf[key]
    return conf.get(key, default)
