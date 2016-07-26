#!/usr/bin/env python

from gi.repository import GLib, Gtk, Gdk, GObject
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.exceptions import ConnectionException



MODBUS_SLEEP=1

class HMIWindow(Gtk.Window):
    def initModbus(self):

        self.modbusClient = ModbusClient('localhost', port=5020)

    def resetLabels(self):
        self.feed_pump_value.set_markup("<span weight='bold' foreground='gray33'>N/A</span>")
#        self.inlet_valve_value.set_markup("<span weight='bold' foreground='gray33'>N/A</span>")
        self.outlet_valve_value.set_markup("<span weight='bold' foreground='gray33'>N/A</span>")
        self.separator_value.set_markup("<span weight='bold' foreground='gray33'>N/A</span>")
#        self.discharge_pump_value.set_markup("<span weight='bold' foreground='gray33'>N/A</span>")
        self.process_status_value.set_markup("<span weight='bold' foreground='gray33'>N/A</span>")
        self.connection_status_value.set_markup("<span weight='bold' foreground='red'>OFFLINE</span>")
     
    def __init__(self):
        Gtk.Window.__init__(self, title="Oil Refinery")
        #self.gtk_widget_override_background_color(Gtk.StateType.NORMAL, Gtk.Window("green"))

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

         #Crude Oil Inlet Valve
#        inlet_valve_label = Gtk.Label("Crude Oil Tank Inlet Valve")
#        inlet_valve_value = Gtk.Label()

#        inlet_valve_open_button = Gtk.Button("OPEN")
#        inlet_valve_close_button = Gtk.Button("CLOSE")

#        inlet_valve_open_button.connect("clicked", self.setProcess, 1)
#        inlet_valve_close_button.connect("clicked", self.setProcess, 0)

#        grid.attach(inlet_valve_label, 0, elementIndex, 1, 1)
#        grid.attach(inlet_valve_value, 1, elementIndex, 1, 1)
#        grid.attach(inlet_valve_open_button, 2, elementIndex, 1, 1)
#        grid.attach(inlet_valve_close_button, 3, elementIndex, 1, 1)
#        elementIndex += 1

        # Crude Oil Outlet Valve
        outlet_valve_label = Gtk.Label("Crude Oil Tank Outlet Valve")
        outlet_valve_value = Gtk.Label()

        outlet_valve_open_button = Gtk.Button("OPEN")
        outlet_valve_close_button = Gtk.Button("CLOSE")

        outlet_valve_open_button.connect("clicked", self.setOutputValve, 1)
        outlet_valve_close_button.connect("clicked", self.setOutputValve, 0)

        grid.attach(outlet_valve_label, 0, elementIndex, 1, 1)
        grid.attach(outlet_valve_value, 1, elementIndex, 1, 1)
        grid.attach(outlet_valve_open_button, 2, elementIndex, 1, 1)
        grid.attach(outlet_valve_close_button, 3, elementIndex, 1, 1)
        elementIndex += 1

        # Crude Oil Discharge Pump
#        discharge_pump_label = Gtk.Label("Crude Oil Tank Discharge Pump")
#        discharge_pump_value = Gtk.Label()

#        discharge_pump_start_button = Gtk.Button("START")
#        discharge_pump_stop_button = Gtk.Button("STOP")

#        discharge_pump_start_button.connect("clicked", self.setProcess, 1)
#        discharge_pump_stop_button.connect("clicked", self.setProcess, 0)

#        grid.attach(discharge_pump_label, 0, elementIndex, 1, 1)
#        grid.attach(discharge_pump_value, 1, elementIndex, 1, 1)
#        grid.attach(discharge_pump_start_button, 2, elementIndex, 1, 1)
#        grid.attach(discharge_pump_stop_button, 3, elementIndex, 1, 1)
#        elementIndex += 1

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
#        self.inlet_valve_value = inlet_valve_value
        self.outlet_valve_value = outlet_valve_value
#        self.discharge_pump_value = discharge_pump_value
        self.process_status_value = process_status_value
        self.connection_status_value = connection_status_value
        self.separator_value = separator_value

        self.resetLabels()
        GObject.timeout_add_seconds(MODBUS_SLEEP, self.update_status)

    def setPump(self, widget, data=None):
        try:
            self.modbusClient.write_register(0x01, data)
        except:
            pass
        
    def setTankLevel(self, widget, data=None):
        try:
            self.modbusClient.write_register(0x02, data)
        except:
            pass
        
    def setOutputValve(self, widget, data=None):
        try:
            self.modbusClient.write_register(0x03, data)
        except:
            pass
        
    def setSepVessel(self, widget, data=None):
        try:
            self.modbusClient.write_register(0x04, data)
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

            if regs[0] == 1:
                self.feed_pump_value.set_markup("<span weight='bold' foreground='green'>RUNNING</span>")
            else:
                self.feed_pump_value.set_markup("<span weight='bold' foreground='red'>STOPPED</span>")

#            if regs[2] == 1:
#                self.inlet_valve_value.set_markup("<span> weight='bold' foreground='green'>OPEN</span>")
#            else:
#                self.inlet_valve_value.set_markup("<span> weight='bold' foreground='red'>CLOSED</span>")

            if regs[2] == 1:
                self.outlet_valve_value.set_markup("<span weight='bold' foreground='green'>OPEN</span>")
            else:
                self.outlet_valve_value.set_markup("<span weight='bold' foreground='red'>CLOSED</span>")

#           if regs[1] == 1:
#                self.discharge_pump_value.set_markup("<span weight='bold' foreground='green'>RUNNING</span>")
#            else:
#                self.discharge_pump_value.set_markup("<span weight='bold' foreground='red'>STOPPED</span>")

            if regs[3] == 1:
                self.separator_value.set_markup("<span weight='bold' foreground='green'>RUNNING</span>")
            else:
                self.separator_value.set_markup("<span weight='bold' foreground='red'>STOPPED</span>")

            if regs[3] == 1:
                self.process_status_value.set_markup("<span weight='bold' foreground='green'>RUNNING </span>")
            else:
                self.process_status_value.set_markup("<span weight='bold' foreground='red'>STOPPED </span>")

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
