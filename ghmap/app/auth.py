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
Authentication views and stuff
"""

from ghmap import settings

CLIENT_ID = settings.get('github.client_id')
CLIENT_SECRET = settings.get('github.client_secret')

import json
from functools import wraps

from flask import url_for, session, request, redirect, make_response
from rauth.service import OAuth2Service

from .app import app


github = OAuth2Service(
    name='github',
    base_url='https://api.github.com/',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
)


def require_github(func):
    ## todo: catch authentication exceptions -> redirect to login page
    @wraps(func)
    def wrapped(*a, **kw):
        if session.has_key('token'):
            return func(*a, **kw)
        else:
            return redirect(url_for('login'))  # todo: add ?next=<current_url>
    return wrapped


@app.route('/login/')
def login():
    redirect_uri = url_for('authorized', next=request.args.get('next') or
        request.referrer or None, _external=True)
    # More scopes http://developer.github.com/v3/oauth/#scopes
    params = {'redirect_uri': redirect_uri, 'scope': 'user:email'}
    print(github.get_authorize_url(**params))
    return redirect(github.get_authorize_url(**params))


@app.route('/callback/')
def authorized():
    ## check to make sure the user authorized the request
    if not 'code' in request.args:
        #flash('You did not authorize the request')
        #return redirect(url_for('index'))
        return "You did not authorize the request", 403

    ## make a request for the access token credentials using code
    redirect_uri = url_for('authorized', _external=True)

    data = dict(
        code=request.args['code'],
        redirect_uri=redirect_uri,
        scope='user:email,public_repo',
    )

    auth = github.get_auth_session(data=data)

    session['token'] = auth.access_token

    return redirect(url_for('index'))


@app.route('/about/')
@require_github
def about():
    auth = github.get_session(token=session['token'])
    resp = auth.get('/user')
    if resp.status_code == 200:
        user = resp.json()

    #return render_template('about.html', user = user)
    resp = make_response(
        json.dumps(user), 200,
        {'Content-type': 'application/json'})
    return resp


@app.route('/about/token/')
@require_github
def get_token():
    return session.get('token')
