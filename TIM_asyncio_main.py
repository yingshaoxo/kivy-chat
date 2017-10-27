import asyncio
from datetime import datetime

from kivy.app import App
from kivy.lang import Builder
from kivy.config import Config
from kivy.uix.screenmanager import ScreenManager

from kivy.clock import Clock
from kivy.core.clipboard import Clipboard

import os
import json


PORT = 5920


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
    font_name:'data/droid.ttf'

<Button>:
    font_size: 30
    height: 90
    size_hint: (1, None)
    background_normal: 'data/button_normal.png'
    background_down: 'data/button_down.png'
    border: (2, 2, 2, 2)

<TextInput>:
    font_size: 30
    multiline: False
    padding: [10, 0.5 * (self.height - self.line_height)]
    font_name:'data/droid.ttf'

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
    padding: (0, 0)  # fixed in Kivy 1.8.1
    size_hint: (1, None)
    height: self.texture_size[1]
    markup: True


<RootWidget>:
    transition: RiseInTransition()

    Screen:
        name: 'login'

        BoxLayout:
            orientation: 'vertical'

            canvas.before:
                Color:
                    rgba: 1, 1, 1, 1
                Rectangle:
                    pos: self.pos
                    size: self.size
                    source: "data/background.png"

            FloatLayout:
                canvas:
                    Color:
                        rgb: 1, 1, 1
                    Ellipse:
                        id: user_picture
                        pos: root.width/2 - 150/2, self.height/2 - 150/2 + 150*1.5
                        size: 150, 150
                        source: 'data/yingshaoxo.png'
                        angle_start: 0
                        angle_end: 360
                    Line:
                        width: 2
                        ellipse: (root.width/2 - 158/2, self.height/2 - 158/2 + 150*1.5, 158, 158, 0, 360)

                TextInput:
                    id: server
                    hint_text: "Server IP"
                    size_hint: (3.9/6.8, 1/12)
                    pos_hint: {'center_x': 0.5, 'y': 0.47}
                    background_normal: 'data/input_line.png'
                    background_active: 'data/white.png'
                    text: app.host

                TextInput:
                    id: nickname
                    hint_text: "Nickname"
                    size_hint: (3.9/6.8, 1/12)
                    pos_hint: {'center_x': 0.5, 'y': 0.37}
                    background_normal: 'data/input_line.png'
                    background_active: 'data/white.png'
                    text: app.nick

                Button:
                    text: 'Connect'
                    on_press: app.connect()
                    size_hint: (4/6.8, 1/12)
                    pos_hint: {'center_x': 0.5, 'y': 0.22}

    Screen:
        name: 'chatroom'

        BoxLayout:
            orientation: 'vertical'

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

            ScrollView:
                ChatLabel:
                    id: chat_logs
                    text: ''
""")


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
            '[b][color=2980b9]{}:[/color][/b] {}\n'.format(nickname, esc_markup(msg))
            )

            Clipboard.copy(msg)

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
                          self.host, PORT)
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
            '[b][color=2980b9]{}:[/color][/b] {}\n'
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
