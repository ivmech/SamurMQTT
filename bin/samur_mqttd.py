import os
import sys
import select
import RPi.GPIO as GPIO
from time import sleep
import paho.mqtt.client as mqtt
import json
import threading

import ConfigParser
import io

import samur

MB = samur.Mainboard()
thread = None

with open("/etc/samur.conf") as f:
    sample_config = f.read()
config = ConfigParser.RawConfigParser(allow_no_value=True)
config.readfp(io.BytesIO(sample_config))

# Define Variables
try:
    MQTT_BROKER = config.get("MQTT", "BROKER")
    MQTT_PORT = int(config.get("MQTT", "PORT"))
    MQTT_USER = config.get("MQTT", "USER")
    MQTT_PASS = config.get("MQTT", "PASS")
    SAMUR_ID = config.get("MQTT", "SAMURID")
    MQTT_KEEPALIVE_INTERVAL = int(config.get("MQTT", "INTERVAL"))
except:
    SAMUR_ID = "samur70"
    MQTT_BROKER = "localhost"
    MQTT_PORT = 1883
    MQTT_USER = ""
    MQTT_PASS = ""
    MQTT_KEEPALIVE_INTERVAL = 45

def main():
    MQTT_TOPIC = "%s/#" % SAMUR_ID
    topic = "%s/in" % SAMUR_ID
    def on_connect(client, userdata, flags, rc):
        client.subscribe(MQTT_TOPIC, 0)

    def on_subscribe(client, userdata, mid, granted_qos):
        print "Subscribed to MQTT with Topic: %s" % MQTT_TOPIC

    def on_message(client, userdata, message):
        print message.payload
        if message.topic == topic:
            msg = json.loads(message.payload)
            if msg["command"] == "switchlight":
                state = GPIO.LOW
                if msg["switchcmd"] == "On": state = GPIO.HIGH
                unit = msg["unit"]
                if unit < 13:
                    MB.digitalWrite("K"+str(unit), state)
                else:
                    MB.digitalWrite("V"+str(unit-12), state)

    thread = threading.Thread(target=worker)
    thread.start()

    # Connect MQTT as Subscriber
    client = mqtt.Client()
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_subscribe = on_subscribe
    client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)
    client.loop_forever()

def worker():
    MQTT_TOPIC = "domoticz/in"
    
    def on_connect(mosq, obj, rc):
	    print "Connected to MQTT Broker"

    # Define on_publish event Handler
    def on_publish(client, userdata, mid):
	    print "Message Published..."

    client = mqtt.Client()
    client.on_publish = on_publish
    client.on_connect = on_connect
    client.username_pw_set(MQTT_USER, MQTT_PASS)

    prev_line = [1]*14
    while 1:
        line = MB.digitalReadAll()
        for i,l in enumerate(line):
            state = "Off"
            if l != prev_line[i]:
                if not l: state = "On"
                MQTT_MSG = '{"command": "switchlight", "idx": %d, "switchcmd": "%s" }' % (i+16, state)
                client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL) 
                client.publish(MQTT_TOPIC, MQTT_MSG)
                client.disconnect()
        prev_line = line
        sleep(1)

if __name__ == "__main__":
    try:
        while 1:
            main()
    except KeyboardInterrupt:
        print "\rCtrl-C - Quit."

        GPIO.cleanup()
