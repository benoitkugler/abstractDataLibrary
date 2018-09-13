"""Implements widgets to visualize and modify basic fields. (french language)
ASSOCIATION should be updated with custom widgets, since common.abstractDetails will use it.
"""
import datetime
import re
from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor, QPen, QBrush
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QPushButton, QLineEdit, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, \
    QCheckBox, QCompleter, QGridLayout, QVBoxLayout, QPlainTextEdit, QStyledItemDelegate

from . import list_views, clear_layout, Icons
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
        add.setIcon(Icons.Valid)
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



class DepartementFixe(abstractEnum):
    VALEUR_TO_LABEL = formats.DEPARTEMENTS
    DEFAULT_VALUE = "00"


class DepartementEditable(abstractEnumEditable):
    VALEURS_LABELS = sorted((i, i + " " + v) for i, v in formats.DEPARTEMENTS.items())
    DEFAULT_VALUE = '00'


class SexeFixe(abstractEnum):
    VALEUR_TO_LABEL = formats.SEXES
    DEFAULT_VALUE = "F"


class SexeEditable(abstractEnumEditable):
    VALEURS_LABELS = sorted((k, v) for k, v in formats.SEXES.items())
    DEFAULT_VALUE = "F"


class ModePaiementFixe(abstractEnum):
    VALEUR_TO_LABEL = formats.MODE_PAIEMENT
    DEFAULT_VALUE = "cheque"


class ModePaiementEditable(abstractEnumEditable):
    VALEURS_LABELS = sorted([(k, v) for k, v in formats.MODE_PAIEMENT.items()])
    DEFAULT_VALUE = "cheque"



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

class DateHeureFixe(QLabel):
    FONCTION_AFF = staticmethod(formats.abstractRender.dateheure)



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



class Texte(QPlainTextEdit):
    data_changed = pyqtSignal(str)

    def __init__(self, text, is_editable, placeholder="Informations complémentaires"):
        super().__init__(text)
        self.setSizeAdjustPolicy(QPlainTextEdit.AdjustToContentsOnFirstShow)
        self.setMinimumHeight(20)
        self.setPlaceholderText(placeholder)
        self.setReadOnly(not is_editable)
        self.textChanged.connect(lambda: self.data_changed.emit(self.toPlainText()))

    def get_data(self):
        return self.toPlainText()

    def set_data(self, text):
        self.setPlainText(text)






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


def Departement(value, is_editable):
    return _get_widget(is_editable and DepartementEditable or DepartementFixe, value)


def Sexe(value, is_editable):
    return _get_widget(is_editable and SexeEditable or SexeFixe, value)


def Adresse(value, is_editable):
    return Texte(value, is_editable, placeholder="")


def ModePaiement(value, is_editable):
    return _get_widget(is_editable and ModePaiementEditable or ModePaiementFixe, value)


def DateHeure(value, is_editable):
    if is_editable:
        raise NotImplementedError("No editable datetime widget !")
    w = DateHeureFixe()
    w.set_value(value)
    return w

"""Correspondance field -> widget (callable)"""
TYPES_WIDGETS = defaultdict(
    lambda: Default,
    date_naissance=Date,
    departement_naissance=Departement,
    sexe=Sexe,
    tels=Tels,
    adresse=Adresse,
    date=Date,
    date_debut=Date,
    date_fin=Date,
    date_arrivee=Date,
    date_depart=Date,
    date_emission=Date,
    date_reception=Date,
    nb_places=Entier,
    nb_places_reservees=Entier,
    age_min=Entier,
    age_max=Entier,
    acquite=Booleen,
    is_acompte=Booleen,
    is_remboursement=Booleen,
    reduc_special=Euros,
    acompte_recu=Euros,
    valeur=Euros,
    total=Euros,
    prix=Euros,
    date_heure_modif=DateHeure,
    date_reglement=Date,
    date_encaissement=Date,
    info=Texte,
    message=Texte,
    mode_paiement=ModePaiement,
)

ASSOCIATION = {}


def add_widgets_type(type_widgets, abstract_ASSOCIATION):
    TYPES_WIDGETS.update(type_widgets)
    for k, v in abstract_ASSOCIATION.items():
        t = TYPES_WIDGETS[k]
        ASSOCIATION[k] = (v[0], v[1], v[2], t, v[3])


add_widgets_type({}, formats.ASSOCIATION)


## ------------------Custom delegate  ------------------ ##

class delegateAttributs(QStyledItemDelegate):
    CORRES = {"montant": MontantEditable, "mode_paiement": ModePaiementEditable,
              "valeur": EurosEditable,
              "description": DefaultEditable, "quantite": EntierEditable,
              "obligatoire": BoolEditable}
    """Correspondance between fields and widget classes"""

    size_hint_: tuple

    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)
        self.size_hint_ = None
        self.row_done_ = None

    @staticmethod
    def paint_filling_rect(option, painter, proportion):
        rect = option.rect
        painter.save()
        color = QColor(0, 255 * proportion / 100, 100 - proportion)
        painter.setPen(QPen(color, 0.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBackgroundMode(Qt.OpaqueMode)
        painter.setBackground(QBrush(color))
        painter.setBrush(QBrush(color))
        rect.setWidth(rect.width() * proportion / 100)
        painter.drawRoundedRect(rect, 5, 5)
        painter.restore()

    @staticmethod
    def _get_field(index):
        return index.model().header[index.column()]

    def sizeHint(self, option, index):
        if self.size_hint_ and self.size_hint_[0] == index:
            return self.size_hint_[1]
        return super().sizeHint(option, index)

    def setEditorData(self, editor, index):
        value = index.data(role=Qt.EditRole)
        editor.set_data(value)
        self.sizeHintChanged.emit(index)

    def createEditor(self, parent, option, index):
        field = self._get_field(index)
        other = index.data(role=Qt.UserRole)
        classe = self.CORRES[field]
        w = classe(parent, other) if other else classe(parent)
        self.size_hint_ = (index, w.sizeHint())
        self.row_done_ = index.row()
        return w

    def destroyEditor(self, editor, index):
        self.size_hint_ = None
        super().destroyEditor(editor, index)

    def setModelData(self, editor, model, index):
        value = editor.get_data()
        model.set_data(index, value)
