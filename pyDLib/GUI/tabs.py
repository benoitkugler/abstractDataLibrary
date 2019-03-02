import logging

from PyQt5.QtCore import pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QFrame, QStatusBar

from pyDLib.GUI import fenetres
from ..Core import controller


class abstractModule(QFrame):
    popup_asked = pyqtSignal(str, object)
    """Asks for bottom right popup displaying given string, title (maybe none)"""

    status_bar: QStatusBar

    def __init__(self, status_bar, interface):
        super().__init__()
        self.status_bar = status_bar
        self.interface = interface

        def on_error(s, wait=False):
            logging.error(s)
            fenetres.WarningBox(s)

        def on_done(l, wait=False):
            logging.debug(l)
            if wait:
                self.status_bar.showMessage(str(l))
            else:
                self.status_bar.showMessage(str(l), 3000)

        self.interface.sortie_erreur_GUI = on_error
        self.interface.sortie_standard_GUI = on_done
        self.interface.callbacks.show_local_file = self.show_local_file

    def set_callbacks(self, **dic_functions):
        """Register callbacks needed by the interface object"""
        for action in self.interface.CALLBACKS:
            try:
                f = dic_functions[action]
            except KeyError:
                pass
            else:
                setattr(self.interface.callbacks, action, f)
        manquantes = [
            a for a in self.interface.CALLBACKS if not a in dic_functions]
        if not manquantes:
            logging.debug(
                f"{self.__class__.__name__} : Tous les callbacks demandés sont fournis.")
        else:
            logging.warning(
                f"{self.__class__.__name__} didn't set asked callbacks {manquantes}")

    def show_local_file(self, filepath):
        QDesktopServices.openUrl(QUrl.fromLocalFile(filepath))
