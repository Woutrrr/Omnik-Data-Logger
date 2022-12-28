##
# ----------------------------------------------------------------------------
# "THE BEER-WARE LICENSE" (Revision 42):
# <t3kpunk@gmail.com> wrote this file.  As long as you retain this notice you
# can do whatever you want with this stuff. If we meet some day, and you think
# this stuff is worth it, you can buy me a beer in return. Widmar 
# ----------------------------------------------------------------------------
# Heavily updated by Christopher McAvaney <christopher.mcavaney@gmail.com>
# Now uses the Homie Convention library (https://github.com/mjcumming/homie4) with 
# a locally defined "Solar Inverter Device".
##

import PluginLoader

from solar_inverter_homie import Device_Solar_Inverter
import time
#import logging


#logging.basicConfig(format='%(asctime)s %(message)s', level=logging.DEBUG)
#log = logging

class MQTTOutput(PluginLoader.Plugin):

    def __init__(self):
        # Translate config items to what homie mqtt library expects for mqtt settings
        mqtt_settings = {
            'MQTT_BROKER' : self.config.get('mqtt', 'host'),
            'MQTT_PORT' : int(self.config.get('mqtt', 'port')),
            'MQTT_USERNAME' : self.config.get('mqtt', 'user'),
            'MQTT_PASSWORD' : self.config.get('mqtt', 'passwd'),
        }

        self.logger.info('{}: creating Device_Solar_Inverter() homie instance'.format(self.__class__.__name__))
        self.solar_inverter_device = Device_Solar_Inverter( device_id=self.config.get('mqtt', 'device_id'), name=self.config.get('mqtt', 'name'), mqtt_settings=mqtt_settings )
        time.sleep(1)

    def process_message(self, msg):
        self.logger.debug('process_message(): publishing')

        pv_v_array = [msg.v_pv(1), msg.v_pv(2), msg.v_pv(3)]
        pv_c_array = [msg.i_pv(1), msg.i_pv(2), msg.i_pv(3)]
        ac_v_array = [msg.v_ac(1), msg.v_ac(2), msg.v_ac(3)]
        ac_c_array = [msg.i_ac(1), msg.i_ac(2), msg.i_ac(3)]
        ac_f_array = [msg.f_ac(1), msg.f_ac(2), msg.f_ac(3)]

        self.solar_inverter_device.update_pv_voltage(pv_v_array, pv_c_array, ac_v_array, ac_c_array, ac_f_array)
        self.solar_inverter_device.update_energy(msg.e_total, msg.e_today, msg.p_ac(1))
        self.solar_inverter_device.update_status(True)

        time.sleep(3)
