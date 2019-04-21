#!/usr/bin/python
"""
Get data from the omniksol inverter and output to mqtt. This is a small
utility program that just changes the config to output anything to mqtt.
"""
import OmnikExport
import time
from time import sleep


if __name__ == "__main__":
    omnik_exporter = OmnikExport.OmnikExport('config.cfg')

    omnik_exporter.override_config('general', 'enabled_plugins',
                                   'MQTTOutput')
    omnik_exporter.override_config('log', 'type', 'console')
    omnik_exporter.override_config('log', 'level', 'error') #'debug'

    # run every 30 seconds starting on hh:mm:00 or hh:mm:30
    while True:
        while (time.time() % 30 < 0.001):
            omnik_exporter.run()
            sleep(0.001)

