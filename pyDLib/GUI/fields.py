"""Implements widgets to visualize and modify basic fields. (french language)"""
import re

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QPushButton, QLineEdit

from . import list_views, clear_layout, ValidIcon

#TODO add basic fields


class abstractNewButton(QFrame):
    data_changed = pyqtSignal(object)
    LABEL = "Add"

    def __init__(self, is_editable):
        super().__init__()
        self.is_editable = is_editable
        self.setLayout(QHBoxLayout())
        self.set_button()

    def set_button(self):
        b = QPushButton(self.LABEL)
        b.clicked.connect(self.enter_edit)
        b.setEnabled(self.is_editable)
        self.layout().addWidget(b)

    def enter_edit(self):
        pass


class NouveauTelephone(abstractNewButton):
    LABEL = "Ajouter un numéro"

    @staticmethod
    def IS_TELEPHONE(s):
        r = '[0-9]{10}'
        m = re.search(r,s.replace(' ', ''))
        return m is not None


    def _clear(self):
        clear_layout(self.layout())


    def enter_edit(self):
        self.clear()
        line_layout = self.layout()
        self.entree = QLineEdit()
        self.entree.setObjectName("nouveau-numero-tel")
        self.entree.setAlignment(Qt.AlignCenter)
        self.entree.setPlaceholderText("Ajouter...")
        add = QPushButton()
        add.setIcon(ValidIcon())
        add.clicked.connect(self.on_add)
        self.entree.editingFinished.connect(self.on_add)
        line_layout.addWidget(self.entree)
        line_layout.addWidget(add)
        line_layout.setStretch(0, 3)
        line_layout.setStretch(1, 1)

    def on_add(self):
        self.entree.clear()
        num = self.entree.text()
        if self.IS_TELEPHONE(num):
            self.entree.setPlaceholderText("Ajouter...")
            self.data_changed.emit(num)
            self.set_button()
        else:
            self.entree.setPlaceholderText("Numéro invalide")


class Tels(list_views.abstractMutableList):

    LIST_PLACEHOLDER = "Aucun numéro."
    LIST_HEADER = None

    BOUTON_NOUVEAU = NouveauTelephone



