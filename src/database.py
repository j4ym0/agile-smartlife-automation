import time, json, os
import sqlite3
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error

class Database:
    def __init__(self, db_type, config):
        self.db_type = db_type
        self.config = config
        self.connection = None

    def connect(self):
        if self.db_type.lower() == "none":
            return None
        elif self.db_type == "sqlite":
            print("Connecting SQLite database")
            if not os.path.exists(self.config["sqlite"]["database"]):
                # file does not exsist so we need to create it 
                self.connection = sqlite3.connect(self.config["sqlite"]["database"])
                cursor = self.connection.cursor()
                cursor.execute(f"""
                    CREATE TABLE `tuya_devices` (
                        `uid` INTEGER NOT NULL,
                        `id` varchar(100) NOT NULL,
                        `name` varchar(100) DEFAULT NULL,
                        `dev_type` varchar(100) DEFAULT NULL,
                        `ha_type` varchar(100) DEFAULT NULL,
                        `dev_data` text DEFAULT NULL
                    ); 
                """)
                cursor.execute(f"""
                    CREATE TABLE `tuya_accounts` (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        `email` varchar(100) NOT NULL UNIQUE,
                        `password` varchar(100) NOT NULL,
                        `access_token` varchar(100) DEFAULT NULL,
                        `refresh_token` varchar(100) DEFAULT NULL,
                        `expires` datetime DEFAULT '1970-01-01 00:00:00'
                    );
                """)
                self.execute("INSERT INTO tuya_accounts (email, password) VALUES(?, ?);", (self.config["tuya"]["email"], self.config['tuya']['password']))
                print(f"SQLite database file created.")
            else:
                # file exists just connect
                self.connection = sqlite3.connect(self.config["sqlite"]["database"])
            
        elif self.db_type == "mysql":
            print("Connecting MYSQL database")
            try:
                self.connection = mysql.connector.connect(
                    host=self.config["mysql"]["host"],
                    user=self.config["mysql"]["user"],
                    password=self.config["mysql"]["password"],
                    database=self.config["mysql"]["database"],
                    port=self.config["mysql"]["port"]
                )
            except Error as e:
                print(f"Error: {e}")
                self.connection = None
        else:
            print("Invalid database type specified in the config.")
        
        return self

    # this has no return of results
    def execute(self, query, data=None):
        if self.connection == None:
            return False
        
        if self.db_type == "sqlite":
            query = query.replace('%s', '?')
            cursor = self.connection.cursor()
        else:
            cursor = self.connection.cursor(buffered=True)

        try:
            if data:
                cursor.execute(query, data)
            else:
                cursor.execute(query)
            self.connection.commit()

            return True
        except Error as e:
            print(f"Error: {e}")
            return False
    # this will return the results
    def query(self, query, data=None):
        if self.connection == None:
            return None

        if self.db_type == "sqlite":
            query = query.replace('%s', '?')
            cursor = self.connection.cursor()
        else:
            cursor = self.connection.cursor(buffered=True)

        try:
            if data:
                cursor.execute(query, data)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor.fetchall()
        except Error as e:
            print(f"Error: {e}")
            return None

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def access_token_get(self, email, password):
        data = (email, password,)
        _query = "SELECT access_token, refresh_token, expires FROM tuya_accounts WHERE email = %s and password = %s and expires > CURRENT_TIMESTAMP"

        result = self.query(_query, data)

        if not result is None:
            for row in result:
                return row
        
        return None, None, 864000

    def access_token_save(self, email, access_token, refresh_token, expires_in):
        current_time = datetime.now()
        if not expires_in is None:
            current_time = current_time + timedelta(seconds=expires_in)
        expires = current_time.strftime(self.config["mysql_fromat"])

        data = (access_token, refresh_token, expires, email)
        _query = "UPDATE tuya_accounts SET access_token = %s, refresh_token = %s, expires = %s WHERE email = %s"

        self.execute(_query, data)

    def device_save(self, access_token, id, name, dev_type, ha_type, dev_data):
        # delete the device so we can update it
        data = (id,)
        _query = "DELETE FROM tuya_devices WHERE id = %s"
        self.execute(_query, data)

        data = (access_token, id, name, dev_type, ha_type, str(dev_data),)
        _query = "INSERT INTO tuya_devices (uid, id, name, dev_type, ha_type, dev_data) VALUES ((SELECT ID FROM tuya_accounts WHERE access_token = %s), %s, %s, %s, %s, %s)"

        self.execute(_query, data)

    def device_get_list(self, access_token):
        # delete the device so we can update it
        data = (access_token,)
        _query = "SELECT id, name, dev_type, ha_type, dev_data FROM tuya_devices WHERE uid = (SELECT ID FROM tuya_accounts WHERE access_token = %s)"

        return self.query(_query, data)

    def device_update_data(self, id, data, access_token):
        # Check if data is string or dictionary
        if type(data) is dict:
            data = json.dumps(data)
        data = (data, id, access_token,)
        _query = "UPDATE tuya_devices SET dev_data = %s WHERE id = %s AND uid = (SELECT ID FROM tuya_accounts WHERE access_token = %s)"

        self.execute(_query, data)


