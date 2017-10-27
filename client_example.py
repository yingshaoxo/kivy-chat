import asyncio
import threading

import time
from datetime import datetime


SERVER_ADDRESS = '127.0.0.1' # VPS address
PORT = 5920


class ClientProtocol(asyncio.Protocol):
    def __init__(self, control, loop):
        self.loop = loop
        self.control = control

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        text = data.decode('utf-8', 'ignore')

        if "*1*" in text:
            self.control.last_connection_time = datetime.now()
            return 

        print('Data received: {!r}'.format(text))

    def connection_lost(self, exc):
        print('The server closed the connection')
        self.transport.close()
        self.loop.stop()
        self.control.is_loop_stop = True


class ConnectionControl():
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.is_loop_stop = False
        self.is_stop = False

        try:
            self.coro = self.loop.create_connection(lambda: ClientProtocol(self, self.loop), SERVER_ADDRESS, PORT)
            self.last_connection_time = datetime.now()
            self.transport, self.protocol = self.loop.run_until_complete(self.coro)
        except:
            print("You need to make sure server is availablei.")
            exit()

        threading.Thread(target=self.receive_msg).start()
        threading.Thread(target=self.detect_if_offline).start()

    def reconnect(self):
        try:
            if self.is_loop_stop:
                self.coro = self.loop.create_connection(lambda: ClientProtocol(self, self.loop), SERVER_ADDRESS, PORT)
                self.last_connection_time = datetime.now()
                self.transport, self.protocol = self.loop.run_until_complete(self.coro)
                self.is_loop_stop = False
                return
        except Exception as e:
            print(e)
            return
        try:
            _, self.protocol = self.loop.run_until_complete(self.coro)
            self.transport.set_protocol(self.protocol)
            
            self.last_connection_time = datetime.now()
        except Exception as e:
            print(e)
            print("No server available.")

    def detect_if_offline(self): #run every 3 seconds
        while True:
            if (datetime.now() - self.last_connection_time).total_seconds() > 45:
                self.reconnect()
                print("I just reconnected the server.")
            time.sleep(3)
            if self.is_stop == True:
                return

    def receive_msg(self):
        while True:
            if self.is_loop_stop == False:
                self.loop.run_until_complete(self.coro)
            time.sleep(1)
            if self.is_stop == True:
                return

    def send_msg(self, msg):
        if self.transport != None:
            if self.transport.is_closing():
                self.reconnect()
            self.transport.write(msg.encode("utf-8"))


try:
    conn = ConnectionControl()

    while True:
        conn.send_msg(input("say something: "))
        print('You got', threading.active_count(), 'threadings.')

except KeyboardInterrupt:
    conn.is_stop = True
