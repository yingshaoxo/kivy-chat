from kivy.app import App
from kivy.lang import Builder
from kivy.config import Config
from kivy.uix.screenmanager import ScreenManager

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

                TextInput:
                    id: nickname
                    hint_text: "Nickname"
                    size_hint: (3.9/6.8, 1/12)
                    pos_hint: {'center_x': 0.5, 'y': 0.37}
                    background_normal: 'data/input_line.png'
                    background_active: 'data/white.png'

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

class RootWidget(ScreenManager):
    def __init__(self, **kwargs):
        super(RootWidget, self).__init__(**kwargs)


class ChatApp(App):

    def build(self):
        return RootWidget()

    def connect(self):
        self.host = self.root.ids.server.text
        self.nick = self.root.ids.nickname.text
        self.root.current = 'chatroom'

    def send_msg(self):
        msg = self.root.ids.message.text
        self.root.ids.chat_logs.text += (
            '  [b][color=2980b9]{}:[/color][/b] {}\n'
                .format(self.nick, esc_markup(msg)))
        self.root.ids.message.text = ''

    def on_stop(self):
        exit()


if __name__ == '__main__':
    Config.set('graphics', 'width', '600')
    Config.set('graphics', 'height', '900')

    ChatApp().run()
