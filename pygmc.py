"""PyGMC is a library to communicate with the GQ Electronics GMC 500, 500+, 600, and 600+ using the device's custom protocol.
It implements all documented commands, and provides a mechanism to access and update the device configuration.

Sources used:
GQ RFC 1801: https://www.gqelectronicsllc.com/download/GQ-RFC1801.txt
Config Memory layout: https://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=9643
"""


import csv
import ctypes
from enum import IntEnum
import datetime
import struct
import time

from construct import Bytes, CString, NullStripped, PaddedString, Struct, Padding, Int16ub, Int24ub, Int32ub, Int8ub
import serial

config_format = Struct(
	'power' / Int8ub,
	'alarm' / Int8ub,
	'speaker'	/ Int8ub,
	'idle_display_mode' / Int8ub,
	'back_light_timeout_seconds' / Int8ub,
	'idle_title_display_mode' / Int8ub,
	'alarm_CPM_value' / 	Int16ub,
	'calib_CPM_0' / Int16ub,
	'calib_uSv_0' / Int32ub,
	'calib_CPM_1' / Int16ub,
	'calib_uSv_1' / Int32ub,
	'calib_CPM_2' / Int16ub,
	'calib_uSv_2' / Int32ub,
	'idle_text_state' / Int8ub,
	'alarm_value_uSv' / Int32ub,
	'alarm_type' / Int8ub,
	'save_data_type' / Int8ub,
	'swivel_display' / Int8ub,
	'zoom' / Int32ub,
	'SPI_data_save_address' / Int24ub,
	'SPI_data_read_address' / Int24ub,
	'power_saving_mode' / Int8ub,
	'sensitivity_mode' / Int8ub,
	'counter_delay' / Int16ub,
	'display_contrast' / Int8ub,
	'max_CPM' / Int16ub,
	'unknown1' / Int8ub,
	'large_font_mode' / Int8ub,
	'LCD_back_light_level' / Int8ub,
	'reverse_display_mode' / Int8ub,
	'motion_detect'	/ Int8ub,
	'battery_type' / Int8ub,
	'baudrate' / Int8ub,
	'CPM_speaker_on_off_calib' / Int8ub,
	'graphic_drawing_mode' / 	Int8ub,
	'LED_on_off' / Int8ub,
	'unknown2' / Int8ub,
	'save_threshold_value_uSv_m_nCPM' / Int16ub,
	'save_threshold_mode' / Int8ub,
	'save_threshold_value' / Int32ub,
	'SSID' / PaddedString(64, 'ascii'),
	'password' / 	PaddedString(64, 'ascii'),
	'website' / PaddedString(32, 'ascii'),
	'URL' / 	PaddedString(32, 'ascii'),
	'user_ID' / 	PaddedString(32, 'ascii'),
	'counter_ID' / 	PaddedString(32, 'ascii'),
	'period' / Int8ub,
	'WIFI_on_off' / Int8ub,
	'text_status_mode' / Int8ub,
	'fast_estimate_time' / Int8ub,
	'third_party_output' / Int8ub,
	'high_voltage_level_tube_1' / Int8ub,
	'high_voltage_level_tube_2' / Int8ub,
	'CPM_tube_mode' / Int8ub,
	'CPM_tube_display' / Int8ub,
	'voltage_display' / Int8ub,
	'deadtime_enable' / Int8ub,
	'deadtime_tube_1' / Int16ub,
	'deadtime_tube_2' / Int16ub,
	'medium_threshold' / Int16ub,
	'high_threshold' / Int16ub,
	'speaker_volume' / Int8ub,
	'HV_reading' / Int8ub,
	'target_HV' / Int16ub,
	'HV_calib' / Int8ub,
	'SS1' / Bytes(6),
	'SS2' / 	Bytes(6),
	'SS3' / Bytes(6),
	'SS4' / Bytes(6),
	'accuracy_display' / Int8ub,
	'dose_alarm_0' / Int8ub,
	'dose_alarm_1' / Int8ub,
	'dose_alarm_2' / Int8ub,
	'dose_alarm_3' / Int8ub,
	'save_date_time' / Bytes(6),
	'unused' / Padding(128, b'\xff'),
)

