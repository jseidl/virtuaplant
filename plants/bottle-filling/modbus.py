#!/usr/bin/env python

#########################################
# Imports
#########################################
# - Modbus protocol
from pymodbus.client.sync   import ModbusTcpClient
from pymodbus.server.async  import ModbusServerFactory
from pymodbus.device        import ModbusDeviceIdentification
from pymodbus.datastore     import ModbusSequentialDataBlock
from pymodbus.datastore     import ModbusSlaveContext, ModbusServerContext
from pymodbus.exceptions    import ConnectionException 
from pymodbus.transaction   import ModbusSocketFramer

#########################################
# Modbus code
#########################################
# Global Variables
MODBUS_PORT = 502

class ClientModbus(ModbusTcpClient):
    def __init__(self, address, port = MODBUS_PORT):
        ModbusTcpClient.__init__(self, address, port)

    def read(self, addr):
        regs = self.readln(addr,1)

        return regs[0]

    def readln(self, addr, size):
        rr = self.read_holding_registers(addr,size)
        regs = []

        if not rr or not rr.registers:
            raise ConnectionException

        regs = rr.registers

        if not regs or len(regs) < size:
            raise ConnectionException

        return regs

    def write(self, addr, data):
        self.write_register(addr, data)

    def writeln(self, addr, data, size):
        self.write_registers(addr, data)

class ServerModbus(ModbusServerFactory):
    def __init__(self, address, port = MODBUS_PORT):
        store = ModbusSlaveContext(
            di = ModbusSequentialDataBlock(0, [0]*100),
            co = ModbusSequentialDataBlock(0, [0]*100),
            hr = ModbusSequentialDataBlock(0, [0]*100),
            ir = ModbusSequentialDataBlock(0, [0]*100))
        
        self.context = ModbusServerContext(slaves=store, single=True)
        
        identity = ModbusDeviceIdentification()
        identity.VendorName         = 'MockPLCs'
        identity.ProductCode        = 'MP'
        identity.VendorUrl          = 'http://github.com/bashwork/pymodbus/'
        identity.ProductName        = 'MockPLC 3000'
        identity.ModelName          = 'MockPLC Ultimate'
        identity.MajorMinorRevision = '1.0'

        ModbusServerFactory.__init__(self, self.context, ModbusSocketFramer, identity)
    
    def write(self, addr, data):
        self.context[0x0].setValues(3, addr, [data])
    
    def writeln(self, addr, data, size):
        self.context[0x0].setValues(3, addr, [data])
    
    def read(self, addr):
        return self.context[0x0].getValues(3, addr, count=1)[0]

    def readln(self, addr, size):
        return self.context[0x0].getValues(3, addr, count=1)[0]

if __name__ == '__main__':
    sys.exit(main())
