import asyncio
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.config import Config
from kivy.uix.screenmanager import ScreenManager

from kivy.clock import Clock

import os
import json

Builder.load_string("""
#:import C kivy.utils.get_color_from_hex
#:import RiseInTransition kivy.uix.screenmanager.RiseInTransition

<BoxLayout>:
    padding: 10
    spacing: 10

<GridLayout>:
    rows: 2
    cols: 2
    spacing: 10
    row_default_height: 90
    row_force_default: True

<Label>:
    font_size: 25

<Button>:
    font_size: 30
    height: 90
    size_hint: (1, None)
    background_normal: 'button_normal.png'
    background_down: 'button_down.png'
    border: (2, 2, 2, 2)

<TextInput>:
    font_size: 30
    multiline: False
    padding: [10, 0.5 * (self.height - self.line_height)]

<ScrollView>:
    canvas.before:
        Color:
            rgb: 1, 1, 1
        Rectangle:
            pos: self.pos
            size: self.size

<ChatLabel@Label>:
    color: C('#101010')
    text_size: (self.width, None)
    halign: 'left'
    valign: 'top'
    padding: (-10, 0)  # fixed in Kivy 1.8.1
    size_hint: (1, None)
    height: self.texture_size[1]
    markup: True


<RootWidget>:
    transition: RiseInTransition()

    Screen:
        name: 'login'

        BoxLayout:
            orientation: 'vertical'

            GridLayout:
                Label:
                    text: 'Server:'
                    halign: 'left'
                    size_hint: (0.4, 1)

                TextInput:
                    id: server
                    text: app.host

                Label:
                    text: 'Nickname:'
                    halign: 'left'
                    size_hint: (0.4, 1)

                TextInput:
                    id: nickname
                    text: app.nick

            Button:
                text: 'Connect'
                on_press: app.connect()

    Screen:
        name: 'chatroom'

        BoxLayout:
            orientation: 'vertical'

            ScrollView:
                ChatLabel:
                    id: chat_logs
                    text: ''

            BoxLayout:
                height: 90
                orientation: 'horizontal'
                padding: 0
                size_hint: (1, None)

                TextInput:
                    id: message
                    on_text_validate: app.send_msg()

                Button:
                    text: 'Send'
                    on_press: app.send_msg()
                    size_hint: (0.3, 1)
""")
#45.63.90.169

def esc_markup(msg):
    return (msg.replace('&', '&amp;')
            .replace('[', '&bl;')
            .replace(']', '&br;'))


class ClientProtocol(asyncio.Protocol):
    def __init__(self, app, loop):
        self.app = app
        self.loop = loop

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        if data:
            text = data.decode('utf-8', 'ignore')

            if text == "*1*":
                self.app.last_connection_time = datetime.now()
                return 
            
            print(text)
            nickname = ''
            msg = ''
            for num, i in enumerate(text.split(':'), start=0):
                if num == 0:
                    nickname = i
                else:
                    msg += i
            self.app.root.ids.chat_logs.text += (
            '\t[b][color=2980b9]{}:[/color][/b] {}\n'.format(nickname, esc_markup(msg))
            )

    def connection_lost(self, exc):
        print('The server closed the connection')
        self.transport.close()


class RootWidget(ScreenManager):
    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)


class ChatApp(App):

    def build(self):
        self.base_folder =os.path.dirname(os.path.abspath('.'))
        self.setting_file = os.path.join(self.base_folder, 'chat_setting.json')
        self.read_config() 
        return RootWidget()

    def read_config(self):
        try:
            with open(self.setting_file, 'r') as f:
                text = f.read()
            self.setting_dict = json.loads(text)

            self.host = self.setting_dict['host']
            self.nick = self.setting_dict['nick']
        except:
            self.host = "127.0.0.1"
            self.nick = "kivy"

    def save_config(self):
        self.setting_dict = {'host': self.host, 'nick': self.nick}
        with open(self.setting_file, 'w') as f:
            f.write(json.dumps(self.setting_dict))

    def connect(self):
        self.host = self.root.ids.server.text
        self.nick = self.root.ids.nickname.text

        self.is_stop = False
        self.loop = asyncio.get_event_loop()

        if self.reconnect():

            self.clock_receive = Clock.schedule_interval(self.receive_msg, 1)
            self.clock_detect = Clock.schedule_interval(self.detect_if_offline, 3)

            self.root.current = 'chatroom'
            self.save_config()
            print('-- connecting to ' + self.host)

    def reconnect(self):
        try:
            self.coro = self.loop.create_connection(lambda: ClientProtocol(self, self.loop),
                          self.host, 5920)
            self.transport, self.protocol = self.loop.run_until_complete(self.coro)

            self.last_connection_time = datetime.now()
            print("I just reconnected the server.")
            return True
        except Exception as e:
            #print(e)
            self.root.current = 'login'
            try:
                self.clock_receive.cancel()
                self.clock_detect.cancel()
            except:
                print("No server available.")
            return False

    def detect_if_offline(self, dt): #run every 3 seconds
        if (datetime.now() - self.last_connection_time).total_seconds() > 45:
            self.transport.close()
            self.reconnect()

    def send_msg(self):
        if self.transport.is_closing():
            self.transport.close()
            self.reconnect()
        msg = self.root.ids.message.text
        self.transport.write('{0}:{1}'.format(self.nick, msg).encode('utf-8', 'ignore'))
        self.root.ids.chat_logs.text += (
            '\t[b][color=2980b9]{}:[/color][/b] {}\n'
                .format(self.nick, esc_markup(msg)))
        self.root.ids.message.text = ''

    def receive_msg(self, dt):
        self.loop.run_until_complete(self.coro)

    def on_stop(self):
        exit()


if __name__ == '__main__':
    Config.set('graphics', 'width', '600')
    Config.set('graphics', 'height', '900')

    ChatApp().run()
