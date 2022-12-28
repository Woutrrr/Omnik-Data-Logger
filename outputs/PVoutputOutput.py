import PluginLoader
import datetime

# put in place for python2 vs python3 compatibility
import six
if six.PY2:
    import urllib
    import urllib2
elif six.PY3:
    import requests



class PVoutputOutput(PluginLoader.Plugin):
    """Sends the data from the Omnik inverter to PVoutput.org"""

    def process_message(self, msg):
        """Send the information from the inverter to PVoutput.org.

        Args:
            msg (InverterMsg.InverterMsg): Message to process

        """
        now = datetime.datetime.now()

        if (now.minute % 5) == 0:  # Only run at every 5 minute interval
            self.logger.info('Uploading to PVoutput')

            url = "http://pvoutput.org/service/r2/addstatus.jsp"

            # always provided data
            get_data = {
                'key': self.config.get('pvout', 'apikey'),
                'sid': self.config.get('pvout', 'sysid'),
                'd': now.strftime('%Y%m%d'),
                't': now.strftime('%H:%M'),
                'v2': msg.p_ac(1),
                'v6': msg.v_ac(1)
            }
            # optionally provided data
            if self.config.getboolean('inverter', 'use_temperature'):
                get_data['v5'] = msg.temperature
            if self.config.getboolean('pvout', 'provide_energy_value'):
                get_data['v1'] = msg.e_today * 1000

            if six.PY2:
                get_data_encoded = urllib.urlencode(get_data)

                request_object = urllib2.Request(url + '?' + get_data_encoded)
                response = urllib2.urlopen(request_object)

                self.logger.info(response.read())  # Log the response
            elif six.PY3:
                self.logger.debug(get_data)
                response = requests.get(url, params=get_data)

                self.logger.info(response)  # Log the response
                self.logger.info(response.text)  # Log the response
        else:
                self.logger.info('not at a 5 minute interval')
