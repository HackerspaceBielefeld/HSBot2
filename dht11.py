#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import urllib2
import Adafruit_DHT
import paho.mqtt.publish as mospub
from time import sleep

sensor = Adafruit_DHT.DHT11
pin = 4
mqttserv = '127.0.0.1'
mqtttopt = 'sensors/temperatur/innen'
mqtttoph = 'sensors/luftfeuchtigkeit/innen'
host     = 'https://hackerspace-bielefeld.de/spacestatus/spacestatus.php'

humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

if humidity is not None and temperature is not None:
	mospub.single(mqtttopt, payload=temperature, hostname=mqttserv)
	sleep(1)
	mospub.single(mqtttoph, payload=humidity, hostname=mqttserv)
	print('Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(temperature, humidity))

	urllib2.urlopen(host +"?temp_in="+ str(temperature) +"&humi_in="+ str(humidity)).read()

	sys.exit(0)
else:
    print('Failed to get reading. Try again!')
    sys.exit(1)