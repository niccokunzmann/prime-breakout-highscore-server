#!/usr/bin/python3
from flask import Flask, render_template, make_response, request, jsonify, \
    redirect, send_from_directory
from flask_caching import Cache
import json
import os
import tempfile
import requests
from pprint import pprint
import traceback
import io
import sys
import time
from urllib.parse import urlencode

# configuration
DEBUG = os.environ.get("APP_DEBUG", "true").lower() == "true"
HOST = os.environ.get("HOST", "prime-breakout-highscore-server")
PORT = int(os.environ.get("PORT", "5000"))
DEFAULT_HIGH_SCORE_SOURCE_URL = "https://gitlab.com/niccokunzmann/prime-breakout-highscore-server/-/raw/score/highscore.json";
HIGH_SCORE_SOURCE_URL = os.environ.get("HIGH_SCORE_SOURCE_URL", DEFAULT_HIGH_SCORE_SOURCE_URL)
CACHE_REQUESTED_URLS_FOR_SECONDS = int(os.environ.get("CACHE_REQUESTED_URLS_FOR_SECONDS", 600))
GITLAB_API_TOKEN = os.environ.get("GITLAB_API_TOKEN", "")
GITLAB_PROJECT = os.environ.get("GITLAB_PROJECT", "niccokunzmann/prime-breakout-highscore-server")
GITLAB_PROJECT_BRANCH = os.environ.get("GITLAB_PROJECT_BRANCH", "score")
GITLAB_PROJECT_COMMIT_MESSAGE = os.environ.get("GITLAB_PROJECT_COMMIT_MESSAGE", "update highscore")
GITLAB_PROJECT_AUTHOR_EMAIL = os.environ.get("GITLAB_PROJECT_AUTHOR_EMAIL", os.environ.get("USER", "flask") + "@" + HOST)
GITLAB_PROJECT_AUTHOR_NAME = os.environ.get("GITLAB_PROJECT_AUTHOR_NAME", os.environ.get("USER", "flask"))
GITLAB_HOST = os.environ.get("GITLAB_HOST", "https://gitlab.com")
GITLAB_PROJECT_FILE_PATH = os.environ.get("GITLAB_PROJECT_FILE_PATH", "/highscore.json")
# constants
HERE = os.path.dirname(__name__) or "."
TEMPLATE_FOLDER_NAME = "templates"
TEMPLATE_FOLDER = os.path.join(HERE, TEMPLATE_FOLDER_NAME)
STATIC_FOLDER_NAME = "static"
STATIC_FOLDER_PATH = os.path.join(HERE, STATIC_FOLDER_NAME)

# globals
app = Flask(__name__, template_folder=TEMPLATE_FOLDER)

# Check Configuring Flask-Cache section for more details
cache = Cache(app, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': tempfile.mktemp(prefix="cache-")})

# caching

__URL_CACHE = {}
def cache_url(url, text):
    """Cache the value of a url."""
    __URL_CACHE[url] = text
    try:
        get_text_from_url(url)
    finally:
        del __URL_CACHE[url]

@cache.memoize(
    CACHE_REQUESTED_URLS_FOR_SECONDS,
    forced_update=lambda: bool(__URL_CACHE))
def get_text_from_url(url):
    """Return the text from a url.

    The result is cached CACHE_REQUESTED_URLS_FOR_SECONDS.
    """
    if __URL_CACHE:
        return __URL_CACHE[url]
    return requests.get(url).text


__score = None
__score_time = 0
def get_highscore():
    """Return the current high score."""
    global __score, __score_time
    if (__score_time < time.time() - CACHE_REQUESTED_URLS_FOR_SECONDS):
        __score = json.loads(get_text_from_url(DEFAULT_HIGH_SCORE_SOURCE_URL))
        __score_time = time.time()
    return __score

def set_highscore(new_score):
    """Set the high score."""
    global __score
    __score = new_score
    __score["version"] += 1
    if GITLAB_API_TOKEN:
        update_score_on_gitlab(new_score)
    return __score

def get_update_highscore_js(score):
    """Return the contents of the .js file."""
    return "/* generated */\nupdate_highscore({});".format(json.dumps(score, indent=2))


def update_score_on_gitlab(new_score):
    """Set the current score on gitlab.

    see https://docs.gitlab.com/ee/api/repository_files.html#update-existing-file-in-repository
    """
    # /projects/:id/repository/files/:file_path
    url = GITLAB_HOST + "/api/v4/projects/" + urlencode(GITLAB_PROJECT) + "repository/files/" + urlenode(GITLAB_PROJECT_FILE_PATH)
    content = {
        "branch": GITLAB_PROJECT_BRANCH,
        "content": json.dumps(new_score, indent=2),
        "author_email": GITLAB_PROJECT_AUTHOR_EMAIL,
        "author_name": GITLAB_PROJECT_AUTHOR_NAME,
        "commit_message": GITLAB_PROJECT_COMMIT_MESSAGE
    }
    requests.put(url, json=content, headers={"PRIVATE-TOKEN": GITLAB_API_TOKENc})

def add_scores(scores):
    """Add a list of scores."""
    current = get_highscore()
    for i, score in enumerate(scores):
        assert "name" in score and isinstance(score["name"], str), "score {} must have a name as string".format(i)
        assert "id" in score and isinstance(score["id"], int), "score {} must have an id as int".format(i)
        assert "points" in score and isinstance(score["points"], int), "score {} must have points as int".format(i)
        new_score = {
            "name" : score["name"],
            "id" : score["id"],
            "points" : score["points"]
        }
        if new_score not in current["scores"]:
            current["scores"].append(score)
    set_highscore(current)
    return scores


@app.route("/")
def serve_index():
    return send_from_directory(STATIC_FOLDER_PATH, "index.html")

@app.route("/update_highscore.js")
def serve_score():
    try:
        print(request.args)
        if "scores" in request.args:
            result = add_scores(json.loads(request.args["scores"]))
        else:
            result = get_highscore()
    except Exception as error:
        result = {
            "api_version" : 1,
            "error" : {
                "type" : type(error).__name__,
                "message" : str(error),
                "traceback" : get_traceback_string(error)
            }
        }
    result["source"] = request.host + request.path
    result = get_update_highscore_js(result)
    response = make_response(result)
    response.headers['Access-Control-Allow-Origin'] = '*'
    # see https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS/Errors/CORSMissingAllowHeaderFromPreflight
    response.headers['Access-Control-Allow-Headers'] = request.headers.get("Access-Control-Request-Headers")
    response.headers['Content-Type'] = 'text/javascript'
    return response


def get_traceback_string(error):
    """Return the tracecback string from an error."""
    file = io.StringIO()
    traceback.print_exception(type(error), error, error.__traceback__, file=file)
    return file.getvalue()

@app.errorhandler(500)
def unhandledException(error):
    """Called when an error occurs.

    See https://stackoverflow.com/q/14993318
    """
    return """
    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
    <html>
        <head>
            <title>500 Internal Server Error</title>
        </head>
        <body>
            <h1>Internal Server Error</h1>
            <p>The server encountered an internal error and was unable to complete your request.  Either the server is overloaded or there is an error in the application.</p>
            <pre>\r\n{traceback}
            </pre>
        </body>
    </html>
    """.format(traceback=get_tracebak_string(error)), 500 # return error code from https://stackoverflow.com/a/7824605

if __name__ == "__main__":
    app.run(debug=DEBUG, host="0.0.0.0", port=PORT)
