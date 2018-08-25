"""Implements widgets to visualize and modify basic fields. (french language)"""
import datetime
import re

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QPushButton, QLineEdit, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, \
    QCheckBox, QCompleter, QGridLayout, QVBoxLayout

from . import list_views, clear_layout, ValidIcon
from ..Core import formats



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




class Duree(QLabel):
    """Display the numbers of day between two date widgets.
    These widgets have to implement a get_data method, which return a date.date"""

    def __init__(self, begining, end):
        super().__init__()
        self.begining = begining
        self.end = end
        self.begining.data_changed.connect(self.set_data)
        self.end.data_changed.connect(self.set_data)
        self.set_data()

    def set_data(self, *args):
        """we cant to call set_data to manually update"""
        db = self.begining.get_data() or formats.DATE_DEFAULT
        df = self.end.get_data() or formats.DATE_DEFAULT
        jours = max((df - db).days + 1, 0)
        self.setText(str(jours) + (jours >= 2 and " jours" or " jour"))





class abstractEnum(QLabel):

    VALUE_TO_LABEL = None
    """Dict. giving label from raw value"""

    DEFAULT_VALUE = None
    """Default raw value"""

    def set_data(self, value):
        self.value = value
        value = value or self.DEFAULT_VALUE
        self.setText(self.VALUE_TO_LABEL[value])

    def get_data(self):
        return self.value


