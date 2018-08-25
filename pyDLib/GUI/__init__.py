"""Define shortcut for icons. IMAGES_PATH should be set to use them."""
import json
import logging
import os
import pkgutil
from typing import Union, List

from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import QToolButton, QDialog, QLayout

IMAGES_PATH = ""


CONFIGURATION_PATH =  "configuration/"

STYLE_FILES = {"MAIN_STYLE": "main_style.css","WIDGETS_STYLE": "widgets_style.css","TABS_STYLE": "tabs_style.css"}


PARAMETERS = {}


def load_options():
    bjson = pkgutil.get_data("pyDLib", "ressources/default_options.json")
    if bjson is None:
        logging.error("Default options file not found !")
        dic_default = {}
    else:
        dic_default = json.loads(bjson.decode("utf-8"))
    try:

        with open(os.path.join(CONFIGURATION_PATH,"options.json"), encoding='utf-8') as f:
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


### ------------------ Helpers ------------------ ###

class Color(QColor):

    def __init__(self, c: Union[List[int], str]) -> None:
        if type(c) is list:
            super().__init__(*c)
        else:
            super().__init__(c)


class abstractIcon(QIcon):
    IMAGE = None

    def __init__(self) -> None:
        super().__init__(os.path.join(IMAGES_PATH, self.IMAGE))


class AppIcon(abstractIcon):
    IMAGE = "app-icon.png"


class TimeIcon(abstractIcon):
    IMAGE = "historique.png"


class RefreshIcon(abstractIcon):
    IMAGE = "refresh.png"


class SaveIcon(abstractIcon):
    IMAGE = "save.png"


class SearchIcon(abstractIcon):
    IMAGE = "search.png"


class FavorisIcon(abstractIcon):
    IMAGE = "favoris.png"


class AddIcon(abstractIcon):
    IMAGE = "add.png"


class DeleteIcon(abstractIcon):
    IMAGE = "delete.png"

class ValidIcon(abstractIcon):
    IMAGE = "ok.png"


class ButtonIcon(QToolButton):

    def __init__(self,icon,tooltip: str = "") -> None:
        super().__init__()
        self.setToolTip(tooltip)
        self.setIcon(icon)


class Arrow(QIcon):

    PATH_UP = "arrow_up.png"
    PATH_DOWN = "arrow_down.png"

    def __init__(self,is_up = True):
        super().__init__(os.path.join(IMAGES_PATH, self.PATH_UP if is_up else self.PATH_DOWN))



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