hex_byte = lambda x: chr(x).encode('ascii')

OK = b'\xaa'

AP_LIST_FIELDS = [
	'ecn', 'ssid', 'rssi', 'mac', 'channel', 'freq_offset', 'freqcal_val', 'pairwise_cipher', 'group_cipher', 'bgn', 'wps'
]

AP_STATUS_FIELDS = [
	'ssid', 'bssid', 'channel', 'rssi', 'pci_en', 'reconn_interval', 'listen_interval', 'scan_mode', 'pmf'
]

class EncryptionMethod(IntEnum):
	OPEN = 0
	WEP = 1
	WPA_PSK = 2
	WPA2_PSK = 3
	WPA_WPA2_PSK = 4
	WPA2_ENTERPRISE = 5
	WPA3_PSK = 6
	WPA2_WPA3_PSK = 7
	WAPI_PSK = 8

class GMCConnection:

	def __init__(self, port):
		self.connection = serial.Serial(port, 115200, timeout=0.5, write_timeout=0.5)

	def send_command(self, command, response_format=None, expected_response=None):
		to_send = b'<' + command + b'>>'
		self.write(to_send)
		response = self.read_all()
		if expected_response and response != expected_response:
			raise 	ValueError("Expected response '{}' but got '{}'".format(expected_response, response))
		if response_format:
			unpacked = struct.unpack(response_format, response)
			if len(unpacked) == 1:
				return unpacked[0]
			return unpacked
		return response

	def write(self, ascii_data):
		return self.connection.write(ascii_data)

	def read_all(self):
		buffer = b''
		while new_data := self.connection.read():
			buffer += new_data
		return buffer

