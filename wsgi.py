debug = True
host="127.0.0.1"

import datetime
START_YEAR = 2024
CURRENT_YEAR = datetime.date.today().year
if CURRENT_YEAR > START_YEAR:
    COPYRIGHT_YEAR = f"{START_YEAR}-{CURRENT_YEAR}"
else:
    COPYRIGHT_YEAR = str(START_YEAR)
FOOTER = f"© {COPYRIGHT_YEAR} Emil Wege. All Rights Reserved."

for _ in range(4):
    if debug:
        print("\033[94m\033[1m!!!DEBUGGING IS ENABLED!!!")
    else:
        print("\033[92m\033[1m!!!DEBUGGING IS DISABLED!!!")

import com, lightflight, smoothgamemodeswitcher, stadt, zahlenraten, inactivityscripts, bbs_movie_studio
import threading, os, signal, time

if __name__ == "__main__":
    stadt_thread = threading.Thread(target=stadt.stadt.run, kwargs={"host":host, "port":5001, "debug":debug, "use_reloader": False})
    stadt_thread.start()
    com_thread = threading.Thread(target=com.com.run, kwargs={"host":host, "port":5002, "debug":debug, "use_reloader": False})
    com_thread.start()
    lightflight_thread = threading.Thread(target=lightflight.lightflight.run, kwargs={"host":host, "port":5003, "debug":debug, "use_reloader": False})
    lightflight_thread.start()
    smoothgamemodeswitcher_thread = threading.Thread(target=smoothgamemodeswitcher.smoothgamemodeswitcher.run, kwargs={"host":host, "port":5004, "debug":debug, "use_reloader": False})
    smoothgamemodeswitcher_thread.start()
    zahlenraten_thread = threading.Thread(target=zahlenraten.zahlenraten.run, kwargs={"host":host, "port":5005, "debug":debug, "use_reloader": False})
    zahlenraten_thread.start()
    inactivityscripts_thread = threading.Thread(target=inactivityscripts.inactivityscripts.run, kwargs={"host":host, "port":5006, "debug":debug, "use_reloader": False})
    inactivityscripts_thread.start()
    bbs_thread = threading.Thread(target=bbs_movie_studio.bbs.run, kwargs={"host":host, "port":5007, "debug":debug, "use_reloader": False})
    bbs_thread.start()
    try:
        time.sleep(3)
        for _ in range(4):
            if debug:
                print("\033[94m\033[1m!!!DEBUGGING IS ENABLED!!!")
            else:
                print("\033[92m\033[1m!!!DEBUGGING IS DISABLED!!!")
        while stadt_thread.is_alive() and com_thread.is_alive() and lightflight_thread.is_alive() and smoothgamemodeswitcher_thread.is_alive() and zahlenraten_thread.is_alive() and inactivityscripts_thread.is_alive() and bbs_thread.is_alive():
            pass
    except KeyboardInterrupt:
        os.kill(os.getpid(), signal.SIGINT)