##
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <t3kpunk@gmail.com> wrote this file.  As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. Widmar 
# ----------------------------------------------------------------------------
##

import PluginLoader

import paho.mqtt.client as mqtt
#import datetime
#import time
import logging


#logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
#log = logging

class MQTTOutput(PluginLoader.Plugin):

    def __init__(self):
        self.client = mqtt.Client()

        log = self.logger

        mqttuser = self.config.get('mqtt', 'user')
        mqttpasswd = self.config.get('mqtt', 'passwd')
        self.client.username_pw_set(username=mqttuser, password=mqttpasswd)
        
        mqtthost = self.config.get('mqtt', 'host')
        mqttport = self.config.get('mqtt', 'port')
        log.info("Connecting to MQTT broker: %s on port: %s", mqtthost, mqttport)
        self.client.connect(mqtthost, int(mqttport), 60)

        # disable callback by #
        #self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_log = self.on_log
        #self.client.on_publish = self.on_publish
        #self.client.on_subscribe = self.on_subscribe

        self.basetopic = self.config.get('mqtt', 'basetopic')
        log.info("Base topic: %s", self.basetopic)
        # enable loop for debug purpose
        #self.client.loop_forever()

    def __del__(self):
        self.client.disconnect()

    # The callback for when the client receives a CONNACK response from the server.
    def on_connect(self, client, userdata, flags, rc):
        log = self.logger
        log.info("Connected with result code "+str(rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        self.client.subscribe("emon/#")


    # The callback for when a PUBLISH message is received from the server.
    def on_message(self, client, userdata, msg):
        #current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # node/subject/topic  [basetopic]/[node]/[keyname]
        basetopic, node, keyname = msg.topic.split("/")

        log = self.logger
        log.debug(msg.topic+" "+str(msg.payload.decode("utf-8")))


    # the built in client logging callback.
    def on_log(self, client, userdata, level, buf):
        self.logger.debug("log: {}".format(buf))


    def on_publish(self, mqttc, obj, mid):
        print("mid: " + str(mid))


    def on_subscribe(self, mqttc, obj, mid, granted_qos):
        print("subscribed: " + str(mid) + " " + str(granted_qos))


    def process_message(self, msg):
        self.logger.debug('process_message(): publishing')
        try:
            self.client.publish(self.basetopic + 'kwh_today', msg.e_today)
        except:
            print('len of raw_msg == {} e_today requires data at position 69'.format(len(msg.raw_msg)))
        self.client.publish(self.basetopic + 'kwh_total', msg.e_total)
        self.client.publish(self.basetopic + 'h_total', msg.h_total)
        self.client.publish(self.basetopic + 'temperature', msg.temperature)

        self.client.publish(self.basetopic + 'v_pv1', msg.v_pv(1))
        self.client.publish(self.basetopic + 'i_pv1', msg.i_pv(1))
        self.client.publish(self.basetopic + 'v_pv2', msg.v_pv(2))
        self.client.publish(self.basetopic + 'i_pv2', msg.i_pv(2))

        self.client.publish(self.basetopic + 'power_ac', msg.p_ac(1))
        self.client.publish(self.basetopic + 'voltage_ac', msg.v_ac(1))
        self.client.publish(self.basetopic + 'current_ac', msg.i_ac(1))
        self.client.publish(self.basetopic + 'frequency_ac', msg.f_ac(1))

        # allow the MQTT engine to publish the data
        self.client.loop(2)