class GMCGeigerCounter:

	def __init__(self, connection):
		self.connection = connection

	def get_ver(self):
		return self.connection.send_command(b'GETVER').decode('ascii')

	def get_CPM(self):
		return self.connection.send_command(b'GETCPM', '!I')

	def get_CPS(self):
		return self.connection.send_command(b'GETCPS', '!I')

	def get_CPML(self):
		return self.connection.send_command(b'GETCPML', '!I')

	def get_CPMH(self):
		return self.connection.send_command(b'GETCPMH', '!I')

	def get_CPSL(self):
		return self.connection.send_command(b'GETCPSL', '!I')

	def get_CPSH(self):
		return self.connection.send_command(b'GETCPSH', '!I')

	def get_battery_voltage(self):
		response = self.connection.send_command(b'GETVOLT')
		return float(ctypes.create_string_buffer(response).value[:-1])

	def get_config(self):
		raw_config = self.connection.send_command(b'GETCFG')
		return config_format	.parse(raw_config)

	def erase_config(self):
		self.connection.send_command(b'ECFG', expected_response=OK)

	def set_config(self, config):
		to_write = config_format.build(config)
		for address, byte in enumerate(to_write):
			self.write_config_byte(address, byte)

	def write_config_byte(self, address, data_byte):
		address_bytes = 	struct.pack('!H', address)
		data_byte_bytes = struct.pack('!B', data_byte)
		to_write = b'WCFG' + address_bytes + data_byte_bytes
		self.connection.send_command(to_write, expected_response=OK)

	def reload_config(self):
		self.connection.send_command(b'CFGUPDATE', expected_response=OK)

	def get_datetime(self):
		response = self.connection.send_command(b'GETDATETIME')
		return self.parse_datetime(response)

	@staticmethod
	def parse_datetime(timestamp_bytes):
		y, m, d, h, mi, s = map(lambda b: ord(chr(b)), timestamp_bytes[:6])
		return datetime.datetime(y + 2000, m, d, h, mi, s)

	def set_datetime(self, datetime):
		to_send = 	b'SETDATETIME' + hex_byte(datetime.year - 2000) + \
			hex_byte(datetime.month) + \
			hex_byte(datetime.day) + \
			hex_byte(datetime.hour) + \
			hex_byte(datetime.minute) + \
			hex_byte(datetime.second)
		return self.connection.send_command(to_send, expected_response=OK)

	def factory_reset(self):
		self.connection.send_command(b'FACTORYRESET', expected_response=OK)

	def power_on(self):
		return self.connection.send_command(b'POWERON')

	def power_off(self):
		return self.connection.send_command(b'POWEROFF')

	def alarm_on(self):	
		self.connection.send_command(b'ALARM1', expected_response=OK)

	def alarm_off(self):
		self.connection.send_command(b'ALARM0', expected_response=OK)

	def speaker_on(self):
		self.connection.send_command(b'SPEAKER1', expected_response=OK)

	def speaker_off(self):
		self.connection.send_command(b'SPEAKER0', expected_response=OK)

	def wifi_on(self):
		self.connection.send_command(b'WiFiON', expected_response=OK)

	def wifi_off(self):
		self.connection.send_command(b'WiFiOFF', expected_response=OK)

	def get_serial(self):
		return self.connection.send_command(b'GETSERIAL').hex()

	def get_gyro(self):
		return self.connection.send_command(b'GETGYRO', '!HHHx')

	def reboot(self):
		return self.connection.send_command(b'REBOOT')

	def get_temperature(self):
		return self.connection.send_command(b'GETTEMP')

	def set_date_yy(self, year ):
		return 	self.connection.send_command(b'SETDATEYY' + hex_byte(year), '!B', OK)

	def set_date_mm(self, month):
		return 	self.connection.send_command(b'SETDATEMM' + hex_byte(month), '!B', OK)

	def set_date_dd(self, day):
		return 	self.connection.send_command(b'SETDATEDD' + hex_byte(day), '!B', expected_response=OK)

	def set_date(self, date):
		self.set_date_yy(date.year - 2000)
		self.set_date_mm(date.month)
		self.set_date_dd(date.day)

	def set_time_hh(self, hour):
		return	self.connection.send_command(b'SETTIMEHH' + hex_byte(hour), '!B', expected_response=OK)

	def set_time_mm(self, minute):
		return	self.connection.send_command(b'SETTIMEMM' + hex_byte(minute), '!B', expected_response=OK)

	def	set_time_ss(self, second):
		return	self.connection.send_command(b'SETTIMESS' + hex_byte(second), '!B', expected_response=OK)

	def set_time(self, time):
		self.set_time_ss(time.second)
		self.set_time_mm(time.minute)
		self.set_time_hh(time.hour)

	def at_command(self, command, wait=5.0):
		self.connection.write	(b'<AT+' + command.encode('ascii') + b'>>')
		time.sleep(wait)
		return	self.connection.read_all().decode('ascii').split('\r\n')

	def list_wifi_networks(self):
		raw_response = self.at_command('CWLAP')
		data = [d.split(':(')[1][:-1] for d in raw_response[1:]]
		reader = csv.DictReader(data, AP_LIST_FIELDS)
		networks = []
		for network in reader:
			network['ecn'] = EncryptionMethod(int(network['ecn']))
			networks.append(network)
		return networks

	def disconnect_wifi(self):
		return self.at_command('CWQAP')

	def wifi_auto_connect(self, enable=True):
		return 		self.at_command('CWAUTOCONN=' + ('1' if enable else '0'))

	def get_MAC_address(self):
		response = self.at_command('CIPSTAMAC?')
		return response[1].split('MAC:')[1].strip()[1:-1]

	def set_SSID(self, ssid):
		self.connection.send_command(b'SETSSID' + ssid.encode('ascii'), expected_response=OK)

	def set_wifi_password(self, password):
		self.connection.send_command(b'SETWIFIPW' + password.encode('ascii'), expected_response=OK)

	def get_wifi_status(self):
		response = self.at_command('CWJAP?')
		reader = csv.DictReader(response[1][7:], AP_STATUS_FIELDS)
		return next(reader)

if __name__ == '__main__':
	geiger = GMCGeigerCounter(connection=GMCConnection(port='COM3'))
