from abc import ABCMeta, abstractproperty, abstractmethod

import struct

import ability as i_ability
import algorithm as i_algorithm
import backend as i_backend
import data as i_data
import endpoint as i_endpoint


class Protocol:
    __metaclass__ = ABCMeta

    @abstractmethod
    def localSearch(self, connection, set, time):
        raise NotImplementedError()

    @abstractmethod
    def propagatingSearch(self, connection, set, depth, time):
        raise NotImplementedError()

    @abstractmethod
    def getAcceptableData(self, connection):
        raise NotImplementedError()

    @abstractmethod
    def processData(self, connection, index, input, outputs):
        raise NotImplementedError()


    @abstractmethod
    def provide(self, listener, endpoint):
        raise NotImplementedError()



class Protocol0(Protocol):


    pduHeaderStruct = struct.Struct("!3cQ")

    NOTHING = 0xFF

    VERSION_BYTE =          0xA0

    LOCAL_SEARCH =          0x00
    PROPAGATING_SEARCH =    0x01

    GET_ACCEPTABLE_DATA =   0x10
    PROCESS_DATA =          0x11

    ITEM_RESPONSE =         0x20
    SET_RESPONSE =          0x21
    ASSEMBLY_RESPONSE =     0x22

    INCOMPATIBLE_ERROR =    0x30
    UNIT_ERROR =            0x31
    DATA_ERROR =            0x32


    localSearchStruct =         struct.Struct("!")
    propagatingSearchStruct =   struct.Struct("!")

    getAcceptableDataStruct =   struct.Struct("!")
    processDataStruct =         lambda paramNum: struct.Struct("!B" + paramNum + "B")

    itemResponseStruct =        lambda paramNum: struct.Struct("!" + paramNum + "B")
    setResponseStruct =         lambda itemNum, paramNum: struct.Struct("!Q" + itemNum*paramNum + "B")
    assemblyResponseStruct =    struct.Struct("!")


    def localSearch(self, connection, set, time):
        pass

    def propagatingSearch(self, connection, set, depth, time):
        pass

    def getAcceptableData(self, connection):
        pass

    def processData(self, connection, index, input):

        dataStruct = self.processDataStruct(len(input))
        data = dataStruct.pack(index, *input)

        header = self.pduHeaderStruct.pack(self.VERSION_BYTE, self.PROCESS_DATA, self.ITEM_RESPONSE, len(data))

        connection.sendall(header)
        connection.sendall(data)

        recvHeader = connection.recv(self.pduHeaderStruct.size)
        version, unitType, requestedType, dataLen = self.pduHeaderStruct.unpack(recvHeader)
        recvData = connection.recv(dataLen)

        itemStruct = self.itemResponseStruct(dataLen)
        output = itemStruct.unpack(recvData)

        return output


    def provide(self, listener, endpoint):

        def handle(connection):
            
            recvHeader = connection.recv(self.pduHeaderStruct.size)
            version, unitType, requestedType, dataLen = self.pduHeaderStruct.unpack(recvHeader)
            recvData = connection.recv(dataLen)

            if unitType == self.PROCESS_DATA:
                dataStruct = self.processDataStruct(dataLen - 1)
                index, input = dataStruct.unpack(recvData)
                input = list(input)

                output = endpoint.processData(index, input)

                itemStruct = self.itemResponseStruct(len(output))
                data = itemStruct.pack(*output)

                header = self.pduHeaderStruct.pack(self.VERSION_BYTE, self.ITEM_RESPONSE, self.NOTHING, len(data))
                
                connection.sendall(header)
                connection.sendall(data)

        
        connection, address = listener.accept()

        endpoint.backend.asyncConnectionSafe(handle, connection)


