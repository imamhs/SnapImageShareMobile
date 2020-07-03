import kivy
kivy.require('1.10.0')

from kivy.app import App
from kivy.graphics import Color, Rectangle
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition, SlideTransition
from kivy.lang import Builder

import os
import json
import requests
import pyperclip

Builder.load_string('''
[FileIconEntry@Widget]:
    locked: False
    path: ctx.path
    selected: self.path in ctx.controller().selection
    size_hint: None, None

    on_touch_down: self.collide_point(*args[1].pos) and ctx.controller().entry_touched(self, args[1])
    on_touch_up: self.collide_point(*args[1].pos) and ctx.controller().entry_released(self, args[1])
    size: '100dp', '100dp'

    canvas:
        Color:
            rgba: 1, 1, 1, 1 if self.selected else 0
        BorderImage:
            border: 8, 8, 8, 8
            pos: root.pos
            size: root.size
            source: 'atlas://data/images/defaulttheme/filechooser_selected'

    Image:
        size: '48dp', '48dp'
        source: 'atlas://data/images/defaulttheme/filechooser_%s' % ('folder' if ctx.isdir else 'file')
        pos: root.x + dp(24), root.y + dp(40)
    Label:
        text: ctx.name
        text_size: (root.width, self.height)
        halign: 'center'
        shorten: False
        color: .1, 0.1, 0.1, 1
        size: '100dp', '16dp'
        pos: root.x, root.y + dp(16)

    Label:
        text: '{}'.format(ctx.get_nice_size())
        font_size: '11sp'
        color: .7, 0.7, 0.7, 1
        size: '100dp', '16sp'
        pos: root.pos
        halign: 'center'
'''
)

class WelcomeWindow(BoxLayout):

    def __init__(self, **kwargs):
        super(WelcomeWindow, self).__init__(**kwargs)
        self.orientation='vertical'
        self.spacing = 10
        self.welcome_title = Label(text='Snap Image Share', font_size='32sp')
        self.welcome_title.size_hint = (1, 0.2)
        self.welcome_title.color = (0, 0, 0, 0.8)
        self.welcome_title.halign = 'center'
        self.add_widget(self.welcome_title)
        self.welcome_logo = Image(source='logo.png')
        self.welcome_logo.size_hint = (1, 0.1)
        self.add_widget(self.welcome_logo)
        self.welcome_features = Label(text='Share files without Sign Up\nLimit files downloads\nSafe and secure files sharing', font_size='18sp')
        self.welcome_features.size_hint = (1, 0.1)
        self.welcome_features.color = (0, 0, 0, 0.8)
        self.welcome_features.halign = 'center'
        self.welcome_features.line_height = 1.2
        self.add_widget(self.welcome_features)
        self.welcome_action = Label(text='Touch to continue', font_size='16sp')
        self.welcome_action.size_hint = (1, 0.1)
        self.welcome_action.color = (0, 0, 0, 0.5)
        self.welcome_action.halign = 'center'
        self.add_widget(self.welcome_action)
        self.bind(pos=self._update_rect, size=self._update_rect)
        with self.canvas.before:
            Color(255, 255, 255, 0.95)
            self.rect = Rectangle(size=self.size, pos=self.pos)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class MainWindowShareFile(BoxLayout):

    def __init__(self, **kwargs):
        super(MainWindowShareFile, self).__init__(**kwargs)
        self.orientation='vertical'
        self.spacing = 5
        self.padding = 2
        self.share_settings_file_title = Label(text='Browse file to share', font_size='32sp')
        self.share_settings_file_title.size_hint = (1, 0.1)
        self.share_settings_file_title.color = (0, 0, 0, 0.8)
        self.share_settings_file_title.halign = 'center'
        self.add_widget(self.share_settings_file_title)
        self.share_settings_file_filechooser = FileChooserIconView()
        self.share_settings_file_filechooser.filters = filters=['*.jpeg', '*.jpg', '*.gif', '*.png', '*.tiff', '*.svg', '*.bmp', '*.doc', '*.docx', '*.xlsx', '*.xls', '*.pptx', '*.ppt', '*.pdf', '*.odt', '*.ods', '*.odg', '*.odp', '*.csv', '*.txt']
        self.share_settings_file_filechooser.size_hint = (1, 0.8)
        self.add_widget(self.share_settings_file_filechooser)
        self.share_settings_file_upload = Button(text='Upload selected file')
        self.share_settings_file_upload.size_hint = (1, 0.1)
        self.share_settings_file_upload.background_color = (1, 0, 0, 1)
        self.share_settings_file_upload.bind(on_press=self.share_settings_file_upload_callback)
        self.add_widget(self.share_settings_file_upload)
        self.popup_message = Label(text='Please select a file to share')
        self.popup_message.halign = 'center'
        self.share_settings_file_message = Popup(title='Files browser', content=self.popup_message, auto_dismiss=True)
        self.share_settings_file_message.title_align = 'center'
        self.share_settings_file_message.size_hint = (0.8, 0.3)

    def share_settings_file_upload_callback(self, instance):
        if (len(self.share_settings_file_filechooser.selection) != 1):
            self.popup_message.text_size = (self.width * 0.6, None)
            self.popup_message.height = self.popup_message.texture_size[1]
            self.share_settings_file_message.open()
        else:
            self.parent.parent.upload_file = self.share_settings_file_filechooser.selection[0]
            self.parent.parent.current = 'upload'

