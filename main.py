from pysnmp.hlapi import *
from prettytable import PrettyTable
import math
import time
import csv


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0b"
    size_name = ("bps", "Kbps", "Mbps", "Gbps", "Tbps", "Pbps", "Ebps", "Zbps", "Ybps")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2) * 8
    return "%s %s" % (s, size_name[i])


class InterfaceEntry:
    def __init__(self, name: str, rxbytes: int, txbytes: int):
        self.name = name
        self.rxbytes = rxbytes
        self.txbytes = txbytes

    def __str__(self):
        return f"Name: {self.name},     TX bytes: {convert_size(self.txbytes)},      RX bytes: {convert_size(self.rxbytes)}"

    def get_name(self):
        return self.name

    def get_rxbytes(self):
        return self.rxbytes

    def get_txbytes(self):
        return self.txbytes


def gettable(oid: str, max_count: int) -> dict:
    iterator = nextCmd(
        SnmpEngine(),
        CommunityData('public', mpModel=1),
        UdpTransportTarget(('192.168.1.11', 161)),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
        lexicographicMode=False
    )

    retval = {}
    retrieved = 0
    for (errorIndication, errorStatus, errorIndex, varBinds) in iterator:
        for varBind in varBinds:
            id = int(str(varBind[0]).split(".")[-1])
            retval[id] = varBind[1]

        retrieved = retrieved + 1
        if max_count != 0 and retrieved >= max_count:
            break

    return retval


if __name__ == '__main__':
    ie = []

    file = open(f"./output_{time.time()}.csv", "w")
    writer = csv.writer(file)
    writer.writerow(["Port name", "TX (bps)", "RX (bps)", "Timestamp"])

    it = 0
    init = True
    stop = False
    while not stop:
        ts_start = time.time()
        interface_names = gettable(".1.3.6.1.4.1.14988.1.1.14.1.1.2", 0)
        interface_rx_bytes = gettable(".1.3.6.1.4.1.14988.1.1.14.1.1.31", 0)
        interface_tx_bytes = gettable(".1.3.6.1.4.1.14988.1.1.14.1.1.61", 0)

        ts_end = time.time()
        # print("Took: ", ts_end - ts_start)

        table = PrettyTable(["Port", "Tx", "Rx"])
        i = 0
        for key in interface_names:
            if key not in (0, 1, 2):
                continue

            ent = InterfaceEntry(interface_names[key], int(interface_rx_bytes[key]), int(interface_tx_bytes[key]))
            if init:
                ie.append(ent)
            else:
                tx = ent.get_txbytes() - ie[i].get_txbytes()
                rx = ent.get_rxbytes() - ie[i].get_rxbytes()
                table.add_row([ent.name, convert_size(tx), convert_size(rx)])
                writer.writerow([ent.name, tx, rx, (ts_start + ts_end) / 2])

                ie[i] = ent

            i += 1

        if not init:
            print(table)

        if (ts_end - ts_start) > 1:
            print("Requests took too long!")
        else:
            time.sleep(1 - (ts_end - ts_start))

        init = False
        it += 1
