import sys, os
import wsgi as wsgi_mod
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import flask, os, requests, time, json, re
from flask import render_template

lightflight = flask.Flask(__name__, template_folder="lightflight/templates")

def get_curseforge_compatibility(slug: str):
    global curseforge_api_token
    cache_path = os.path.join(os.path.dirname(__file__), "lightflight_cache.json")
    try:
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            ts = float(cached.get("timestamp", 0))
            if time.time() - ts < 3600:
                return cached.get("compatibility", {})
    except Exception:
        pass

    search_url = f"https://api.cfwidget.com/minecraft/mc-mods/light-flight"
    try:
        r = requests.get(search_url, timeout=10)
        result = r.json()
        loader_map = {}
        for f in result.get("files", []):
            vers = f.get("versions", [])
            if "Fabric" in vers:
                for v in vers:
                    if v and v[0].isdigit():
                        loader_map.setdefault("Fabric", set()).add(v)
        result = {k: sorted(list(s)) for k, s in loader_map.items()}
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump({"timestamp": time.time(), "compatibility": result}, f)
        except Exception:
            pass

        return result
    except Exception:
        return None

try:
    compatibility = get_curseforge_compatibility("light-flight")
    if compatibility is None:
        compatibility = {}
except Exception:
    compatibility = {}

@lightflight.route("/")
def home():
    global compatibility
    if getattr(wsgi_mod, "debug", ""):
        result = get_curseforge_compatibility("light-flight")
        if result is not None:
            compatibility = result
    try:
        footer = getattr(wsgi_mod, "FOOTER", "")
    except Exception:
        footer = ""
    return render_template("home.html", compatibility=compatibility, footer=footer)