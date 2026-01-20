import sys, os, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import flask
from flask import render_template, url_for

com = flask.Flask(__name__, template_folder="com/templates")

com.config['JSON_AS_ASCII'] = False

with open("contents.json", "r", encoding="utf-8") as f:
    contents = json.load(f)

for project in contents["projects"]:
    for lang in ["de", "en"]:
        if project["description"].get(lang):
            project["description"][lang] = project["description"][lang][:100] + ("..." if len(project["description"][lang]) > 100 else "")

@com.route("/")
def home():
    if com.debug:
        with open("contents.json", "r", encoding="utf-8") as f:
            contents = json.load(f)
        for project in contents["projects"]:
            for lang in ["de", "en"]:
                if project["description"].get(lang):
                    project["description"][lang] = project["description"][lang][:100] + ("..." if len(project["description"][lang]) > 100 else "")
    try:
        import wsgi as wsgi_mod
        footer = getattr(wsgi_mod, "FOOTER", "")
    except Exception:
        footer = ""
    return render_template("home.html", projects=contents["projects"], debug=com.debug, footer=footer)

@com.route("/mcdownload_secret_asjdß09283zernaszdhouih23")
def mcdownload_secret():
    servers=[]
    files = [f for f in os.listdir(os.path.join(ROOT, "emilsleepercom", "static")) if f.startswith("server") and f.endswith(".zip")]
    for f in files:
        name="UNKNOWN"
        date="UNKNOWN"
        if "server1-aisodf7nb903w48rfsndilfuhq927403rztbsdafuh" in f:
            name="survival"
            date="~10.11.2024 - 14.05.2025"
        elif "server2-asdjahgsdklhgaspd3ß97zdasudasd798z7ashdaiu" in f:
            name="survival2"
            date="28.09.2024 - 10.11.2024"
        elif "server3-asd9uz0379zdoiasud09f738f7zaodift08927tfai" in f:
            name="survival2025"
            date="~14.05.2025 - 13.09.2025"
        elif "server4-asud08732tgdaiszdg237dzt20837daioszft02937" in f:
            name="survival20252_old"
            date="~14.09.2025 - 29.09.2025"
        elif "server5-a9sdz09273daisfuz29378rzasiouz9207zriauz09" in f:
            name="survival20252"
            date="~29.09.2025 - 05.12.2025"
        url=url_for("static", filename=f)
        servers.append({
            "id": f.split("-")[0][6:],
            "file": url,
            "size": "{:.2f} GB".format(os.path.getsize(os.path.join(ROOT, "emilsleepercom", "static", f)) / (1024 * 1024 * 1024)),
            "date": date,
            "name": name
        })
    try:
        import wsgi as wsgi_mod
        footer = getattr(wsgi_mod, "FOOTER", "")
    except Exception:
        footer = ""
    return render_template("mcdownload_secret.html", servers=servers, footer=footer)