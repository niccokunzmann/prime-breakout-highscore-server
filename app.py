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

# configuration
DEBUG = os.environ.get("APP_DEBUG", "true").lower() == "true"
PORT = int(os.environ.get("PORT", "5000"))
CACHE_REQUESTED_URLS_FOR_SECONDS = int(os.environ.get("CACHE_REQUESTED_URLS_FOR_SECONDS", 600))

# constants
HERE = os.path.dirname(__name__) or "."
TEMPLATE_FOLDER_NAME = "templates"
TEMPLATE_FOLDER = os.path.join(HERE, TEMPLATE_FOLDER_NAME)
STATIC_FOLDER_NAME = "static"
STATIC_FOLDER_PATH = os.path.join(HERE, STATIC_FOLDER_NAME)
with open(os.path.join(HERE, "example_highscore.json")) as f:
    EXAMPLE_HIGHSCORE = json.load(f)

# globals
app = Flask(__name__, template_folder=TEMPLATE_FOLDER)
# Check Configuring Flask-Cache section for more details
cache = Cache(app, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': tempfile.mktemp(prefix="cache-")})

def get_highscore():
    """Return the current high score."""
    return EXAMPLE_HIGHSCORE

def set_JS_headers(response):
    repsonse = make_response(response)
    response.headers['Access-Control-Allow-Origin'] = '*'
    # see https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS/Errors/CORSMissingAllowHeaderFromPreflight
    response.headers['Access-Control-Allow-Headers'] = request.headers.get("Access-Control-Request-Headers")
    response.headers['Content-Type'] = 'text/javascript'
    return response

def set_js_headers(func):
    """Set the response headers for a valid CORS request."""
    def with_js_response(*args, **kw):
        return set_JS_headers(func(*args, **kw))
    return with_js_response

@app.route("/")
def serve_index():
    return send_from_directory(STATIC_FOLDER_PATH, "index.html")

@app.route("/update_highscore.js")
@set_js_headers
def serve_configuration():
    return "/* generated */\nupdate_highsore({});".format(json.dumps(get_highscore()))

@app.errorhandler(500)
def unhandledException(error):
    """Called when an error occurs.

    See https://stackoverflow.com/q/14993318
    """
    file = io.StringIO()
    traceback.print_exception(type(error), error, error.__traceback__, file=file)
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
    """.format(traceback=file.getvalue()), 500 # return error code from https://stackoverflow.com/a/7824605

if __name__ == "__main__":
    app.run(debug=DEBUG, host="0.0.0.0", port=PORT)
