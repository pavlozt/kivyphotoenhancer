from kivy.app import App
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock, mainthread
from kivy.config import Config
from kivy.utils import platform

import threading
import time
import subprocess
import os

imagickexe = r'C:\Program Files\ImageMagick-7.0.8-Q16\magick.exe'
outputdir = 'out'


class DropFileArea(Button):
    # Специальная инциализация кнопки-области куда кидают файлы
    def __init__(self, **kwargs):
        super(DropFileArea, self).__init__(**kwargs)
        app = App.get_running_app()
        app.drops.append(self.on_dropfile)
        self.filenamelist = []

    def on_dropfile(self, widget, filename):
        if self.collide_point(*Window.mouse_pos):
            fname = filename.decode('utf-8')
            self.parent.ids['fileslist'].text += fname + "\n"
            self.filenamelist.append(fname)
            # Добавить имя файла в глобальный массив на обработку

# все окно приложения
class DropLayout(BoxLayout):
    pass

# приложение, обрабатывающее закинутые в него файлы
class ConvertApp(App):
    def build_config(self, config):
        self.drops = []
        self.files = []
        Window.bind(on_dropfile=self.handledrops)
        self.title = 'Загрузка фото заказа'
        if not os.path.exists(outputdir):
            os.mkdir(outputdir)

    def handledrops(self, *args):
        for func in self.drops:
            func(*args)

    def do_upload(self):
        print("Загрузка началась....")
        self.convert_thread = threading.Thread(target=self.convert,
                                               args=(
                                                   self.root.ids.droparea.filenamelist)
                                               )
        self.root.ids.progress.max = len(self.root.ids.droparea.filenamelist)
        self.root.ids.progress.value = 0
        self.root.ids.uploadbutton.disabled = True
        self.convert_thread.start()

    # запускается в отдельном треде, но для правильного обновления элементов интерфейса, нужно вызывать функции отдекорированные mainthread
    def convert(self, *filelist):
        print("converting filelist ", filelist)
        p = 0
        for fullname in filelist:
            # последовательный код обработки файла
            path, filename = os.path.split(fullname)
            print("Обработка ", filename)
            # запуск программы из пакета imagemagick с параметром -auto-level
            # результирующий файл записывается в каталог out
            subprocess.call([imagickexe, fullname, '-colorspace', 'Lab', '-channel', str(
                0), '-auto-level', '+channel', '-colorspace', 'sRGB', 'out/'+filename])
            p += 1
            self.update_progress(p)

        print("..закончена")
        self.root.ids.droparea.filenamelist = []
        self.unlock_upload()

    # индикатор прогресса обработки
    @mainthread
    def update_progress(self, i):
        self.root.ids.statuslabel.text = str(i)
        self.root.ids.progress.value = i

    # приведение интерфейса в исходное состояние
    @mainthread
    def unlock_upload(self):
        self.root.ids.uploadbutton.disabled = False
        self.root.ids.statuslabel.text = 'Готово'
        self.root.ids.fileslist.text = ''


# декстоп-стайл инциализация окна
if platform in ('linux', 'win', 'macosx'):
    width = 300
    Config.set('kivy', 'keyboad_mode', 'system')
    Config.set('graphics', 'desktop', '1')
    Config.set('graphics', 'resizable', 1)
    Config.set('graphics', 'width', width)
    Config.set('graphics', 'height', int(width*2.16))


if __name__ == '__main__':
    ConvertApp().run()
