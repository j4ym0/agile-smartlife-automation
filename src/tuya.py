import requests, json, time, random
from datetime import datetime, timedelta
from config import config
import tools
# Tuya country codes US - 1, eu - 44, cn - 86

class tuya():
    def __init__(self, email, password, country_code, database=None):
        print("init tuya interface")

        self.tuya_country_code = country_code
        self.tuya_base_url = f"https://px1.tuya{self.tuya_country_code}.com/homeassistant/"
        # Your Tuya account email and password
        self.email = email
        self.password = password

        self.access_token = None
        self.refresh_token = None
        self.token_expires_in = 864000
        # used to save the device list and access tokens for later
        self.db = database

        # cache the device list
        self.device_list = {}

        self.login()

    def login(self):

        # check if the db has been set
        if not self.db is None:
            #check for an existing access token
            print(f"Checking DB for Auth Token")
            self.access_token, self.refresh_token, self.token_expires_in = self.db.access_token_get(self.email, self.password)
            # convert expiry datetime into seconds 
            current_time = datetime.now()
            self.token_expires_in = (self.token_expires_in - current_time).total_seconds()

        # if a token has been set return
        if not self.access_token is None:
            print(f"Got Auth Token from DB")
            return True
        
        # Tuya API URL for authentication
        auth_url = f"{self.tuya_base_url}auth.do"

        # Start building the headers
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        # Get the form data ready
        form_data = {
            "userName": self.email,
            "password": self.password,
            "countryCode": 86 if self.tuya_country_code == 'cn' else 44 if self.tuya_country_code == 'eu' else 1,
            "bizType": "smart_life",
            "from": "tuya",
        }

        # Authenticate and get the access token
        response = requests.post(auth_url, data=form_data, headers=headers)

        if response.status_code == 200:
            auth_data = response.json()
            if not auth_data.get('responseStatus') == 'error':
                self.access_token = auth_data.get("access_token")
                self.refresh_token = auth_data.get("refresh_token")
                self.token_expires_in = auth_data.get("expires_in")
            else:
                print(f"Got message '{auth_data.get('errorMsg')}'")
                print(f"Sleeping for 60 seconds", flush=True)
                time.sleep(60)
                return self.login()
        else:
            print(f"Authentication failed. Status code: {response.text}")
        
        # Save access token if db has been set
        if not self.db is None:
            print(f"Auth Token saved")
            self.db.access_token_save(self.email, self.access_token, self.refresh_token, self.token_expires_in)

        print(f"Auth Token: {self.access_token}")

    def refresh_access_token(self):
        print(f"Refreshing access token")

        # if a token has been set return
        if self.access_token is None:
            print(f"No Access token to exchange")
            return
        
        # Tuya API URL for authentication
        auth_url = f"{self.tuya_base_url}access.do"

        # Get the form data ready
        form_data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "rand": random.random(),
        }

        # Authenticate and get the access token
        response = requests.get(auth_url, params=form_data)

        if response.status_code == 200:
            auth_data = response.json()
            if not auth_data.get('responseStatus') == 'error':
                self.access_token = auth_data.get("access_token")
                self.refresh_token = auth_data.get("refresh_token")
                self.token_expires_in = auth_data.get("expires_in")
            else:
                print(f"Got message '{auth_data.get('errorMsg')}'")
                print(f"Sleeping for 60 seconds", flush=True)
                time.sleep(60)
                return self.login()
        else:
            print(f"Authentication failed. Status code: {response.text}")
        
        # Save access token if db has been set
        if not self.db is None:
            print(f"Auth Token saved")
            self.db.access_token_save(self.email, self.access_token, self.refresh_token, self.token_expires_in)

        print(f"New Token: {self.access_token}")

    def getDeviceList(self,refresh_access_token=False):
        # Check if a access token needs refresh
        if refresh_access_token == True:
            self.refresh_access_token()

        # Check if we have a Auth Token and get one if not
        if self.access_token is None:
            self.login()

        # Load device list from database
        if not self.db is None:
            db_devices = self.db.device_get_list(self.access_token)
            for row in db_devices:
                print(f"Getting Device from DB {row[0]}")
                self.device_list.update({row[0]: {'id':row[0], 'name': row[1], 'dev_type': row[2], 'ha_type': row[3], 'data': json.loads(row[4])}})

        # Start building the headers
        headers = {
            "Content-Type": "application/json",
        }
        # Build the json data to send
        data = {
            "header": {
                "name": "Discovery",
                "namespace": "discovery",
                "payloadVersion": 1,
            },
            "payload": {
                "accessToken": self.access_token,
            },
        }
        
        # Tuya API URL for querying device list
        device_list_url = f"{self.tuya_base_url}skill"
        # Send post of json data
        response = requests.post(device_list_url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            if response.json().get('header').get('code') == 'FrequentlyInvoke':
                print(f"Got message '{response.json().get('header').get('msg')}'")
                if not self.db is None:
                    print(f"Using device list from database", flush=True)
                    return
                print(f"Sleeping for 120 seconds", flush=True)
                time.sleep(120)
                return self.getDeviceList(refresh_access_token)
            else:
                device_list = response.json().get('payload')
                if not device_list is None:
                    if not device_list.get('devices') is None:
                        print("Device List:")
                        for device in device_list.get('devices'):
                            # cache device in a list
                            try:
                                del self.device_list[device.get('id')]
                            except KeyError:
                                pass
                            self.device_list.update({device.get('id'): {'id':device.get('id'), 'name': device.get('name'), 'dev_type': device.get('dev_type'), 'ha_type': device.get('ha_type'), 'data': device.get('data')}})

                            # Checking for db before saving device
                            if not self.db is None:
                                print(f"Adding/Updating Device {device.get('id')}")
                                self.db.device_save(self.access_token, device.get('id'), device.get('name'), device.get('dev_type'), device.get('ha_type'), json.dumps(device.get('data')),)
                            print(f"Device ID: {device.get('id')}, Name: {device.get('name')}")
        else:
            print(f"Failed to get the device list. Response: {response.text}")

    def deviceAdjust(self, dev_id, action, value, state):
        # Check if we have a Auth Token and get one if not
        if self.access_token is None:
            self.login()

        # Start building the headers
        headers = {
            "Content-Type": "application/json",
        }
        # Build the json data to send
        data = {
            "header": {
                "name": action,
                "namespace": "control",
                "payloadVersion": 1,
            },
            "payload": {
                "accessToken": self.access_token,
                "devId": dev_id,
                value: state,
            },
        }
        
        # Tuya API URL for querying device list
        device_list_url = f"{self.tuya_base_url}skill"
        # Send post of json data
        response = requests.post(device_list_url, headers=headers, data=json.dumps(data))
        if response.status_code == 200:
            if response.json().get('header').get('code') == 'SUCCESS':
                return True
        return False

    def deviceToggle(self, dev_id):
        # check the current state and send the opposite command
        current_state = self.device_list[dev_id]["data"]["state"]
        new_state = 0
        if (not current_state) or (self.device_list[dev_id]["dev_type"] == "scene"):
            new_state = 1
        # Send the command and check if it succeeded and update the cache
        if self.deviceAdjust(dev_id, "turnOnOff", "value", new_state):
            self.device_list[dev_id]["data"]["state"] = bool(new_state)
        print("dev data", self.device_list[dev_id]["data"])
        # Save the device data that we modified
        if not self.db is None:
            return
            self.db.device_update_data(dev_id, self.device_list[dev_id]["data"], self.access_token)

    def deviceSetState(self, dev_id, state):
        # Send the command and check if it succeeded and update the cache
        if self.deviceAdjust(dev_id, "turnOnOff", "value", state):
            self.device_list[dev_id]["data"]["state"] = bool(state)

        # Save the device data that we modified
        if not self.db is None:
            self.db.device_update_data(dev_id, self.device_list[dev_id]["data"], self.access_token)
    
    def deviceStateByName(self, dev_name, state):
        for device in self.device_list:
            device = self.device_list[device]
            # Search for the devices with the name
            if device['name'] == dev_name:
                self.deviceSetState(device['id'], state)
