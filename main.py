from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.config import Config
from kivy.lang import Builder  # сборка из .kv файла
import webbrowser  # Вывод вебсайта в браузер по умолчанию.
# import webview <-- Вывод вебсайта в отдельное окно
import sqlite3  # запросы к локальной базе данных учетных записей, в дальнейшем – к базе сервера
import hashlib  # хэширование паролей
import json  # парсинг json

Config.set('graphics', 'resizable', 0)
Config.set('graphics', 'width', 640)
Config.set('graphics', 'height', 480)

def setup_database():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # код ниже необходим только для создания бд на новом устройстве
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY, 
        password_hash TEXT
    )''')
    cursor.execute('''REPLACE INTO users (username, password_hash) VALUES (
        'Teacher', 
        '8ab7bbdf01a24e988c50c4cfe9557814'
    )''')
    cursor.execute('''REPLACE INTO users (username, password_hash) VALUES (
        'Student', 
        'f5c0a1c9384c2e25e79ba1abf5d9a037'
    )''')
    conn.commit()
    conn.close()

setup_database()

# главный экран, выбор вида аккаунта
class MainScreen(Screen):
    previous = 'main'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', spacing=20, padding=50)
        layout.add_widget(Label(text='Хаб', font_size=32))
        button_box = BoxLayout(orientation='horizontal', spacing=10)
        teacher_btn = Button(text='Учитель', on_press=lambda x: self.goto_next('Teacher'))
        student_btn = Button(text='Ученик', on_press=lambda x: self.goto_next('Student'))
        button_box.add_widget(teacher_btn)
        button_box.add_widget(student_btn)
        layout.add_widget(button_box)
        self.add_widget(layout)
    # переход к экрану входа
    def goto_next(self, r):
        global role
        role = r
        self.manager.transition.direction = 'left'
        self.manager.current = 'login'

# экран входа в аккаунт
class LoginScreen(Screen):
    previous = 'main'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        al = AnchorLayout()
        layout = BoxLayout(orientation='vertical', spacing=20, size_hint=(0.5, 0.5))
        self.username = TextInput(hint_text='Логин', multiline=False)
        self.password = TextInput(hint_text='Пароль', multiline=False, password=True)
        login_btn = Button(text='Войти', on_press=lambda x: self.verify_login())
        self.errlabel = Label(text='Неверные данные входа, повторите снова.', color=(1,0,0,1), opacity=0)
        layout.add_widget(self.username)
        layout.add_widget(self.password)
        layout.add_widget(login_btn)
        al.add_widget(layout)
        self.add_widget(al)
        self.add_widget(self.errlabel)
    # NOQA
    def verify_login(self):
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE username=?', (self.username.text, ))
        targethash = cursor.fetchone()
        conn.close()

        if targethash and hashlib.md5(self.password.text.encode('utf-8')).hexdigest() == targethash[0]:
            self.errlabel.opacity = 0
            self.goto_next()
        else:
            self.username.text = ''
            self.password.text = ''
            self.errlabel.opacity = 1

    def goto_next(self):
        self.manager.transition.direction = 'left'
        self.manager.get_screen('dashboard').reset()
        self.manager.current = 'dashboard'


# выбор типа ресурсов в зависимости от типа аккаунта
class DashboardScreen(Screen):
    previous = 'login'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical', spacing=20, padding=50)
        self.add_widget(self.layout)

    def reset(self):
        self.layout.clear_widgets(children=None)
        for i in resources[role]:
            bl = BoxLayout()
            btn = Button(text=f'Ресурс {i}', on_press=lambda x, idx=i: self.goto_next(idx))
            img = Image(source=resources[role][i]['Icon'], size_hint=(0.1, 1))
            bl.add_widget(img)
            bl.add_widget(btn)
            self.layout.add_widget(bl)

    def goto_next(self, idx):
        self.manager.direction = 'left'
        self.manager.get_screen('resources').reset(resource_data=resources[role][idx]['Resources'])
        self.manager.current = 'resources'


# экран с ресурсами, позволяет из приложения открыть нужный виджет
class ResourceScreen(Screen):
    previous = 'dashboard'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = ScrollView()
        self.grid = GridLayout(cols=2, spacing=10, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))

        layout.add_widget(self.grid)
        self.add_widget(layout)

    def reset(self, resource_data):
        self.grid.clear_widgets(children=None)
        for resource in resource_data:
            box = BoxLayout(orientation='vertical', size_hint_y=None, height=150)
            box.add_widget(Label(text=resource, size_hint_y=None, height=30))
            btn = Button(text='Посетить', on_press=lambda x: self.open_webview(resource_data[resource]['Link']))
            box.add_widget(btn)
            self.grid.add_widget(box)

    @staticmethod
    def open_webview(link):
        webbrowser.open(link)

# сборка приложения
class ShowCaseApp(App):
    def build(self):
        fl = FloatLayout()

        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(ResourceScreen(name=f'resources'))

        exitbtn = Button(text='Назад', size_hint=(0.1, 0.1), on_press=lambda x: self.back(sm))

        fl.add_widget(sm)
        fl.add_widget(exitbtn)
        return fl
    @staticmethod
    def back(manager):
        manager.transition.direction = 'right'
        manager.current = manager.get_screen(manager.current).previous


if __name__ == '__main__':
    role = None
    with open('resources/resources.json', 'rt') as file:
        resources = json.loads(file.read())
    ShowCaseApp().run()
