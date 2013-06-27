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

import json, base64

from flask import render_template, session, url_for
from flask.ext import restful
import requests

from .app import app
from .auth import github, require_github


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/map-editor/')
@app.route('/map-editor/<owner>/')
@app.route('/map-editor/<owner>/<repo>/')
@app.route('/map-editor/<owner>/<repo>/<branch>/')
@app.route('/map-editor/<owner>/<repo>/<branch>/<path:path>')
@require_github
def map_editor(owner=None, repo=None, branch=None, path=None):
    auth = github.get_session(token=session['token'])
    if repo is None:

        ## todo: fetch repos for organizations too..
        if owner is None:
            title = "Your repositories"
            resp = auth.get('/user/repos?sort=updated&direction=desc')
        else:
            title = "Repositories for {}".format(owner)
            resp = auth.get('/users/{}/repos?sort=updated&direction=desc'.format(owner))
        if resp.status_code != 200:
            raise Exception("Request failure (code: {})".format(resp.status_code))
        repos = resp.json()

        return render_template("map-editor/repos-index.html", repos=repos, title=title)

    elif branch is None:
        ## List branches in this repo
        resp = auth.get('/repos/{}/{}'.format(owner, repo))
        if resp.status_code == 200:
            repo_obj = resp.json()
        else:
            raise Exception("Error getting repository: {}".format(resp.status_code))

        resp = auth.get('/repos/{}/{}/branches'.format(owner, repo))
        if resp.status_code == 200:
            branches = resp.json()
        else:
            raise Exception("Error getting repository: {}".format(resp.status_code))

        return render_template(
            "map-editor/repos-branches.html",
            branches=branches,
            title=repo_obj['full_name'],
            repo=repo_obj)

    else:
        ## List files in this branch unless we're on a .geojson file
        ## In that case, show the map, using tiles from:
        ## http://a.tiles.mapbox.com/v3/redshadow.map-9pbekffc/9.058900000000008,45.8006,14/500x300.png

        # GET /repos/:owner/:repo/git/trees/:sha
        # GET /repos/:owner/:repo/contents/:path

        if path is None:
            path = ""  # Root

        if path.endswith('.geojson'):
            # resp = auth.get('/repos/{}/{}/contents/{}?ref={}'.format(owner, repo, path, branch))
            # if not 200 <= resp.status_code < 300:
            #     raise Exception("Error getting file")

            # file_data = resp.json()

            # assert file_data['type'] == 'file'

            # geojson = json.loads(base64.decodestring(file_data['content']))

            ## todo: we can get this from the API...

            #geojson_url = url_for('GeoJsonFile', owner=owner, repo=repo, branch=branch, path=path)
            geojson_url = "/api/geojson/{owner}/{repo}/{branch}/{path}".format(owner=owner, repo=repo, branch=branch, path=path)

            from flask import request

            return render_template(
                'map-editor/map-view.html',
                geojson_url=geojson_url,
                mode=request.args.get('mode') or 'view')
            #return json.dumps(geojson)

        else:
            ## todo: return a list of files in this directory so far..
            #https://api.github.com/repos/rshk/geojson-experiments/contents/?access_token=0ec2d31671893e2306013768506e684a01f7e923

            auth = github.get_session(token=session['token'])
            resp = auth.get('/repos/{}/{}/contents/{}?ref={}'.format(owner, repo, path, branch))

            if not resp.ok:
                raise Exception("Error getting directory list")

            contents = resp.json()

            if not isinstance(contents, list):
                ## this is not a directory! -> raise something?
                raise Exception("This is not a directory!")

            return render_template('map-editor/repos-files.html', owner=owner, repo=repo, branch=branch, contents=contents)






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


class GeoJsonFile(restful.Resource):
    def get(self, owner, repo, branch, path):
        auth = github.get_session(token=session['token'])
        resp = auth.get('/repos/{}/{}/contents/{}?ref={}'.format(owner, repo, path, branch))

        if not resp.ok:
            raise Exception("Error getting file")

        file_data = resp.json()

        assert file_data['type'] == 'file'

        geojson = json.loads(base64.decodestring(file_data['content']))

        ## todo: we can get this from the API...
        return geojson

api.add_resource(GeoJsonFile, '/api/geojson/<owner>/<repo>/<branch>/<path:path>')

# https://raw.github.com/rshk/geojson-experiments/master/example.geojson
