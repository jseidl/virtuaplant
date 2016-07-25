#!/usr/bin/env python

from gi.repository import GLib, Gtk, GObject
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.exceptions import ConnectionException

MODBUS_SLEEP=1

class HMIWindow(Gtk.Window):

    def initModbus(self):

        self.modbusClient = ModbusClient('localhost', port=5020)

    def resetLabels(self):
        self.bottlePositionValue.set_markup("<span weight='bold' foreground='gray33'>N/A</span>")
        self.motorStatusValue.set_markup("<span weight='bold' foreground='gray33'>N/A</span>")
        self.levelHitValue.set_markup("<span weight='bold' foreground='gray33'>N/A</span>")
        self.processStatusValue.set_markup("<span weight='bold' foreground='gray33'>N/A</span>")
        self.nozzleStatusValue.set_markup("<span weight='bold' foreground='gray33'>N/A</span>")
        self.connectionStatusValue.set_markup("<span weight='bold' foreground='red'>OFFLINE</span>")

    def __init__(self):
        Gtk.Window.__init__(self, title="Bottle-filling factory - HMI - VirtuaPlant")

        self.set_border_width(20)
        
        self.initModbus()

        elementIndex = 0

        # Grid
        grid = Gtk.Grid()
        grid.set_row_spacing(15)
        grid.set_column_spacing(10)
        self.add(grid)

        # Main title label
        label = Gtk.Label()
        label.set_markup("<span weight='bold' size='x-large'>Bottle-filling process status</span>")
        grid.attach(label, 0, elementIndex, 2, 1)
        elementIndex += 1

        # Bottle in position label
        bottlePositionLabel = Gtk.Label("Bottle in position")
        bottlePositionValue = Gtk.Label()
        grid.attach(bottlePositionLabel, 0, elementIndex, 1, 1)
        grid.attach(bottlePositionValue, 1, elementIndex, 1, 1)
        elementIndex += 1

        # Nozzle status label
        nozzleStatusLabel = Gtk.Label("Nozzle Status")
        nozzleStatusValue = Gtk.Label()
        grid.attach(nozzleStatusLabel, 0, elementIndex, 1, 1)
        grid.attach(nozzleStatusValue, 1, elementIndex, 1, 1)
        elementIndex += 1

        # Motor status label
        motorStatusLabel = Gtk.Label("Motor Status")
        motorStatusValue = Gtk.Label()
        grid.attach(motorStatusLabel, 0, elementIndex, 1, 1)
        grid.attach(motorStatusValue, 1, elementIndex, 1, 1)
        elementIndex += 1

        # Level hit label
        levelHitLabel = Gtk.Label("Level Hit")
        levelHitValue = Gtk.Label()
        grid.attach(levelHitLabel, 0, elementIndex, 1, 1)
        grid.attach(levelHitValue, 1, elementIndex, 1, 1)
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

        # VirtuaPlant branding
        virtuaPlant = Gtk.Label()
        virtuaPlant.set_markup("<span size='small'>VirtuaPlant - HMI</span>")
        grid.attach(virtuaPlant, 0, elementIndex, 2, 1)

        # Attach Value Labels
        self.processStatusValue = processStatusValue
        self.connectionStatusValue = connectionStatusValue
        self.levelHitValue = levelHitValue
        self.motorStatusValue = motorStatusValue
        self.bottlePositionValue = bottlePositionValue
        self.nozzleStatusValue = nozzleStatusValue

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
                self.bottlePositionValue.set_markup("<span weight='bold' foreground='green'>YES</span>")
            else:
                self.bottlePositionValue.set_markup("<span weight='bold' foreground='red'>NO</span>")

            if regs[0] == 1:
                self.levelHitValue.set_markup("<span weight='bold' foreground='green'>YES</span>")
            else:
                self.levelHitValue.set_markup("<span weight='bold' foreground='red'>NO</span>")

            if regs[2] == 1:
                self.motorStatusValue.set_markup("<span weight='bold' foreground='green'>ON</span>")
            else:
                self.motorStatusValue.set_markup("<span weight='bold' foreground='red'>OFF</span>")

            if regs[3] == 1:
                    self.nozzleStatusValue.set_markup("<span weight='bold' foreground='green'>OPEN</span>")
            else:
                self.nozzleStatusValue.set_markup("<span weight='bold' foreground='red'>CLOSED</span>")

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