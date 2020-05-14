#! /usr/bin/python3

import adafruit_dht
import board
import time
from time import sleep
from datetime import datetime

from influxdb import InfluxDBClient
import syslog
syslog.syslog("Temperature Reading Started")

dhtDevice = adafruit_dht.DHT11(board.D4)

t = None
t_last = None
h = None

attempts = 15
while attempts > 0:
   sleep(1)
   attempts = attempts - 1
   print(attempts)
   try: 
       t = dhtDevice.temperature
       h = dhtDevice.humidity
       if (t is not None) and (h is not None):
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

if (t < 10) or (t > 35) :
    syslog.syslog(syslog.LOG_WARNING, "Implausible temperature {0}, last {1}. Abandon".format(t, t_last))
    exit(1)

t_last = t

CALIBRATION_OFFSET = -2.0
t += CALIBRATION_OFFSET

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

syslog.syslog(syslog.LOG_INFO, "Temp: {:.1f} C, Hum: {}%".format(t,h))
client = InfluxDBClient('influxserver.lan', 8086, 'influx_username', 'influx_password', 'influx_database_name_here')
client.write_points(json_body)
