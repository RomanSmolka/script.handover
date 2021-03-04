import xbmc
import xbmcgui
import xbmcaddon
import json
import requests
import sys
import math

from .lib.ssdp import SSDP_Provider
from .lib.helpers import display_message, log_error

class HandoverUI():

	def __init__(self,):
		self.addon = xbmcaddon.Addon()
		self.player_time = 0
		self.player_file = self.get_player_file()
		self.target = ""
		self.main()

	def main(self):
		xbmc.executebuiltin('ActivateWindow(busydialognocancel)')
		try:
			if not self.player_file:
				message = xbmcgui.Dialog()
				message.ok('Handover', self.addon.getLocalizedString(32026))
				xbmc.executebuiltin('Dialog.Close(busydialognocancel)')
				sys.exit(0)

			ssdp = SSDP_Provider(self.addon)
			ssdp.discover()
			ssdp.resolve()

			addresses = []
			menu_items = []
			for service in ssdp.resolved_devices:
				addresses.append(service)
				menu_items.append(ssdp.resolved_devices[service]['friendlyName'])
		finally:
			xbmc.executebuiltin('Dialog.Close(busydialognocancel)')

		if len(menu_items):
			window = xbmcgui.Dialog()
			menu = window.contextmenu(menu_items)

			self.target = addresses[menu]
			self.send()
		else:
			message = xbmcgui.Dialog()
			message.ok('Handover', self.addon.getLocalizedString(32027))

	def get_player_file(self):
		player = xbmc.Player()
		if player.isPlaying():
			self.player_time = int(math.floor(player.getTime()))
			return player.getPlayingFile()
		else:
			return False

	def send(self):
		post_data = {
			"jsonrpc": "2.0",
			"method": "Player.Open",
			"params": {
				"item": {
					"file": self.player_file
				}
			},
			"id": 1
		}

		if not self.addon.getSettingBool('noresume'):
			offset = self.addon.getSettingInt('offset')
			time = max(0, self.player_time - offset)
			m, s = divmod(time, 60)
			h, m = divmod(m, 60)
			post_data['params']['options'] = {
				"resume": {"hours": h, "minutes": m, "seconds": s, "milliseconds": 0}
			}

		try:
			request = requests.post(
				'http://%s:8080/jsonrpc' % self.target,
				data = json.dumps(post_data),
				timeout = 10
			)
		except requests.exceptions.RequestException as e:
			display_message(self.addon.getLocalizedString(32024), 'ERROR')
			log_error(str(e), True)

		if request.status_code != requests.codes.ok:
			display_message('%s: %s' % (self.addon.getLocalizedString(32025), str(request.status_code)), 'ERROR')
