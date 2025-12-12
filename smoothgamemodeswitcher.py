import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import flask, os
from flask import render_template


smoothgamemodeswitcher = flask.Flask(__name__, template_folder="smoothgamemodeswitcher/templates")

@smoothgamemodeswitcher.route("/")
def home():
    return render_template("home.html")