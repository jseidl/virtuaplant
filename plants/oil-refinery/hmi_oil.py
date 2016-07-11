#!/usr/bin/env python

from gi.repository import GLib, Gtk, GObject
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.exceptions import ConnectionException
import pygtk
import socket

s = socket.socket()
host = '192.168.228.143'
port = 5020
s.connect((host, port))
#print s.recv(1024)

MODBUS_SLEEP=1

class HMIWindow(Gtk.Window):

    def initModbus(self):

        self.modbusClient = ModbusClient('localhost', port=5020)

    def resetLabels(self):
        self.crudeOilValue.set_markup("<span weight='bold' foreground='red'>STOPPED</span>")
        self.boilerValveValue.set_markup("<span weight='bold' foreground='red'>CLOSED</span>")
        self.boilerTempValue.set_markup("<span weight='bold' foreground='green'>NORMAL</span>")
        self.processStatusValue.set_markup("<span weight='bold' foreground='red'>STOPPED</span>")
        self.connectionStatusValue.set_markup("<span weight='bold' foreground='red'>OFFLINE</span>")
        self.distTwrValveValue.set_markup("<span weight='bold' foreground='red'>CLOSED</span>")
     
    def __init__(self):
        Gtk.Window.__init__(self, title="Oil Refining - HMI - Oil Refinery")

        self.set_border_width(100)
        
        self.initModbus()

        elementIndex = 0

        # Grid
        grid = Gtk.Grid()
        grid.set_row_spacing(15)
        grid.set_column_spacing(10)
        self.add(grid)

        # Main title label
        label = Gtk.Label()
        label.set_markup("<span weight='bold' size='x-large' color='black'>Oil Refining Process</span>")
        grid.attach(label, 0, elementIndex, 2, 1)
        elementIndex += 1

        # Crude Oil barrel
        crudeOilLabel = Gtk.Label("Crude Oil Dumping Status")
        crudeOilValue = Gtk.Label()
        grid.attach(crudeOilLabel, 0, elementIndex, 1, 1)
        grid.attach(crudeOilValue, 1, elementIndex, 1, 1)
        elementIndex += 1

        # Boiler Valve
        boilerValveLabel = Gtk.Label("Boiler Valve Status")
        boilerValveValue = Gtk.Label()
        grid.attach(boilerValveLabel, 0, elementIndex, 1, 1)
        grid.attach(boilerValveValue, 1, elementIndex, 1, 1)
        elementIndex += 1

        # Boiler Temperature
        boilerTempLabel = Gtk.Label("Boiler Temperature")
        boilerTempValue = Gtk.Label()
        grid.attach(boilerTempLabel, 0, elementIndex, 1, 1)
        grid.attach(boilerTempValue, 1, elementIndex, 1, 1)
        elementIndex += 1

        # Distillation Tower
        distTwrValveLabel = Gtk.Label("Distillation Tower Valve")
      	distTwrValveValue = Gtk.Label()
        grid.attach(distTwrValveLabel, 0, elementIndex, 1, 1)
        grid.attach(distTwrValveValue, 1, elementIndex, 1, 1)
        elementIndex += 1

        # Process status
        processStatusLabel = Gtk.Label("Process Status")
        processStatusValue = Gtk.Label()
        grid.attach(processStatusLabel, 0, elementIndex, 1, 1)
        grid.attach(processStatusValue, 1, elementIndex, 1, 1)
        elementIndex += 1

        # Connection status
        connectionStatusLabel = Gtk.Label("Connection Status")
        connectionStatusValue = Gtk.Label()
        grid.attach(connectionStatusLabel, 0, elementIndex, 1, 1)
        grid.attach(connectionStatusValue, 1, elementIndex, 1, 1)
        elementIndex += 1

        # Run and Stop buttons
        runButton = Gtk.Button("Run")
        stopButton = Gtk.Button("Stop")

        runButton.connect("clicked", self.setProcess, 1)
        stopButton.connect("clicked", self.setProcess, 0)

        grid.attach(runButton, 0, elementIndex, 1, 1)
        grid.attach(stopButton, 1, elementIndex, 1, 1)
        elementIndex += 1

        # Oil Refienery branding
        virtualRefienery = Gtk.Label()
        virtualRefienery.set_markup("<span size='small'>Oil Refinery - HMI</span>")
        grid.attach(virtualRefienery, 0, elementIndex, 2, 1)

        # Attach Value Labels
        self.crudeOilValue = crudeOilValue
        self.boilerValveValue = boilerValveValue
        self.boilerTempValue = boilerTempValue
        self.distTwrValveValue = distTwrValveValue
        self.processStatusValue = processStatusValue
        self.connectionStatusValue = connectionStatusValue

        self.resetLabels()
        GObject.timeout_add_seconds(MODBUS_SLEEP, self.update_status)

    def setProcess(self, widget, data=None):
        try:
            self.modbusClient.write_register(0x10, data)
        except:
            pass

    def update_status(self):

        try:
            rr = self.modbusClient.read_holding_registers(1,16)
            regs = []

            if not rr or not rr.registers:
                raise ConnectionException

            regs = rr.registers

            if not regs or len(regs) < 16:
                raise ConnectionException

            if regs[1] == 1:
                self.crudeOilValue.set_markup("<span weight='bold' foreground='green'>YES</span>")
            else:
                self.crudeOilValue.set_markup("<span weight='bold' foreground='red'>NO</span>")

            if regs[0] == 1:
                self.boilerValveValue.set_markup("<span weight='bold' foreground='green'>OPEN</span>")
            else:
                self.boilerValveValue.set_markup("<span weight='bold' foreground='red'>CLOSED</span>")

            if regs[2] == 1:
                self.boilerTempValue.set_markup("<span weight='bold' foreground='green'>NORMAL</span>")
            else:
                self.boilerTempValue.set_markup("<span weight='bold' foreground='red'>HOT</span>")

            if regs[3] == 1:
                    self.distTwrValveValue.set_markup("<span weight='bold' foreground='green'>OPEN</span>")
            else:
                self.distTwrValveValue.set_markup("<span weight='bold' foreground='red'>CLOSED</span>")

            if regs[15] == 1:
                self.processStatusValue.set_markup("<span weight='bold' foreground='green'>RUNNING</span>")
            else:
                self.processStatusValue.set_markup("<span weight='bold' foreground='red'>STOPPED</span>")

            self.connectionStatusValue.set_markup("<span weight='bold' foreground='green'>ONLINE</span>")


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
