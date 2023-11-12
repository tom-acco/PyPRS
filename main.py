import threading
import json
import os

import kiss
from ax253 import Frame
from gpsdclient import GPSDClient

from textual.app import App
from textual.containers import Grid
from textual.reactive import reactive
from textual.widgets import Input, Label, OptionList
from textual.widgets.option_list import Option

#### SET CALLSIGN HERE
os.environ["MYCALL"] = "N0CALL"
####

class GPSD_Thread(threading.Thread):
	def __init__(self, host = "127.0.0.1", port = 2947, callback = None, name = "gpsd_thread"):
		self.host = host
		self.port = port
		self.callback = callback
		super(GPSD_Thread, self).__init__(name=name)
		self.daemon = True
		self.start()

	def run(self):
		print(f"Connecting to GPSD: {self.host}:{self.port}")

		with GPSDClient(host = self.host, port = self.port) as gps:
			for result in gps.json_stream():
				result = json.loads(result)
				self.callback(result)

class KISS_Thread(threading.Thread):
	def __init__(self, host = "127.0.0.1", port = 8001, callback = None, name = "kiss_thread"):
		self.host = host
		self.port = port
		self.callback = callback
		self.src = os.environ.get("MYCALL", "N0CALL")
		super(KISS_Thread, self).__init__(name=name)
		self.daemon = True
		self.start()

	def run(self):
		print(f"Connecting to KISS: {self.host}:{self.port}")

		self.ki = kiss.TCPKISS(host = self.host, port = self.port, strip_df_start=True)
		self.ki.start()
		self.ki.read(callback=self.callback, min_frames=None)

	def send(self, dest, message):
		self.frame = Frame.ui(
			destination=dest,
			source=self.src,
			info=f">{message}",
		)

		self.ki.write(self.frame)

class GPS_Status(Label):
	status = reactive("Waiting for GPS device")
	def render(self):
		return self.status

class APRSDisplay(App):
	line_count = 0

	def compose(self):
		yield Grid(
			OptionList(),
			Input(id = "to", placeholder = "To"),
			Input(id = "message", placeholder = "Message")
		)
		yield GPS_Status()

	def on_mount(self):
		self.gpsd_thread = GPSD_Thread(host = "127.0.0.1", port = 2947, callback = self.gpsd_callback)
		self.kiss_thread = KISS_Thread(host = "127.0.0.1", port = 8001, callback = self.kiss_callback)

		def handle_submit():
			dest = str(dest_input.value)
			
			if not dest:
				dest = "APDW17"

			message = str(message_input.value)
			message_input.value = ""
			
			self.kiss_thread.send(dest, message)
			self.add_message(str(self.kiss_thread.frame))

		dest_input = self.query(Input).first()
		dest_input.focus()

		message_input = self.query(Input).last()
		message_input.action_submit = handle_submit		

	def gpsd_callback(self, result):
		gps_class = result.get("class")

		if gps_class == "TPV":
			if result.get("lat") and result.get("lon"):
				self.query_one(GPS_Status).status = f"{result.get('lat')}, {result.get('lon')}"
		elif gps_class == "DEVICES":
			devices = result.get("devices", [])
			if len(devices) > 0:
				self.query_one(GPS_Status).status = "Searching for GPS"

	def kiss_callback(self, frame):
		frame = Frame.from_bytes(frame)
		message = Option(str(frame))
		
		if frame == self.kiss_thread.frame:
			return
		
		self.add_message(message)
		
	def add_message(self, message):
		self.line_count += 5
		self.query_one(OptionList).add_option(message)
		self.query_one(OptionList).scroll_to(y = self.line_count)


if __name__ == "__main__":
	app = APRSDisplay(css_path="style.tcss")
	app.run()