import logging

from PyQt5.QtWidgets import QFrame, QStatusBar

from pyDLib.GUI import fenetres
from ..Core import controller


class abstractModule(QFrame):
    status_bar: QStatusBar
    interface: controller.abstractInterface

    def __init__(self, status_bar, interface):
        super().__init__()
        self.status_bar = status_bar
        self.interface = interface

        # Convenient callbacks
        def on_error(s, wait=False):
            logging.error(s)
            fenetres.WarningBox(s)

        def on_done(l, wait=False):
            logging.debug(l)
            if wait:
                self.status_bar.showMessage(str(l))
            else:
                self.status_bar.showMessage(str(l), 3000)

        self._set_erreur_reussite(on_error, on_done)

    def _set_erreur_reussite(self, sortie_erreur_GUI, sortie_standard_GUI):
        """sortie_erreur_GUI: Called on error (argument: str) ;
        sortie_standard_GUI: Called on succes (argument: str)"""
        self.interface.sortie_erreur_GUI = sortie_erreur_GUI
        self.interface.sortie_standard_GUI = sortie_standard_GUI

    def set_callbacks(self, **dic_functions):
        """Register callbacks needed by the interface object"""
        for action in self.interface.CALLBACKS:
            try:
                f = dic_functions[action]
            except KeyError:
                pass
            else:
                setattr(self.interface.callbacks, action, f)
        manquantes = [a for a in self.interface.CALLBACKS if not a in dic_functions]
        if not manquantes:
            logging.debug(f"{self.__class__.__name__} : Tous les callbacks demandés sont fournis.")
        else:
            logging.warning(f"{self.__class__.__name__} didn't set asked callbacks {manquantes}")
