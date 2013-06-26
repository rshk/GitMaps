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

"""
Views
"""

import json

from flask import render_template
from flask.ext import restful
import requests

from .app import app

@app.route("/")
def index():
    return render_template("index.html")



## === API URLs ================================================================

api = restful.Api(app)

class Layer(restful.Resource):
    def get(self, owner, repo, branch, path):
        if not owner:
            return "Invalid owner", 400

        if not repo:
            return "Invalid repo", 400

        if not path.endswith('.geojson'):
            return "You must pass a valid geojson file", 400

        url = "https://raw.github.com/{}/{}/{}/{}"\
            .format(owner, repo, branch, path)
        response = requests.get(url)

        ## todo: validate GeoJSON..
        return json.loads(response.text)

api.add_resource(Layer, '/api/layer/<owner>/<repo>/<branch>/<path:path>')

# https://raw.github.com/rshk/geojson-experiments/master/example.geojson
