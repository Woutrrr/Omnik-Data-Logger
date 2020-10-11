#!/usr/bin/python3
"""OmnikExport program.

Get data from an omniksol inverter with 602xxxxx - 606xxxx ans save the data in
a database or push to pvoutput.org.
"""
import socket  # Needed for talking to inverter
import sys
import logging
import logging.config
import configparser
import os
from PluginLoader import Plugin
import InverterMsg  # Import the Msg handler
import codecs
import re


class OmnikExport(object):
    """
    Get data from Omniksol inverter and store the data in a configured output
    format/location.

    """

    config = None
    logger = None

    def __init__(self, config_file):
        # Load the setting
        config_files = [self.__expand_path('config-default.cfg'),
                        self.__expand_path(config_file)]

        self.config = configparser.RawConfigParser()
        self.config.read(config_files)

    def run(self):
        """Get information from inverter and store is configured outputs."""

        self.build_logger(self.config)

        # Load output plugins
        # Prepare path for plugin loading
        sys.path.append(self.__expand_path('outputs'))

        Plugin.config = self.config
        Plugin.logger = self.logger

        enabled_plugins = self.config.get('general', 'enabled_plugins')\
                                     .split(',')
        for plugin_name in enabled_plugins:
            plugin_name = plugin_name.strip()
            self.logger.debug('Importing output plugin ' + plugin_name)
            __import__(plugin_name)

        # Connect to inverter
        ip = self.config.get('inverter', 'ip')
        port = self.config.get('inverter', 'port')

        for res in socket.getaddrinfo(ip, port, socket.AF_INET,
                                      socket.SOCK_STREAM):
            family, socktype, proto, canonname, sockadress = res
            try:
                self.logger.info('connecting to {0} port {1}'.format(ip, port))
                inverter_socket = socket.socket(family, socktype, proto)
                inverter_socket.settimeout(10)
                inverter_socket.connect(sockadress)
            except socket.error as msg:
                self.logger.error('Could not open socket')
                self.logger.error(msg)
                sys.exit(1)

        wifi_serial = self.config.getint('inverter', 'wifi_sn')
        inverter_socket.sendall(OmnikExport.generate_string(wifi_serial))
        data = inverter_socket.recv(1024)
        inverter_socket.close()

        msg = InverterMsg.InverterMsg(data)

        # At this point the Inverter could be starting up or shutting down
        # What appears to be common at this point is the ID isn't of the expected form
        # when in error: some Chinese characters
        # expecting something like: SF5K016008677
        if re.match(r'^[A-Z0-9]+$', msg.id) == None:
            self.logger.error('Inverter not in correct state')
            sys.exit(1)

        try:
            self.logger.info("ID: {0}".format(msg.id))
        except UnicodeDecodeError:
            print('some issue with data or InverterMsg decoding')
            print('data == {}'.format(data))
            print('msg == {}'.format(msg))

        for plugin in Plugin.plugins:
            self.logger.debug('Run plugin' + plugin.__class__.__name__)
            plugin.process_message(msg)

    def build_logger(self, config):
        # Build logger
        """
        Build logger for this program


        Args:
            config: ConfigParser with settings from file
        """
        log_levels = dict(debug=10, info=20, warning=30, error=40, critical=50)
        log_dict = {
            'version': 1,
            'formatters': {
                'f': {'format': '%(asctime)s %(levelname)s %(message)s'}
            },
            'handlers': {
                'none': {'class': 'logging.NullHandler'},
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'f'
                },
                'file': {
                    'class': 'logging.FileHandler',
                    'filename': self.__expand_path(config.get('log',
                                                              'filename')),
                    'formatter': 'f'},
            },
            'loggers': {
                'OmnikLogger': {
                    'handlers': config.get('log', 'type').split(','),
                    'level': log_levels[config.get('log', 'level')]
                }
            }
        }
        logging.config.dictConfig(log_dict)
        self.logger = logging.getLogger('OmnikLogger')

    def override_config(self, section, option, value):
        """Override config settings"""
        self.config.set(section, option, value)

    @staticmethod
    def __expand_path(path):
        """
        Expand relative path to absolute path.

        Args:
            path: file path

        Returns: absolute path to file

        """
        if os.path.isabs(path):
            return path
        else:
            return os.path.dirname(os.path.abspath(__file__)) + "/" + path

    @staticmethod
    def generate_string(serial_no):
        """Create request string for inverter.

        The request string is build from several parts. The first part is a
        fixed 4 char string; the second part is the reversed hex notation of
        the s/n twice; then again a fixed string of two chars; a checksum of
        the double s/n with an offset; and finally a fixed ending char.

        Args:
            serial_no (int): Serial number of the inverter

        Returns:
            str: Information request string for inverter
        """
        # changed by python3
        response = b'\x68\x02\x40\x30'

        double_hex = hex(serial_no)[2:] * 2

        # changed for python3
        hex_list = [codecs.decode(double_hex[i:i + 2], 'hex') for i in
                    reversed(range(0, len(double_hex), 2))]

        cs_count = 115 + sum([ord(c) for c in hex_list])

        # changed for python3
        checksum = codecs.decode(hex(cs_count)[-2:], 'hex')

        # changed for python3
        response += b''.join(hex_list) + b'\x01\x00' + checksum + b'\x16'

        return response


if __name__ == "__main__":
    omnik_exporter = OmnikExport('config.cfg')
    omnik_exporter.run()
