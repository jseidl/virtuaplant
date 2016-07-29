#!/usr/bin/env python

from gi.repository import GLib, Gtk, Gdk, GObject
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.exceptions import ConnectionException

import argparse
import os
import sys
import time

# Override Argument parser to throw error and generate help message
# if undefined args are passed
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)
        
# Create argparser object to add command line args and help option
parser = MyParser(
	description = 'This Python script runs the SCADA HMI to control the PLC',
	epilog = '',
	add_help = True)
	
# Add a "-i" argument to receive a filename
parser.add_argument("-t", action = "store", dest="server_addr",
					help = "Modbus server IP address to connect the HMI to")

# Print help if no args are supplied
if len(sys.argv)==1:
	parser.print_help()
	sys.exit(1)

# Split and process arguments into "args"
args = parser.parse_args()

MODBUS_SLEEP=1

class HMIWindow(Gtk.Window):
    def initModbus(self):
        # Create modbus connection to specified address and port
        self.modbusClient = ModbusClient(args.server_addr, port=5020)

    # Default values for the HMI labels
    def resetLabels(self):
        self.feed_pump_value.set_markup("<span weight='bold' foreground='gray33'>N/A</span>")
        self.separator_value.set_markup("<span weight='bold' foreground='gray33'>N/A</span>")
        self.level_switch_value.set_markup("<span weight='bold' foreground='gray33'>N/A</span>")
        self.process_status_value.set_markup("<span weight='bold' foreground='gray33'>N/A</span>")
        self.connection_status_value.set_markup("<span weight='bold' foreground='red'>OFFLINE</span>")
     
    def __init__(self):
        # Window title
        Gtk.Window.__init__(self, title="Oil Refinery")
        self.set_border_width(100)
        
        #Create modbus connection
        self.initModbus()

        elementIndex = 0
        # Grid
        grid = Gtk.Grid()
        grid.set_row_spacing(15)
        grid.set_column_spacing(10)
        self.add(grid)

        # Main title label
        label = Gtk.Label()
        label.set_markup("<span weight='bold' size='x-large' color='black'>Crude Oil Pretreatment Unit </span>")
        grid.attach(label, 0, elementIndex, 4, 1)
        elementIndex += 1

        # Crude Oil Feed Pump
        feed_pump_label = Gtk.Label("Crude Oil Tank Feed Pump")
        feed_pump_value = Gtk.Label()
        
        feed_pump_start_button = Gtk.Button("START")
        feed_pump_stop_button = Gtk.Button("STOP")
        
        feed_pump_start_button.connect("clicked", self.setPump, 1)
        feed_pump_stop_button.connect("clicked", self.setPump, 0)
        
        grid.attach(feed_pump_label, 0, elementIndex, 1, 1)
        grid.attach(feed_pump_value, 1, elementIndex, 1, 1)
        grid.attach(feed_pump_start_button, 2, elementIndex, 1, 1)
        grid.attach(feed_pump_stop_button, 3, elementIndex, 1, 1)
        elementIndex += 1
        
        # Level Switch
        level_switch_label = Gtk.Label("Crude Oil Tank Level Switch")
        level_switch_value = Gtk.Label()
        
        level_switch_start_button = Gtk.Button("ON")
        level_switch_stop_button = Gtk.Button("OFF")
        
        level_switch_start_button.connect("clicked", self.setTankLevel, 1)
        level_switch_stop_button.connect("clicked", self.setTankLevel, 0)
        
        grid.attach(level_switch_label, 0, elementIndex, 1, 1)
        grid.attach(level_switch_value, 1, elementIndex, 1, 1)
        grid.attach(level_switch_start_button, 2, elementIndex, 1, 1)
        grid.attach(level_switch_stop_button, 3, elementIndex, 1, 1)
        elementIndex += 1

        #Oil/Water Separator Vessel
        separator_label = Gtk.Label("Oil/Water Separator Vessel")
        separator_value = Gtk.Label()

        separator_start_button = Gtk.Button("START")
        separator_stop_button = Gtk.Button("STOP")

        separator_start_button.connect("clicked", self.setSepVessel, 1)
        separator_stop_button.connect("clicked", self.setSepVessel, 0)

        grid.attach(separator_label, 0, elementIndex, 1, 1)
        grid.attach(separator_value, 1, elementIndex, 1, 1)
        grid.attach(separator_start_button, 2, elementIndex, 1, 1)
        grid.attach(separator_stop_button, 3, elementIndex, 1, 1)
        elementIndex += 1

        # Process status
        process_status_label = Gtk.Label("Process Status")
        process_status_value = Gtk.Label()
        grid.attach(process_status_label, 0, elementIndex, 1, 1)
        grid.attach(process_status_value, 1, elementIndex, 1, 1)
        elementIndex += 1

        # Connection status
        connection_status_label = Gtk.Label("Connection Status")
        connection_status_value = Gtk.Label()
        grid.attach(connection_status_label, 0, elementIndex, 1, 1)
        grid.attach(connection_status_value, 1, elementIndex, 1, 1)
        elementIndex += 1
        
        
        # Oil Refienery branding
        virtual_refinery = Gtk.Label()
        virtual_refinery.set_markup("<span size='small'>Crude Oil Pretreatment Unit - HMI</span>")
        grid.attach(virtual_refinery, 0, elementIndex, 2, 1)

        # Attach Value Labels
        self.feed_pump_value = feed_pump_value
        self.process_status_value = process_status_value
        self.connection_status_value = connection_status_value
        self.separator_value = separator_value
        self.level_switch_value = level_switch_value

        # Set default label values
        self.resetLabels()
        GObject.timeout_add_seconds(MODBUS_SLEEP, self.update_status)

    # Control the feed pump register values
    def setPump(self, widget, data=None):
        try:
            self.modbusClient.write_register(0x01, data)
        except:
            pass
        
    # Control the tank level register values
    def setTankLevel(self, widget, data=None):
        try:
            self.modbusClient.write_register(0x02, data)
        except:
            pass
        
    # Control the separator vessel level register values
    def setSepVessel(self, widget, data=None):
        try:
            self.modbusClient.write_register(0x04, data)
        except:
            pass
    
    # Control the separator feed register values
    def setSepFeed(self, widget, data=None):
        try:
            self.modbusClient.write_register(0x05, data)
        except:
            pass

    def update_status(self):

        try:
            # Store the registers of the PLC in "rr"
            rr = self.modbusClient.read_holding_registers(1,16)
            regs = []

            # If we get back a blank response, something happened connecting to the PLC
            if not rr or not rr.registers:
                raise ConnectionException
            
            # Regs is an iterable list of register key:values
            regs = rr.registers

            if not regs or len(regs) < 16:
                raise ConnectionException
            
            # If the feed pump "0x01" is set to 1, then the pump is running
            if regs[0] == 1:
                self.feed_pump_value.set_markup("<span weight='bold' foreground='green'>RUNNING</span>")
            else:
                self.feed_pump_value.set_markup("<span weight='bold' foreground='red'>STOPPED</span>")
                
            # If the level sensor is ON
            if regs[1] == 1:
                self.level_switch_value.set_markup("<span weight='bold' foreground='green'>ON</span>")
            else:
                self.level_switch_value.set_markup("<span weight='bold' foreground='red'>OFF</span>")
                
            # If the feed pump "0x04" is set to 1, separator is currently processing
            if regs[3] == 1:
                self.separator_value.set_markup("<span weight='bold' foreground='green'>RUNNING</span>")
                self.process_status_value.set_markup("<span weight='bold' foreground='green'>RUNNING </span>")
            else:
                self.separator_value.set_markup("<span weight='bold' foreground='red'>STOPPED</span>")
                self.process_status_value.set_markup("<span weight='bold' foreground='red'>STOPPED </span>")

            # If we successfully connect, then show that the HMI has contacted the PLC
            self.connection_status_value.set_markup("<span weight='bold' foreground='green'>ONLINE </span>")


        except ConnectionException:
            if not self.modbusClient.connect():
                self.resetLabels()
        except:
            raise
        finally:
            return True

def app_main():
    win = HMIWindow()
    win.connect("delete-event", Gtk.main_quit)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()


if __name__ == "__main__":
    GObject.threads_init()
    app_main()
    Gtk.main()