class abstractEnumEditable(QComboBox):
    data_changed = pyqtSignal(object)

    VALEURS_LABELS = None
    """List of tuples (value, label) or None to add a separator"""

    DEFAULT_VALUE = None
    """Default raw value"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.set_choix(self.VALEURS_LABELS)
        self.currentIndexChanged.connect(lambda i: self.data_changed.emit(self.currentData()))

    def set_choix(self, choix):
        self.places = {}
        for t in choix:
            if t:
                self.places[t[0]] = self.count()
                self.addItem(t[1], userData=t[0])
            else:
                self.insertSeparator(self.count())

    def set_data(self, value):
        value = value or self.DEFAULT_VALUE
        self.setCurrentIndex(self.places[value])

    def get_data(self):
        return self.currentData()



class abstractSimpleField(QLabel):
    FONCTION_AFF = None

    def set_data(self, value):
        self.value = value
        label = self.FONCTION_AFF(value)
        self.setText(label)

    def get_data(self):
        return self.value


class BoolFixe(abstractSimpleField):
    FONCTION_AFF = staticmethod(formats.abstractRender.boolen)


class EurosFixe(abstractSimpleField):
    FONCTION_AFF = staticmethod(formats.abstractRender.euros)


class PourcentFixe(abstractSimpleField):
    FONCTION_AFF = staticmethod(formats.abstractRender.pourcent)


class DefaultFixe(abstractSimpleField):
    FONCTION_AFF = staticmethod(formats.abstractRender.default)


class DateFixe(abstractSimpleField):
    FONCTION_AFF = staticmethod(formats.abstractRender.date)



class abstractEntierEditable(QSpinBox):
    UNITE = ""
    MAX = None
    MIN = 0
    DEFAULT = 0
    data_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximum(self.MAX)
        self.setMinimum(self.MIN)
        self.setSuffix(self.UNITE)
        self.valueChanged.connect(self.data_changed.emit)

    def set_data(self, somme):
        somme = somme if somme is not None else self.DEFAULT
        self.setValue(somme)

    def get_data(self):
        return self.value()


class EntierEditable(abstractEntierEditable):
    MAX = 10000


class PourcentEditable(abstractEntierEditable):
    UNITE = "%"
    MAX = 100
    DEFAULT = 0


class EurosEditable(QDoubleSpinBox):
    data_changed = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximum(100000)
        self.setSuffix("€")
        self.valueChanged.connect(self.data_changed.emit)

    def set_data(self, somme):
        somme = somme or 0
        self.setValue(somme)

    def get_data(self):
        return self.value()


class BoolEditable(QFrame):
    data_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        cb = QCheckBox()
        l = QLabel()
        self.setAutoFillBackground(True)  # Pour éviter la transparence
        layout = QHBoxLayout(self)
        layout.addWidget(cb)
        layout.addWidget(l)

        def callback(b):
            l.setText(b and "Oui" or "Non")
            self.data_changed.emit(b)

        cb.clicked.connect(callback)
        self.cb = cb
        self.l = l

    def set_data(self, b):
        b = b or False
        self.cb.setChecked(b)
        self.l.setText(b and "Oui" or "Non")

    def get_data(self):
        return self.cb.isChecked()


class DefaultEditable(QLineEdit):
    data_changed = pyqtSignal(str)

    def __init__(self, parent=None, completion=[]):
        super().__init__(parent)
        self.textChanged.connect(self.data_changed.emit)
        if completion:
            c = QCompleter(completion)
            c.setCaseSensitivity(Qt.CaseInsensitive)
            self.setCompleter(c)

    def set_data(self, value):
        self.setText(str(value or ""))

    def get_data(self):
        return self.text()



class DateEditable(QFrame):

    data_changed = pyqtSignal(datetime.date)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        j = QSpinBox()
        j.setMinimum(0)
        j.setMaximum(31)
        m = QSpinBox()
        m.setMinimum(0)
        m.setMaximum(12)
        a = QSpinBox()
        a.setMinimum(0)
        a.setMaximum(2500)
        j.setAlignment(Qt.AlignCenter)
        m.setAlignment(Qt.AlignCenter)
        a.setAlignment(Qt.AlignCenter)
        j.setSpecialValueText(" ")
        m.setSpecialValueText(" ")
        a.setSpecialValueText(" ")
        layout.addWidget(j, 0, 0)
        layout.addWidget(m, 0, 1)
        layout.addWidget(a, 0, 2, 1, 2)

        j.valueChanged.connect(lambda v: self.data_changed.emit(self.get_data()))
        m.valueChanged.connect(lambda v: self.data_changed.emit(self.get_data()))
        a.valueChanged.connect(lambda v: self.data_changed.emit(self.get_data()))
        self.ws = (a, m, j)

    def get_data(self):
        d = [self.ws[0].value(), self.ws[1].value(), self.ws[2].value()]
        try:
            d = datetime.date(*d)
        except ValueError:
            d = formats.DATE_DEFAULT
        return d

    def set_data(self, d):
        d = d and (d.year, d.month, d.day) or (0, 0, 0)
        self.ws[0].setValue(d[0])
        self.ws[1].setValue(d[1])
        self.ws[2].setValue(d[2])


class MontantEditable(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.val = QDoubleSpinBox()
        self.val.setMaximum(100000)
        self.par_jour = QCheckBox("Par jour")
        layout = QVBoxLayout(self)
        layout.addWidget(self.val)
        layout.addWidget(self.par_jour)

    def set_data(self, value):
        self.val.setValue(value[0])
        self.par_jour.setChecked(value[1])

    def get_data(self):
        return [self.val.value(), self.par_jour.isChecked()]


class DateRange(QFrame):
    data_changed = pyqtSignal(datetime.date, datetime.date)

    def __init__(self):
        super().__init__()
        self.debut = DateEditable()
        self.fin = DateEditable()
        self.debut.data_changed.connect(self.on_change)
        self.fin.data_changed.connect(self.on_change)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(QLabel("Du "))
        layout.addWidget(self.debut)
        layout.addWidget(QLabel(" au "))
        layout.addWidget(self.fin)

    def on_change(self):
        self.data_changed.emit(*self.get_data())

    def get_data(self):
        return self.debut.get_data(), self.fin.get_data()

    def set_data(self, v):
        self.debut.set_data(v[0])
        self.fin.set_data(v[1])


###---------------------------- Wrappers---------------------------- ###

def _get_widget(classe, value):
    w = classe()
    w.set_data(value)
    return w


def Default(value, is_editable):
    return _get_widget(is_editable and DefaultEditable or DefaultFixe, value)


def Booleen(value, is_editable):
    return _get_widget(is_editable and BoolEditable or BoolFixe, value)


def Entier(entier, is_editable):
    return _get_widget(is_editable and EntierEditable or DefaultFixe, entier)


def Euros(value, is_editable):
    return _get_widget(is_editable and EurosEditable or EurosFixe, value)


def Pourcent(value, is_editable):
    return _get_widget(is_editable and PourcentEditable or PourcentFixe, value)


def Date(value, is_editable):
    return _get_widget(is_editable and DateEditable or DateFixe, value)

