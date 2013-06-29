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

import os
import base64

from flask import Flask
app = Flask(__name__)


if 'GITMAP_CONF' in os.environ:
    from ConfigParser import RawConfigParser
    import json
    settings_file = os.environ['GITMAP_CONF']
    cfgp = RawConfigParser()
    cfgp.read(settings_file)
    for section in cfgp.sections():
        for option in cfgp.options(section):
            app.config['{}.{}'.format(section, option)] = \
                json.loads(cfgp.get(section, option))

app.secret_key = base64.decodestring(app.config['server.secret_key'])


## Import the views
from GitMaps import auth
from GitMaps import views
