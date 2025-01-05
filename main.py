import flask
from flask import render_template
from flask_limiter.util import get_remote_address

app = flask.Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=80, debug=True)