class MainWindowShareLink(BoxLayout):

    def __init__(self, **kwargs):
        super(MainWindowShareLink, self).__init__(**kwargs)
        self.orientation='vertical'
        self.spacing = 20
        self.padding = 40
        self.share_settings_link__button_ns = Button(text='Share another file')
        self.share_settings_link__button_ns.size_hint = (1, 0.2)
        self.share_settings_link__button_ns.background_color = (1, 0, 0, 1)
        self.share_settings_link__button_ns.bind(on_press=self.share_settings_link__button_ns_callback)
        self.add_widget(self.share_settings_link__button_ns)
        self.share_settings_link_filler = Label()
        self.share_settings_link_filler.size_hint = (1, 0.2)
        self.add_widget(self.share_settings_link_filler)
        self.share_settings_link_title = Label(text='Get the sharing link', font_size='18sp', markup=True)
        self.share_settings_link_title.size_hint = (1, 0.2)
        self.share_settings_link_title.bold = True
        self.share_settings_link_title.color = (0, 0, 0, 0.4)
        self.share_settings_link_title.halign = 'center'
        self.add_widget(self.share_settings_link_title)
        self.share_settings_link__button_cwl = Button(text='Copy web share link')
        self.share_settings_link__button_cwl.size_hint = (1, 0.2)
        self.share_settings_link__button_cwl.background_color = (1, 0, 0, 1)
        self.share_settings_link__button_cwl.bind(on_press=self.share_settings_link__button_cwl_callback)
        self.add_widget(self.share_settings_link__button_cwl)
        self.share_settings_link__button_cmc = Button(text='Copy mobile share code')
        self.share_settings_link__button_cmc.size_hint = (1, 0.2)
        self.share_settings_link__button_cmc.background_color = (1, 0, 0, 1)
        self.share_settings_link__button_cmc.bind(on_press=self.share_settings_link__button_cmc_callback)
        self.add_widget(self.share_settings_link__button_cmc)

    #     self.bind(pos=self._update_rect, size=self._update_rect)
    #     with self.canvas.before:
    #         Color(255, 255, 255, 0.95)
    #         self.rect = Rectangle(size=self.size, pos=self.pos)
    #
    # def _update_rect(self, instance, value):
    #     self.rect.pos = instance.pos
    #     self.rect.size = instance.size

    def share_settings_link__button_cwl_callback(self, instance):
        pyperclip.copy("https://snapshare.salhosengineering.com/image.php?file=" + self.parent.parent.upload_file_share_code)

    def share_settings_link__button_cmc_callback(self, instance):
        pyperclip.copy(self.parent.parent.upload_file_share_code)

    def share_settings_link__button_ns_callback(self, instance):
        self.parent.parent.current = 'settings'

class MainWindowShareUpload(BoxLayout):

    def __init__(self, **kwargs):
        super(MainWindowShareUpload, self).__init__(**kwargs)
        self.orientation='vertical'
        self.spacing = 10
        self.share_settings_upload_title = Label(text='', font_size='14sp', markup=True)
        self.share_settings_upload_title.size_hint = (1, 1)
        self.share_settings_upload_title.color = (0, 0, 0, 0.8)
        self.share_settings_upload_title.halign = 'center'
        self.add_widget(self.share_settings_upload_title)

        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, instance, value):
        self.share_settings_upload_title.text_size = (self.width * 0.6, None)
        self.share_settings_upload_title.height = self.share_settings_upload_title.texture_size[1]

    def on_touch_down(self, touch):
        self.parent.parent.current = 'link'

