import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import flask, json, os
from flask import render_template, session
import geopy.distance
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

stadt = flask.Flask(__name__, static_folder="stadt/static", template_folder="stadt/templates")
stadt.secret_key="SECRET_KEY"
limiter = Limiter(
    app=stadt,
    key_func=get_remote_address,
    storage_uri="memory://",
)

with open("stadt/stadt_database.json", "r") as f:
    database = json.load(f)

def get_sort_key(object):
    try:
        return float(object["distance"])
    except:
        return 0

@stadt.route("/")
def home():
    return render_template("home.html")

@stadt.route("/documentation")
def docs():
    return render_template("docs.html")

@stadt.route("/datenschutz")
def pp():
    return render_template("privacy policy.html")

@stadt.route("/api/reset")
def reset_session():
    session["key"]=""
    return {
            "status" : "1",
            "message" : "Success"
        }

@stadt.route("/api/get_nearest_place/<latitude>/<longitude>")
@limiter.limit("1000/day")
def api(latitude: str, longitude: str):
    try:
        latitude=float(latitude)
        longitude=float(longitude)
    except:
        return {
            "status" : "0",
            "message" : "Die App hat fehlerhafte Koordinaten gesendet."
        }
    places = database["places"]
    new_places=[]
    for place in places:
        if place["information"] != "":
            place["index"] = places.index(place)
            place["distance"] = geopy.distance.geodesic((latitude, longitude), (place["latitude"], place["longitude"])).meters
            new_places.append(place)
    new_places.sort(key=get_sort_key)
    if new_places[0]["distance"] < new_places[0]["min_distance"]:
        number = new_places[0]["index"]
        value=session.get("key", None)
        if value == None:
            session["key"]=""
            value=session.get("key", None).split(";")
        else:
            value=value.split(";")
        if value[len(value)-1] == "":
            value.pop(len(value)-1)
        if not str(number) in value:
            list=""
            for a in value:
                if len(a) >= 1:
                    list=list+a+";"
            list=list+str(number)+";"
            session["key"]=list
            if new_places[0]["information"].startswith("file/"):
                return {
                    "status" : "3",
                    "message" : new_places[0]["information"][5:]+".mp3"
                }
            return {
                "status" : "1",
                "message" : new_places[0]["information"]
            }
        else:
            return {
                "status" : "2",
                "message" : "Warst schon hier."
            }
    return {
        "status" : "2",
        "message" : "Zu weit von markierten Stellen entfernt."
    }

@stadt.errorhandler(429)
def too_many_request_errorhandler(e):
    return {
        "status" : "0",
        "message" : "Sie haben ihr tägliches Kontingent von 500 Anfragen am Tag verbraucht."
    }