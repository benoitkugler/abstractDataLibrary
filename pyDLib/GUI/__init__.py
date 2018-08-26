"""Define shortcut for icons. PARAMETERS["IMAGES_PATH"] should be set to use them."""
import json
import logging
import os
import pkgutil
from typing import Union, List

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor, QIcon, QPixmap
from PyQt5.QtWidgets import QToolButton, QLayout, QGraphicsOpacityEffect, QApplication

CONFIGURATION_PATH =  "configuration/"

STYLE_FILES = {"MAIN_STYLE": "main_style.css", "WIDGETS_STYLE": "widgets_style.css"}


PARAMETERS = {}


def load_options():
    bjson = pkgutil.get_data("pyDLib", "ressources/default_GUI_options.json")
    if bjson is None:
        logging.error("Default options file not found !")
        dic_default = {}
    else:
        dic_default = json.loads(bjson.decode("utf-8"))

    try:

        with open(os.path.join(CONFIGURATION_PATH,"GUI_options.json"), encoding='utf-8') as f:
            dic = json.load(f)
    except FileNotFoundError:
        logging.warning("No options file found !")
        dic = {}
    except json.JSONDecodeError:
        logging.warning("Invalid options file !")
        dic = {}
    PARAMETERS["OPTIONS"] = dict(dic_default,**dic)

    for name, file in STYLE_FILES.items():
        style = pkgutil.get_data("pyDLib", "ressources/default_" + file)
        if style is None:
            logging.error(f"Default style sheet {name} not found !")
            style = ""
        else:
            style = style.decode("utf-8")
        try:
            with open(os.path.join(CONFIGURATION_PATH,file),encoding="utf-8") as f:
                style_add = f.read()
        except FileNotFoundError:
            logging.warning(f"No style sheet found for {name} !")
            style_add = ""
        PARAMETERS[name] = style + "\n" + style_add


def _pixmap_from_ressource(name):
    b = pkgutil.get_data("pyDLib", os.path.join("ressources/images", name))
    pixmap = QPixmap()
    pixmap.loadFromData(b)
    return pixmap


class Icons:
    Time = "historique.png"
    Refresh = "refresh.png"
    Save = "save.png"
    Search = "search.png"
    Favoris = "favoris.png"
    Add = "add.png"
    Delete = "delete.png"
    Valid = "ok.png"
    Default = "default.png"
    Back = "back.png"
    ArrowUp = "arrow_up.png"
    ArrowDown = "arrow_down.png"

    @classmethod
    def load_icons(cls):
        for name in ["Time", "Refresh", "Save", "Search", "Favoris", "Add",
                     "Delete", "Valid", "Default", "Back", "ArrowUp", "ArrowDown"]:
            val = _pixmap_from_ressource(getattr(cls, name))
            setattr(cls, name, val)



### ------------------ Helpers ------------------ ###

class Color(QColor):

    def __init__(self, c: Union[List[int], str]) -> None:
        if type(c) is list:
            super().__init__(*c)
        else:
            super().__init__(c)


class AppIcon(QIcon):
    IMAGE = "app-icon.png"

    def __init__(self):
        path = os.path.abspath(os.path.join(PARAMETERS["IMAGES_PATH"], self.IMAGE))
        super(AppIcon, self).__init__(path)


class ButtonIcon(QToolButton):

    def __init__(self,icon,tooltip: str = "") -> None:
        super().__init__()
        self.setToolTip(tooltip)
        self.setIcon(QIcon(icon))


class UserAvatar(QPixmap):
    IMAGE = "user.png"

    def __init__(self):
        super(UserAvatar, self).__init__(_pixmap_from_ressource(self.IMAGE))


class SuperUserAvatar(UserAvatar):
    IMAGE = "user-super.png"


### ------------------- Misc ------------------- ###
def clear_layout(layout: QLayout) -> None:
    """Clear the layout off all its components"""
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                clear_layout(item.layout())


class MakeLoader(QGraphicsOpacityEffect):
    MIN = 40
    MAX = 100
    PAS = 4

    def __init__(self, widget):
        super().__init__()
        self.i = self.MAX
        self.sens = False
        self.widget = widget
        widget.setGraphicsEffect(self)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_opacity)

    def set_opacity(self, i):
        self.setOpacity(float(i) / 100)
        self.update()
        QApplication.processEvents()

    def update_opacity(self):
        self.set_opacity(self.i)
        if self.i >= self.MAX:
            self.i, self.sens = self.MAX - self.PAS, False
        elif self.i <= self.MIN:
            self.i, self.sens = self.MIN + self.PAS, True
        elif self.sens:
            self.i += self.PAS
        else:
            self.i -= self.PAS

    def stop(self):
        self.timer.stop()
        self.set_opacity(100)
        self.setEnabled(False)

    def start(self):
        self.timer.start(50)
