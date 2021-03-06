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
    init()

    MQTT_TOPIC = "%s/#" % SAMUR_ID
    topic = "%s/in" % SAMUR_ID
    def on_connect(client, userdata, flags, rc):
        client.subscribe(MQTT_TOPIC, 0)

    def on_subscribe(client, userdata, mid, granted_qos):
        print "Subscribed to MQTT with Topic: %s" % MQTT_TOPIC

    def on_message(client, userdata, message):
        if message.topic == topic:
            try:
                msg = json.loads(message.payload)
                if msg["command"] == "switchlight":
                    state = GPIO.LOW
                    if msg["switchcmd"] == "On": state = GPIO.HIGH
                    unit = msg["unit"]
                    if unit < 13:
                        MB.digitalWrite("K"+str(unit), state)
                    else:
                        MB.digitalWrite("V"+str(unit-12), state)
            except:
                pass

        # topic:samurid/K1/set payload:ON
        elif message.topic.startswith(SAMUR_ID):
            try:
                relay = message.topic.split("/")[1]
                state = GPIO.LOW
                if message.payload == "ON": state = GPIO.HIGH
                MB.digitalWrite(relay, state)
            except:
                return

        print message.topic, message.payload

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
                contact = "L%d" % (i+1)
                if i > 7:
                    contact = "D%d" % (i-7)

                # Topic for General MQTT
                topic = "%s/%s/contact" % (SAMUR_ID, contact)

                # Message for Domoticz
                MQTT_MSG = '{"command": "switchlight", "idx": %d, "switchcmd": "%s" }' % (i+16, state)

                client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL) 

                # Publishing for Domoticz
                client.publish(MQTT_TOPIC, MQTT_MSG)

                # Publishing for General MQTT
                client.publish(topic, state.upper())


                client.disconnect()

        prev_line = line
        sleep(1)

def init():
    MQTT_TOPIC = "domoticz/in"
    client = mqtt.Client()
    client.on_publish = on_publish
    client.on_connect = on_connect
    client.username_pw_set(MQTT_USER, MQTT_PASS)

    for i in range(15):
        MB.relays.outputAll([0] * 16)
        state = "Off"
        contact = "K%d" % (i+1)
        topic = "%s/%s/contact" % (SAMUR_ID, contact)
        MQTT_MSG = '{"command": "switchlight", "idx": %d, "switchcmd": "%s" }' % (i+1, state)
        client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL) 
        client.publish(MQTT_TOPIC, MQTT_MSG)
        client.publish(topic, state.upper())
        client.disconnect()
    sleep(3)

def on_connect(mosq, obj, rc):
    print "Connected to MQTT Broker"

def on_publish(client, userdata, mid):
    pass
#    print "Message Published..."

if __name__ == "__main__":
    try:
        while 1:
            main()
    except KeyboardInterrupt:
        print "\rCtrl-C - Quit."

        GPIO.cleanup()
