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

import sys

def run():
    import optparse
    parser = optparse.OptionParser()
    parser.add_option(
        '--debug', action='store_true', dest='debug', default=False)
    parser.add_option(
        '--host', action='store', dest='bind_host', default=None)
    parser.add_option(
        '--port', action='store', dest='bind_port', default=None)
    parser.add_option(
        '-f', '--conf-file', action='store', dest='conf_file')
    opts, args = parser.parse_args()

    if not opts.conf_file:
        print "You must specify a configuration file"
        return 1

    from ghmap import settings
    settings.load(opts.conf_file)

    bind_port = int(opts.bind_port or settings.get('server.port') or 5000)
    bind_host = opts.bind_host or settings.get('server.host')

    from ghmap.app import app
    import base64
    app.secret_key = base64.decodestring(settings.get('server.secret_key'))

    app.run(
        debug=opts.debug,
        host=bind_host,
        port=bind_port)

if __name__ == "__main__":
    sys.exit(run())
