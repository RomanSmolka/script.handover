import xbmc
import xbmcgui
import sys

def display_message(message, type='INFO'):
# Possible types: INFO, WARNING, ERROR
	dialog = xbmcgui.Dialog()
	dialog.notification('Handover', message, getattr(xbmcgui, 'NOTIFICATION_'+type), 5000)

def log_error(message, fatal=False):
	xbmc.log(msg='Handover: %s' % message, level=xbmc.LOGERROR);
	if fatal:
		sys.exit(0)