class MainWindowShareSettings(BoxLayout):

    def __init__(self, **kwargs):
        super(MainWindowShareSettings, self).__init__(**kwargs)
        self.orientation='vertical'
        self.spacing = 5
        self.padding = 10
        self.share_settings_header = Label(text='Choose share settings', font_size='18sp', markup=True)
        self.share_settings_header.size_hint = (1, 0.25)
        self.share_settings_header.color = (0, 0, 0, 0.8)
        self.share_settings_header.halign = 'center'
        self.share_settings_header.bold = True
        self.add_widget(self.share_settings_header)
        self.share_settings_nod_label = Label(text='Number of downloads', font_size='14sp')
        self.share_settings_nod_label.size_hint = (1, 0.2)
        self.share_settings_nod_label.color = (0, 0, 1, 0.8)
        self.share_settings_nod_label.halign = 'center'
        self.add_widget(self.share_settings_nod_label)
        self.share_settings_nod_slider = Slider(min=1, max=1000, value=10, step=1)
        self.share_settings_nod_slider.size_hint = (1, 0.2)
        self.share_settings_nod_slider.bind(value=self.share_settings_nod_slider_callback)
        self.add_widget(self.share_settings_nod_slider)
        self.share_settings_nod_value = Label(text='10 times', font_size='14sp')
        self.share_settings_nod_value.size_hint = (1, 0.2)
        self.share_settings_nod_value.color = (0, 0, 0, 0.8)
        self.share_settings_nod_value.halign = 'center'
        self.add_widget(self.share_settings_nod_value)

        self.share_settings_et_label = Label(text='Time to expiry', font_size='14sp')
        self.share_settings_et_label.size_hint = (1, 0.2)
        self.share_settings_et_label.color = (0, 0, 1, 0.8)
        self.share_settings_et_label.halign = 'center'
        self.add_widget(self.share_settings_et_label)
        self.share_settings_et_slider = Slider(min=1, max=10080, value=30, step=1)
        self.share_settings_et_slider.size_hint = (1, 0.2)
        self.share_settings_et_slider.bind(value=self.share_settings_et_slider_callback)
        self.add_widget(self.share_settings_et_slider)
        self.share_settings_et_value = Label(text='30 minutes', font_size='14sp')
        self.share_settings_et_value.size_hint = (1, 0.2)
        self.share_settings_et_value.color = (0, 0, 0, 0.8)
        self.share_settings_et_value.halign = 'center'
        self.add_widget(self.share_settings_et_value)

        self.share_settings_file_header = Label(text='File details', font_size='18sp', markup=True)
        self.share_settings_file_header.size_hint = (1, 0.25)
        self.share_settings_file_header.color = (0, 0, 0, 0.8)
        self.share_settings_file_header.halign = 'center'
        self.share_settings_file_header.bold = True
        self.add_widget(self.share_settings_file_header)
        self.share_settings_fti = TextInput(hint_text='Enter a title for your file', multiline=False)
        self.share_settings_fti.cursor_color = (0.1, 0.1, 0.1, 1)
        self.share_settings_fti.size_hint = (1, 0.2)
        self.add_widget(self.share_settings_fti)
        self.share_settings_button_sf = Button(text='Select file')
        self.share_settings_button_sf.size_hint = (1, 0.2)
        self.share_settings_button_sf.background_color = (1, 0, 0, 1)
        self.share_settings_button_sf.bind(on_press=self.share_settings_button_sf_callback)
        self.add_widget(self.share_settings_button_sf)
        self.popup_message = Label(text='Please enter a title for your file (maximum 255 characters long)')
        self.popup_message.halign = 'center'
        self.share_settings_message = Popup(title='Share settings', content=self.popup_message, auto_dismiss=True)
        self.share_settings_message.title_align = 'center'
        self.share_settings_message.size_hint = (0.8, 0.3)

    #     self.bind(pos=self._update_rect, size=self._update_rect)
    #
    #     with self.canvas.before:
    #         Color(255, 255, 255, 0.95)
    #         self.rect = Rectangle(size=self.size, pos=self.pos)
    #
    # def _update_rect(self, instance, value):
    #     self.rect.pos = instance.pos
    #     self.rect.size = instance.size

    def share_settings_nod_slider_callback(self, instance, value):
        self.share_settings_nod_value.text = str(value) + " times"

    def share_settings_et_slider_callback(self, instance, value):

        time_m = value;

        days_value = (time_m / 60) / 24
        hr_value = (days_value % 1) * 24
        min_value = (hr_value % 1) * 60

        days_value = int(round(days_value, 3))
        hr_value = int(round(hr_value, 3))
        min_value = int(round(min_value, 3))

        time_text = ""

        if (days_value > 0):
            if (days_value > 1):
                time_text += str(days_value) + " days"
            else:
                time_text += str(days_value) + " day"

        if (hr_value > 0):
            if (days_value > 0):
                time_text += ", "
            if (hr_value > 1):
                time_text += str(hr_value) + " hours"
            else:
                time_text += str(hr_value) + " hour"

        if (min_value > 0):
            if (days_value == 0 and hr_value > 0):
                time_text += ", "
            if (days_value > 0 and hr_value == 0):
                time_text += ", "
            if (days_value > 0 and hr_value > 0):
                time_text += ", "
            if (min_value > 1):
                time_text += str(min_value) + " minutes"
            else:
                time_text += str(min_value) + " minute"

        self.share_settings_et_value.text = time_text

    def share_settings_button_sf_callback (self, instance):
        if (len(self.share_settings_fti.text) == 0 or len(self.share_settings_fti.text) > 255):
            self.popup_message.text_size = (self.width * 0.6, None)
            self.popup_message.height = self.popup_message.texture_size[1]
            self.share_settings_message.open()
        else:
            self.parent.parent.upload_file_nod = int(self.share_settings_nod_slider.value)
            self.parent.parent.upload_file_et = int(self.share_settings_et_slider.value)
            self.parent.parent.upload_file_title = str(self.share_settings_fti.text)
            self.parent.parent.current = 'file'

