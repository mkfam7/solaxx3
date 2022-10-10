class SolaxX3G3Registers:
    __registers = {
        "battery_capacity": {
            "address": 0x01C,
            "register_type": "input",
            "data_format": "uint16",
            "data_length": 1,
            "description": "The percentage of how much the battery is charged",
        },
        "feed_in_power": {
            "address": 0x0046,
            "register_type": "input",
            "data_format": "int32",
            "data_length": 2,
            "description": "The feed-in power value obtained from Meter of CT. Generated power is represented by positive values and consumed power by negative values",
        },
    }

    def list_attributes(self):
        return list(self.__registers.keys())

class SolaxX3G4DecodeFunctions:
    __functions = {

    }

s = SolaxX3G3Registers()
print(s.list_attributes())
print(s.)