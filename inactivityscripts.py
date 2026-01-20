import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import flask, os, requests, time, json
from flask import render_template

inactivityscripts = flask.Flask(__name__, template_folder="inactivityscripts/templates")

@inactivityscripts.route("/")
def home():
    compatibility = get_modrinth_compatibility("inactivity-scripts")
    try:
        import wsgi as wsgi_mod
        footer = getattr(wsgi_mod, "FOOTER", "")
    except Exception:
        footer = ""
    return render_template("home.html", compatibility=compatibility, footer=footer)

def get_modrinth_compatibility(slug: str):
    cache_path = os.path.join(os.path.dirname(__file__), "inactivityscripts_cache.json")
    # Return cached value if less than 1 hour old
    try:
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            ts = float(cached.get("timestamp", 0))
            if time.time() - ts < 3600:
                return cached.get("compatibility", {})
    except Exception:
        pass

    try:
        url = f"https://api.modrinth.com/v2/project/{slug}/version"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        versions = resp.json()
        loader_map = {}
        for v in versions:
            loaders = v.get("loaders") or v.get("loader") or []
            gvers = v.get("game_versions", [])
            for loader in loaders:
                if loader not in loader_map:
                    loader_map[loader] = set()
                for gv in gvers:
                    loader_map[loader].add(gv)
        # Convert sets to sorted lists
        result = {k: sorted(list(v)) for k, v in loader_map.items()}
        # Persist cache (best-effort)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump({"timestamp": time.time(), "compatibility": result}, f)
        except Exception:
            pass
        return result
    except Exception:
        return {}