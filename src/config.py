config = {
    "database_type": "mysql",
    "sqlite": {
        "database": "sqlite.db"
    },
    "mysql": {
        "host": "172.17.0.1",
        "user": "agile",
        "password": "password",
        "database": "agile",
        "port": 3306
    },

    "tuya": {
        "email": "",
        "password": "",
        "country": "eu"
    },

    "triggers": [
        {
            "device_name": "Lamp",   
            "state": "on",   
            "trigger": "time",   
            "time": "21:00",   
        },
        {
            "device_name": "Lamp",   
            "state": "off",   
            "trigger": "time",   
            "time": "21:30",   
        },
    ],
    
    "valid_fromat": "%Y-%m-%dT%H:%M:%SZ",
    "mysql_fromat": "%Y-%m-%d %H:%M:%S",
    "fromat_incTZ": "%Y-%m-%dT%H:%M:%S%z",

}
