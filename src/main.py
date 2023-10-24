import time, os, sys, schedule
from datetime import datetime
from config import config
import tools, tuya, database

# Get any email or password form environment variables
if config["tuya"]["email"] == "" and not os.environ.get("EMAIL") == "":
    config["tuya"]["email"] = os.environ.get("EMAIL")
if config["tuya"]["password"] == "" and not os.environ.get("PASSWORD") == "":
    config["tuya"]["password"] = os.environ.get("PASSWORD")

# Connect to DB if configured
db = database.Database(config["database_type"], config)
db = db.connect()

# connect to tuya and get the access tokens
tuya = tuya.tuya(config["tuya"]["email"], config["tuya"]["password"], config["tuya"]["country"], db)

# retrieve a device list
tuya.getDeviceList()

# schedule a call for a access token refresh
schedule.every(tuya.token_expires_in-60).seconds.do(tuya.refresh_access_token)

# check if there is anything to do at this time
def check_for_triggers():
    print("Checking for Triggers", flush=True)
    current_time = datetime.now()
    hour = str(current_time.hour)
    minutes = str(current_time.minute)

    for trigger in config["triggers"]:
        if trigger["trigger"] == "time":
            trigger_time = trigger["time"].split(":")
            if hour == trigger_time[0] and minutes == trigger_time[1]:
                tuya.deviceStateByName(trigger["device_name"], 1 if trigger["state"].lower() == "on" else 0)

    return True

try:
    while True:
        # check for any scheduled tasks to run
        schedule.run_pending()

        current_time = datetime.now()
        minutes = current_time.minute

        #if minutes == 0 or minutes == 30:
        check_for_triggers()

        # Calculate the time until the next half-hour
        remaining_seconds = 1800 - (current_time.second + 60 * minutes)

        # flush the print to screen
        sys.stdout.flush()
        # Wait until the next half-hour
        time.sleep(60-current_time.second)
except KeyboardInterrupt:
    db.close()
