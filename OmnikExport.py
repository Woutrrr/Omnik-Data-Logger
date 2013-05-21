#!/usr/bin/python

import InverterMsg      # Import the Msg handler

import socket               # Needed for talking to inverter
import datetime             # Used for timestamp
import sys
import re
import logging
import ConfigParser, os
from os import path


# For PVoutput 
import urllib, urllib2

# Load the setting
mydir = os.path.dirname(os.path.abspath(__file__))

config = ConfigParser.RawConfigParser()
config.read([mydir + '/config-default.cfg', mydir + '/config.cfg'])

# Receive data with a socket
ip              = config.get('inverter','ip')
port            = config.get('inverter','port')
use_temp        = config.getboolean('inverter','use_temperature')
wifi_serial     = config.getint('inverter', 'wifi_sn')

mysql_enabled   = config.getboolean('mysql', 'mysql_enabled')
mysql_host      = config.get('mysql','mysql_host')
mysql_user      = config.get('mysql','mysql_user')
mysql_pass      = config.get('mysql','mysql_pass')
mysql_db        = config.get('mysql','mysql_db')

smartmeter      = config.getboolean('smartmeter','read_smartmeter')
smartmeter_file = config.get('smartmeter', 'data_file')

pvout_enabled   = config.getboolean('pvout','pvout_enabled')
pvout_apikey    = config.get('pvout','pvout_apikey')
pvout_sysid     = config.get('pvout','pvout_sysid')

read_remote_temperature = config.getboolean('temperature','read_remote_temperature')
temperature_city = config.get('temperature','city')
temperature_country = config.get('temperature','country')

log_enabled     = config.getboolean('log','log_enabled')
log_filename    = mydir + '/' + config.get('log','log_filename')


server_address = ((ip, port))

logger = logging.getLogger('OmnikLogger')
hdlr = logging.FileHandler(log_filename)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.DEBUG)

if read_remote_temperature:
    import serial
    import yweather
    client = yweather.Client()
    loc = temperature_city + ', ' + temperature_country
    id =  client.fetch_woeid(loc)
    loc_weather = client.fetch_weather(id,  metric=True)
    local_temp = float(loc_weather["condition"]["temp"])
    logger.debug("Local temperature is %s" % local_temp)


for res in socket.getaddrinfo(ip, port, socket.AF_INET , socket.SOCK_STREAM):
    af, socktype, proto, canonname, sa = res
    try:
        if log_enabled:
            logger.info('connecting to %s port %s' % server_address)
        s = socket.socket(af, socktype, proto)
        s.settimeout(10)
    except socket.error as msg:
        s = None
        continue
    try:
        s.connect(sa)
        inverter_online = True
    except socket.error as msg:
        s.close()
        s = None
        continue
    break
    
if s is None:
    if log_enabled:
        logger.error('could not open socket')
        inverter_online = False
    

if inverter_online:
    s.sendall(InverterMsg.generate_string(wifi_serial))
    data = s.recv(1024)
    s.close()

    msg = InverterMsg.InverterMsg(data)  # This is where the magic happens ;)


now = datetime.datetime.now()

if log_enabled:
    if inverter_online:
        logger.info("ID: {0}".format(msg.getID())) 


if mysql_enabled:
    # For database output
    import MySQLdb as mdb   
    
    if log_enabled:
        logger.info('Uploading to database')
    con = mdb.connect(mysql_host, mysql_user, mysql_pass, mysql_db);
    
    with con:
        cur = con.cursor()
        cur.execute("""INSERT INTO minutes 
        (InvID, timestamp, ETotal, EToday, Temp, HTotal, VPV1, VPV2, VPV3,
         IPV1, IPV2, IPV3, VAC1, VAC2, VAC3, IAC1, IAC2, IAC3, FAC1, FAC2, 
         FAC3, PAC1, PAC2, PAC3) 
        VALUES 
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
         %s, %s, %s, %s, %s, %s, %s);""", 
         (msg.getID(), now, msg.getETotal(), 
          msg.getEToday(), msg.getTemp(), msg.getHTotal(), msg.getVPV(1), 
          msg.getVPV(2), msg.getVPV(3), msg.getIPV(1), msg.getIPV(2), 
          msg.getIPV(3), msg.getVAC(1), msg.getVAC(2), msg.getVAC(3), 
          msg.getIAC(1), msg.getIAC(2), msg.getIAC(3), msg.getFAC(1), 
          msg.getFAC(2), msg.getFAC(3), msg.getPAC(1), msg.getPAC(2), 
          msg.getPAC(3)) );


if smartmeter:
    logger.info('Reading smartmeter file')
    with open(smartmeter_file , "r") as f:
      for line in f:
          if line.startswith('actual_usage.'):
                s =  line
                actual_usage = s.split()[-1]
                actual_usage.rstrip()

    f.close()
    logger.debug("Actual usage was read %s", actual_usage)

if pvout_enabled and (now.minute % 5) == 0:
    if log_enabled:
        logger.info('Uploading to PVoutput')
    url = "http://pvoutput.org/service/r2/addstatus.jsp"


    if (inverter_online == True or smartmeter == True):
        #Only send data to pvoutput if the inverter is online or we have a smartmeter (consumption)
        get_data = {
                'key' : pvout_apikey,
                'sid' : pvout_sysid,
                'd'   : now.strftime('%Y%m%d'),
                't'   : now.strftime('%H:%M')
            } 
        if inverter_online:
            get_data['v1'] = msg.getEToday() * 1000
            get_data['v2'] = msg.getPAC(1)
            get_data['v6'] = msg.getVPV(1)

        if ( ( use_temp == True and inverter_online == True) or read_remote_temperature == True):
            if (use_temp == True and inverter_online == True):
                temp_reading = msg.getTemp()
            if (read_remote_temperature == True):
                #Overwrite the reading from real value
                temp_reading = local_temp
            
            get_data['v5'] = temp_reading

        if smartmeter:
            get_data['v4'] = actual_usage

        get_data_encoded = urllib.urlencode(get_data)                       # UrlEncode the parameters
    
        logger.debug("Sending url: %s " % url + '?' + get_data_encoded)

        request_object = urllib2.Request(url + '?' + get_data_encoded)      # Create request object
        response = urllib2.urlopen(request_object)                          # Make the request and store the response
    
        if log_enabled:
            logger.info("Response from server: %s" % response.read())                                               # Show the response
    else:
        if log_enabled:
            logger.debug("Inverter is offline and no smartmeter installed")                                               # Show the response