class MainWindowShareFileScreen(Screen):
    def __init__(self, **kwargs):
        super(MainWindowShareFileScreen, self).__init__(**kwargs)
        self.main_window_share_file = MainWindowShareFile()
        self.add_widget(self.main_window_share_file)
    def on_pre_enter(self, *args):
        self.main_window_share_file.share_settings_file_filechooser.path = "/"
        self.main_window_share_file.share_settings_file_filechooser.selection = []

class MainWindowShareLinkScreen(Screen):
    def __init__(self, **kwargs):
        super(MainWindowShareLinkScreen, self).__init__(**kwargs)
        self.main_window_share_link = MainWindowShareLink()
        self.add_widget(self.main_window_share_link)

class MainWindowShareUploadScreen(Screen):
    def __init__(self, **kwargs):
        super(MainWindowShareUploadScreen, self).__init__(**kwargs)
        self.main_window_share_upload = MainWindowShareUpload()
        self.add_widget(self.main_window_share_upload)
    def on_enter(self, *args):
        #self.main_window_share_upload.share_settings_upload_title.text = ''
        server_url = 'https://snapshare.salhosengineering.com/shareimage_upload_image.php'
        file_data = {'image_data': (os.path.basename(str(self.parent.upload_file)), open(str(self.parent.upload_file), 'rb'))}
        file_share_info = {'title': str(self.parent.upload_file_title), 'number_of_downloads': str(self.parent.upload_file_nod), 'availability': str(self.parent.upload_file_et)}
        r = requests.post(server_url, files=file_data, data=file_share_info)
        if(len(r.text) > 0):
            server_reply = r.text.split('.')
            if (int(server_reply[0]) == 0):
                self.main_window_share_upload.share_settings_upload_title.text = str(server_reply[1])
                self.parent.upload_file_share_code = str(server_reply[2])
            else:
                self.main_window_share_upload.share_settings_upload_title.text = str(server_reply[1])
    def on_pre_enter(self, *args):
        self.main_window_share_upload.share_settings_upload_title.text = 'The file is being uploaded to the cloud ...'

class MainWindowShareSettingsScreen(Screen):
    def __init__(self, **kwargs):
        super(MainWindowShareSettingsScreen, self).__init__(**kwargs)
        self.main_window_share_settings = MainWindowShareSettings()
        self.add_widget(self.main_window_share_settings)
    def on_pre_enter(self, *args):
        self.main_window_share_settings.share_settings_fti.text = ""
        self.main_window_share_settings.share_settings_nod_slider.value = 10
        self.main_window_share_settings.share_settings_et_slider.value = 30

