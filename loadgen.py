import asyncio
import os
import random
import struct

# Tuneables
NUM_LISTENERS = 5
NUM_BEACONS = 5
MAX_PPS = 100 # Max packets per second
PORT = int(os.environ['C3LD_ENV_PORT'])
HOST = os.environ['C3LD_PORT_'+str(PORT)+'_UDP_ADDR']
MAX_INFLIGHT = 10

# Global State
LISTENERS = []
LISTENER_DATA = {}
BEACONS = []
BEACON_DATA = {}
INFLIGHT_SEMA = asyncio.Semaphore(MAX_INFLIGHT)

def gen_beacon():
    mac = b''.join([struct.pack('B',random.randrange(255)) for i in range(6)])
    data = b''.join([struct.pack('B', random.randrange(255)) for i in range(16)])
    data += struct.pack('H', random.randrange(65536))
    data += struct.pack('H', random.randrange(65536))
    data += struct.pack('B', random.randrange(255))
    return (mac, data)

def gen_listener():
    mac = b''.join([struct.pack('B',random.randrange(255)) for i in range(6)])
    return mac

def init_state():
    for i in range(NUM_LISTENERS):
        LISTENERS.append(gen_listener())
    for i in range(NUM_BEACONS):
        mac, data = gen_beacon()
        BEACONS.append(mac)
        BEACON_DATA[mac] = data

def gen_packet():
    listener_mac = random.choice(LISTENERS)
    beacon_mac = random.choice(BEACONS)
    data = BEACON_DATA[beacon_mac]
    rssi = random.randrange(255)
    packet = b'\x02\x01\x1a\xff\x4c\x00\x02'
    packet += data
    return packet

class C3ldClientProtocol:
    def __init__(self):
        self.message = gen_packet()
        self.loop = asyncio.get_event_loop()
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        print('Send:', self.message)
        self.transport.sendto(self.message)

    def datagram_received(self, data, addr):
        print("Received:", data)

        print("Close the socket")
        self.transport.close()

    def error_received(self, exc):
        print('Error received:', exc)

    def connection_lost(self, exc):
        self.transport.close()

@asyncio.coroutine
def g():
    print("Started g")
    while True:
        with (yield from INFLIGHT_SEMA):
            yield from asyncio.sleep(1/MAX_PPS)
            asyncio.Task(start_fire())
            
def start_fire():
    return loop.create_datagram_endpoint(
        C3ldClientProtocol,
        remote_addr=(HOST, PORT))

if __name__ == "__main__":
    init_state()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.Task(g()))

