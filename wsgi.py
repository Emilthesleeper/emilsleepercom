debug = True

for _ in range(4):
    if debug:
        print("\033[94m\033[1m!!!DEBUGGING IS ENABLED!!!")
    else:
        print("\033[92m\033[1m!!!DEBUGGING IS DISABLED!!!")

import com, lightflight, smoothgamemodeswitcher, stadt
import threading, os, signal, time

if __name__ == "__main__":
    stadt_thread = threading.Thread(target=stadt.stadt.run, kwargs={"host":"localhost", "port":5001, "debug":debug, "use_reloader": False})
    stadt_thread.start()
    com_thread = threading.Thread(target=com.com.run, kwargs={"host":"localhost", "port":5002, "debug":debug, "use_reloader": False})
    com_thread.start()
    lightflight_thread = threading.Thread(target=lightflight.lightflight.run, kwargs={"host":"localhost", "port":5003, "debug":debug, "use_reloader": False})
    lightflight_thread.start()
    smoothgamemodeswitcher_thread = threading.Thread(target=smoothgamemodeswitcher.smoothgamemodeswitcher.run, kwargs={"host":"localhost", "port":5004, "debug":debug, "use_reloader": False})
    smoothgamemodeswitcher_thread.start()
    try:
        time.sleep(3)
        for _ in range(4):
            if debug:
                print("\033[94m\033[1m!!!DEBUGGING IS ENABLED!!!")
            else:
                print("\033[92m\033[1m!!!DEBUGGING IS DISABLED!!!")
        while stadt_thread.is_alive() and com_thread.is_alive() and lightflight_thread.is_alive() and smoothgamemodeswitcher_thread.is_alive():
            pass
    except KeyboardInterrupt:
        os.kill(os.getpid(), signal.SIGINT)