class MainWindowShareContents(BoxLayout):

    def __init__(self, **kwargs):
        super(MainWindowShareContents, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.upload_file = ""
        self.upload_file_title = ""
        self.upload_file_nod = 0
        self.upload_file_et = 0
        self.upload_file_share_code = ""
        self.share_windows = ScreenManager(transition=SlideTransition(direction='left'))
        self.share_windows.add_widget(MainWindowShareSettingsScreen(name='settings'))
        self.share_windows.add_widget(MainWindowShareFileScreen(name='file'))
        self.share_windows.add_widget(MainWindowShareUploadScreen(name='upload'))
        self.share_windows.add_widget(MainWindowShareLinkScreen(name='link'))
        self.add_widget(self.share_windows)

        self.bind(pos=self._update_rect, size=self._update_rect)

        with self.canvas.before:
            self.rect = Rectangle(source='back.png', size=self.size, pos=self.pos)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class MainWindowDownloadContents(BoxLayout):

    def __init__(self, **kwargs):
        super(MainWindowDownloadContents, self).__init__(**kwargs)
        self.orientation='vertical'
        self.spacing = 10
        self.sis_title = Label(text='Snap Image Share Download', font_size='32sp')
        self.sis_title.size_hint = (1, 0.2)
        self.sis_title.color = (0, 0, 0, 0.8)
        self.sis_title.halign = 'center'
        self.add_widget(self.sis_title)
        self.bind(pos=self._update_rect, size=self._update_rect)
        with self.canvas.before:
            Color(255, 255, 255, 0.95)
            self.rect = Rectangle(size=self.size, pos=self.pos)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class MainWindowAboutContents(BoxLayout):

    def __init__(self, **kwargs):
        super(MainWindowAboutContents, self).__init__(**kwargs)
        self.orientation='vertical'
        self.spacing = 20
        self.padding = 10
        self.main_window_about_about = Label(text='Snap Image Share is a secure file sharing service provided by SALHOS Engineering for easy file sharing', font_size='14sp', markup=True)
        self.main_window_about_about.size_hint = (1, 0.2)
        self.main_window_about_about.color = (0, 0, 0, 0.9)
        self.main_window_about_about.halign = 'center'
        self.add_widget(self.main_window_about_about)

        self.main_window_about_license = Label(text='File hosting online service provided by Snap Image Share is provided for use “as is” and is without warranty of any kind, express or implied, including but not limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. In no event shall Snap Image Share be liable to any party for any direct or indirect damages.', font_size='12sp', markup=True)
        self.main_window_about_license.size_hint = (1, 0.2)
        self.main_window_about_license.color = (0, 0, 0, 0.6)
        self.main_window_about_license.halign = 'center'
        self.add_widget(self.main_window_about_license)

        self.main_window_about_contact = Label(text='Please use salhosengineering@gmail.com to reach out to us.', font_size='12sp', markup=True)
        self.main_window_about_contact.size_hint = (1, 0.2)
        self.main_window_about_contact.color = (0, 0, 0, 0.6)
        self.main_window_about_contact.halign = 'center'
        self.add_widget(self.main_window_about_contact)

        self.bind(pos=self._update_rect, size=self._update_rect)
        with self.canvas.before:
            Color(255, 255, 255, 0.95)
            self.rect = Rectangle(size=self.size, pos=self.pos)

    def _update_rect(self, instance, value):
        self.main_window_about_about.text_size = (self.width * 0.6, None)
        self.main_window_about_about.height = self.main_window_about_about.texture_size[1]
        self.main_window_about_license.text_size = (self.width * 0.6, None)
        self.main_window_about_license.height = self.main_window_about_license.texture_size[1]
        self.main_window_about_contact.text_size = (self.width * 0.6, None)
        self.main_window_about_contact.height = self.main_window_about_contact.texture_size[1]
        self.rect.pos = instance.pos
        self.rect.size = instance.size

class MainWindow(TabbedPanel):

    def __init__(self, **kwargs):
        super(MainWindow, self).__init__(**kwargs)
        self.default_tab_text = 'Share'
        self.main_window_share_contents = MainWindowShareContents()
        self.default_tab_content = self.main_window_share_contents
        self.main_window_download_contents = MainWindowDownloadContents()
        self.download_tab = TabbedPanelHeader(text='Download')
        self.download_tab.content = self.main_window_download_contents
        self.add_widget(self.download_tab)
        self.main_window_about_contents = MainWindowAboutContents()
        self.about_tab = TabbedPanelHeader(text='About')
        self.about_tab.content = self.main_window_about_contents
        self.add_widget(self.about_tab)
        #self.background_color = (255, 255, 255, 0.95)

class WelcomeScreen(Screen):

    def __init__(self, **kwargs):
        super(WelcomeScreen, self).__init__(**kwargs)
        self.welcome_window = WelcomeWindow()
        self.add_widget(self.welcome_window)

    def on_touch_down(self, touch):
        self.parent.current = 'main'

class MainScreen(Screen):

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.main_window = MainWindow()
        self.add_widget(self.main_window)

class SnapImageShare(App):

    def build(self):
        self.title = "Snap Image Share"
        self.icon = 'logo.png'

        self.windows = ScreenManager(transition=FadeTransition())
        self.windows.add_widget(WelcomeScreen(name='welcome'))
        self.windows.add_widget(MainScreen(name='main'))
        self.root = self.windows

if __name__ == '__main__':
    SnapImageShare().run()