#!/usr/bin/env python

#########################################
# Imports
#########################################
# - Modbus protocol
import  time
from pymodbus.client.sync   import ModbusTcpClient
from pymodbus.server.async  import ModbusServerFactory
from pymodbus.device        import ModbusDeviceIdentification
from pymodbus.datastore     import ModbusSequentialDataBlock
from pymodbus.datastore     import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction   import ModbusSocketFramer

#########################################
# Modbus code
#########################################
# Global Variables
MODBUS_PORT = 502

class ClientModbus(ModbusTcpClient):
    def __init__(self, address, port = MODBUS_PORT):
        super(ClientModbus, self).__init__(address, port)

    def read(self, addr):
        return self.read_holding_registers(addr,17)

    def write(self, addr, data):
        self.write_register(addr, data)

class ServerModbus:
    def __init__(self, reactor, address, port = MODBUS_PORT):
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

        framer  = ModbusSocketFramer
        factory = ModbusServerFactory(self.context, framer, identity)
    
        reactor.listenTCP(port, factory, interface = address)
    
    def write(self, addr, data):
        self.context[0x0].setValues(3, addr, [data])
    
    def read(self, addr):
        return self.context[0x0].getValues(3, addr, count=1)[0]

if __name__ == '__main__':
    sys.exit(main())
