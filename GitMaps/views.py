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

from flask import render_template, session
from flask.ext import restful
import requests

from werkzeug.contrib.cache import SimpleCache

from . import app
from .auth import github, require_github


cache = SimpleCache()


@app.context_processor
def add_user_info():
    user = cache.get('user_profile')
    if user is None:
        auth = github.get_session(token=session['token'])
        resp = auth.get('user')
        if resp.ok:
            user = resp.json()
            user['authenticated'] = True
        else:
            user = {'authenticated': False}
        cache.set('user_profile', user, timeout=120)
    return dict(user=user)


@app.route("/")
def index():
    return render_template("index.html")


def dig_down_request(do_req, url):
    while True:
        resp = do_req(url)
        yield resp

        if 'next' in resp.links:
            url = resp.links['next']['url']
        else:
            return  # Nothing to see here..


def dig_down_merge(do_req, url):
    results = []
    for resp in dig_down_request(do_req, url):
        if not resp.ok:
            raise Exception("Request failure (code: {})".format(resp.status_code))
        results.extend(resp.json())
    return results


@app.route('/map-editor/')
@app.route('/map-editor/<owner>/')
@app.route('/map-editor/<owner>/<repo>/')
@app.route('/map-editor/<owner>/<repo>/<branch>/')
@app.route('/map-editor/<owner>/<repo>/<branch>/<path:path>')
@require_github
def map_editor(owner=None, repo=None, branch=None, path=None):

    if repo is None:
        return map_editor_list_repos(owner)

    elif branch is None:
        return map_editor_list_branches(owner, repo)

    else:
        if path is None:
            path = ""  # Root

        if path.endswith('.geojson'):
            ## todo: check that this is a directory too..?
            return map_editor_editor(owner, repo, branch, path)

        else:
            return map_editor_list_files(owner, repo, branch, path)


def map_editor_list_repos(owner=None):
    """
    List repositories for a given user/organization
    """

    ## todo: fetch repos for organizations too..

    if owner is None:
        title = "Your repositories"
        url = '/user/repos?sort=updated&direction=desc'

    else:
        title = "Repositories for {}".format(owner)
        url = '/users/{}/repos?sort=updated&direction=desc'.format(owner)

    auth = github.get_session(token=session['token'])
    repos = dig_down_merge(auth.get, url)
    return render_template("map-editor/repos-index.html", repos=repos, title=title)


def map_editor_list_branches(owner, repo):
    """
    List branches in a repository
    """

    ## List branches in this repo
    auth = github.get_session(token=session['token'])
    resp = auth.get('/repos/{}/{}'.format(owner, repo))

    if not resp.ok:
        raise Exception("Error getting repository: {}".format(resp.status_code))

    repo_obj = resp.json()

    branches = dig_down_merge(
        auth.get, '/repos/{}/{}/branches'.format(owner, repo))

    return render_template(
        "map-editor/repos-branches.html",
        branches=branches,
        title=repo_obj['full_name'],
        repo=repo_obj)


def map_editor_list_files(owner, repo, branch, path=None):
    """
    List files in a repository
    """

    if path is None:
        path = ''

    auth = github.get_session(token=session['token'])
    contents = dig_down_merge(
        auth.get,
        '/repos/{}/{}/contents/{}?ref={}'.format(owner, repo, path, branch))

    if not isinstance(contents, list):
        ## This is not a directory!
        ## todo: if it's a geojson file, return the other view?
        raise Exception("This is not a directory!")

    return render_template(
        'map-editor/repos-files.html',
        owner=owner, repo=repo, branch=branch, contents=contents)


def map_editor_editor(owner=None, repo=None, branch=None, path=None):
    """
    This is the actual map editor view
    """

    from flask import request

    geojson_url = "/api/geojson/{owner}/{repo}/{branch}/{path}"\
                  "".format(owner=owner, repo=repo, branch=branch, path=path)

    ## todo: if this is a directory, return map_editor_list_files() instead!

    return render_template(
        'map-editor/map-view.html',
        geojson_url=geojson_url,
        mode=request.args.get('mode') or 'view')


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
    def getAuth(self):
        return github.get_session(token=session['token'])

    def get(self, owner, repo, branch, path):
        resp = self.getAuth().get('/repos/{}/{}/contents/{}?ref={}'.format(owner, repo, path, branch))

        if not resp.ok:
            raise Exception("Error getting file")

        file_data = resp.json()

        assert file_data['type'] == 'file'

        geojson = json.loads(base64.decodestring(file_data['content']))

        ## todo: we can get this from the API...
        return geojson

    def put(self, owner, repo, branch, path):
        # http://developer.github.com/v3/repos/contents/#create-a-file
        import base64
        from flask import request

        auth = self.getAuth()

        url = '/repos/{}/{}/contents/{}?ref={}'.format(owner, repo, path, branch)

        message = request.args.get('message') or \
            "Updated {} via GitMaps".format(path)

        previous_sha = None
        resp = auth.get(url)
        if resp.ok:
            prev_file = resp.json()
            previous_sha = prev_file['sha']

        payload = {
            'message': message,
            'content': base64.b64encode(request.get_data()),
            #'path': path,  ## This is optional....
            'branch': branch,
            #'sha': None,  # ----- todo: it looks like this is needed!!
        }

        ## This is needed for update...
        if previous_sha is not None:
            payload['sha'] = previous_sha

        ## todo: if nothing changed, do not commit!

        resp = auth.put(
            url,
            data=json.dumps(payload),
            headers={'content-type': 'application/json'})

        if not resp.ok:
            raise Exception("Request failed! {} - {}".format(resp.status_code, resp.text))

        pass

api.add_resource(GeoJsonFile, '/api/geojson/<owner>/<repo>/<branch>/<path:path>')

# https://raw.github.com/rshk/geojson-experiments/master/example.geojson
