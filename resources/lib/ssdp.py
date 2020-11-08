import re
import sys
import socket
import requests
import xml.etree.ElementTree as ET

from helpers import display_message, log_error

try:
	from urlparse import urlparse
except ImportError:
	from urllib.parse import urlparse

class SSDP_Provider():

	def __init__(self,addon):
		self.services = set()
		self.timeout = 1
		self.kodi_modelnames = ['Kodi', 'XBMC Media Center', 'CoreELEC', 'LibreELEC', 'OSMC']
		self.resolved_devices = {}
		self.addon = addon

	def discover(self):
		ssdpDiscover = ('M-SEARCH * HTTP/1.1\r\n' +
						'HOST: 239.255.255.250:1900\r\n' +
						'MAN: "ssdp:discover"\r\n' +
						'MX: 1\r\n' +
						'ST: ssdp:all\r\n' +
						'\r\n')

		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
			sock.sendto(ssdpDiscover.encode('ASCII'), ('239.255.255.250', 1900))
			sock.settimeout(self.timeout)
		except socket.error as e:
			display_message('%s: %s' % (self.addon.getLocalizedString(32023), str(e)), 'ERROR')
			log_error(str(e), True)

		service_re = re.compile('location:[ ]*(.+)\r\n', re.IGNORECASE)
		try:
			while True:
				data, addr = sock.recvfrom(1024)
				result = service_re.search(data.decode('ASCII'))
				if result and (result.group(1) in self.services) == False:
					self.services.add(result.group(1))
		except socket.timeout:
			sock.close()

	def resolve(self):
		if len(self.services) > 0:
			for addr in self.services:
				try:
					response = requests.get(addr, timeout=2)
				except:
					display_message(self.addon.getLocalizedString(32021), 'ERROR')

				try:
					xml = ET.fromstring(response.text)
				except:
					pass

				model_name = xml.find("./{urn:schemas-upnp-org:device-1-0}device/{urn:schemas-upnp-org:device-1-0}modelName").text

				if model_name in self.kodi_modelnames:
					friendly_name = xml.find("./{urn:schemas-upnp-org:device-1-0}device/{urn:schemas-upnp-org:device-1-0}friendlyName").text
					self.resolved_devices[urlparse(addr).hostname] = {
						'friendlyName': friendly_name,
						'modelName': model_name
					}
