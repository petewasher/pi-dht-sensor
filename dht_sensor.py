#! /usr/bin/python3

import adafruit_dht
import board
import time
from time import sleep
from datetime import datetime

from influxdb import InfluxDBClient
import syslog
syslog.syslog("Temperature Reading Started")

# Create the device using GPIO 4
dhtDevice = adafruit_dht.DHT11(board.D4)

# Temperature and humidity
t = None
h = None

# As te adafruit example tells us, the comms are 
# sometimes flaky. We need to try a few times 
# potentially, otherwise we'll get None readings 
# for temperature and humidity.
attempts = 15
while attempts > 0:
   sleep(1)
   attempts = attempts - 1
   try: 
       t = dhtDevice.temperature
       h = dhtDevice.humidity
       if (t is not None) and (h is not None):
          # Success!
          print (t)
          print (h)
          break
   except TypeError as err:
       print(err.args[0])
       syslog.syslog(syslog.LOG_INFO, (err.args[0]))
       sleep(1)
       pass
   except RuntimeError as err:
       print(err.args[0])
       syslog.syslog(syslog.LOG_INFO, (err.args[0]))
       sleep(1)
       pass
   except err:
       print(err)
       sleep(1)

if (t is None) or (h is None):
   print("Failed to get reading")
   syslog.syslog(syslog.LOG_INFO, "Catastrophic fail to get reading after many attempts")
   exit(1)

# Sanity check the readings. Sometimes they spike?? not clear why yet.
if (t < 10) or (t > 35) :
    syslog.syslog(syslog.LOG_WARNING, "Implausible temperature {0}. Abandon".format(t))
    exit(1)

# Prep some JSON we will send to influxdb:
json_body = [
        {
            "measurement": "temperature",
            "tags": {
                "device": "kitchen",
                "type": "dht11"
                },
            "fields": {
               "deg_c": float(t),
               "humidity_percent": float(h)
            },
            "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
            }
        ]

# Post a message in the syslog to say what we read - useful for tracking
syslog.syslog(syslog.LOG_INFO, "Temp: {:.1f} C, Hum: {}%".format(t,h))

# Connect to the influxdb, setting all these settings as appropriate. 
client = InfluxDBClient('influxserver.lan', 8086, 'influx_username', 'influx_password', 'influx_database_name_here')
client.write_points(json_body)
