"""Implements widgets to visualize and modify basic fields. (french language)
ASSOCIATION should be updated with custom widgets, since common.abstractDetails will use it.
"""
import datetime
import re
from collections import defaultdict

from PyQt5.QtCore import pyqtSignal, Qt, QPoint
from PyQt5.QtGui import QColor, QPen, QBrush, QIcon
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QPushButton, QLineEdit, QLabel, QComboBox, QSpinBox, QDoubleSpinBox, \
    QCheckBox, QCompleter, QGridLayout, QVBoxLayout, QPlainTextEdit, QStyledItemDelegate, QToolTip

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
    def IS_TELEPHONE(s: str):
        r = re.compile(r'[0-9]{9,10}')
        m = r.search(s.replace(' ', ''))
        return (m is not None)

    def _clear(self):
        clear_layout(self.layout())

    def enter_edit(self):
        self._clear()
        line_layout = self.layout()
        self.entree = QLineEdit()
        self.entree.setObjectName("nouveau-numero-tel")
        self.entree.setAlignment(Qt.AlignCenter)
        self.entree.setPlaceholderText("Ajouter...")
        add = QPushButton()
        add.setIcon(QIcon(Icons.Valid))
        add.clicked.connect(self.on_add)
        self.entree.editingFinished.connect(self.on_add)
        line_layout.addWidget(self.entree)
        line_layout.addWidget(add)
        line_layout.setStretch(0, 3)
        line_layout.setStretch(1, 1)

    def on_add(self):
        num = self.entree.text()
        if self.IS_TELEPHONE(num):
            self.entree.setPlaceholderText("Ajouter...")
            self.data_changed.emit(num)
            self._clear()
            self.set_button()
        else:
            self.entree.selectAll()
            QToolTip.showText(self.entree.mapToGlobal(QPoint(0, 10)), "Numéro invalide")


class Tels(list_views.abstractMutableList):

    LIST_PLACEHOLDER = "Aucun numéro."
    LIST_HEADER = None

    BOUTON = NouveauTelephone

    def __init__(self, collection: list, is_editable):
        collection = self.from_list(collection)
        super().__init__(collection, is_editable)

    def on_add(self, item):
        """Convert to pseuso acces"""
        super(Tels, self).on_add(list_views.PseudoAccesCategorie(item))

    def set_data(self, collection):
        collection = self.from_list(collection)
        super(Tels, self).set_data(collection)

    def get_data(self):
        col = super(Tels, self).get_data()
        return [tel.Id for tel in col]


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


# -------------- Enumerations vizualisation --------------
class abstractEnum(QLabel):

    VALUE_TO_LABEL = None
    """Dict. giving label from raw value"""

    DEFAULT_VALUE = None
    """Default raw value"""

    def set_data(self, value):
        self.value = value
        if self.value is None:
            if self.DEFAULT_VALUE:
                value = self.DEFAULT_VALUE
                self.setText(self.VALUE_TO_LABEL[value])
            else:
                self.setText("")
        else:
            self.setText(self.VALUE_TO_LABEL[self.value])

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
        if value is None:
            self.setCurrentIndex(-1)
        else:
            self.setCurrentIndex(self.places[value])
            self.data_changed.emit(self.get_data())

    def get_data(self):
        return self.currentData()


# -------------------- Commons types --------------------
class DepartementFixe(abstractEnum):
    VALUE_TO_LABEL = formats.DEPARTEMENTS
    DEFAULT_VALUE = "00"


class DepartementEditable(abstractEnumEditable):
    VALEURS_LABELS = sorted((i, i + " " + v) for i, v in formats.DEPARTEMENTS.items())
    DEFAULT_VALUE = '00'


class SexeFixe(abstractEnum):
    VALUE_TO_LABEL = formats.SEXES



class SexeEditable(abstractEnumEditable):
    VALEURS_LABELS = sorted((k, v) for k, v in formats.SEXES.items())
    DEFAULT_VALUE = "F"


class ModePaiementFixe(abstractEnum):
    VALUE_TO_LABEL = formats.MODE_PAIEMENT
    DEFAULT_VALUE = "cheque"


class ModePaiementEditable(abstractEnumEditable):
    VALEURS_LABELS = sorted([(k, v) for k, v in formats.MODE_PAIEMENT.items()])
    DEFAULT_VALUE = "cheque"


# ------------- Simple string-like field -------------
class abstractSimpleField(QLabel):
    FONCTION_AFF = None
    TOOLTIP = None

    data_changed = pyqtSignal()  # dummy signal

    def __init__(self, *args, **kwargs):
        super(abstractSimpleField, self).__init__(*args, **kwargs)
        if self.TOOLTIP:
            self.setToolTip(self.TOOLTIP)

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


class DateHeureFixe(abstractSimpleField):
    FONCTION_AFF = staticmethod(formats.abstractRender.dateheure)


# --------------- Numeric fields ---------------
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
        self.setSpecialValueText(" ")

    def set_data(self, somme):
        somme = somme if somme is not None else (self.MIN - 1)
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
        self.setMinimum(-1)
        self.setSpecialValueText(" ")
        self.setSuffix("€")
        self.valueChanged.connect(self.data_changed.emit)

    def set_data(self, somme):
        somme = somme if somme is not None else -1
        self.setValue(somme)

    def get_data(self):
        v = self.value()
        return v if v != -1 else None

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


class OptionnalTextEditable(QFrame):
    """QCheckbox + QLineEdit"""

    data_changed = pyqtSignal(object)

    def __init__(self, parent=None):
        super(OptionnalTextEditable, self).__init__(parent=parent)
        self.active = QCheckBox()
        self.text = QLineEdit()

        self.active.clicked.connect(self.on_click)
        self.text.textChanged.connect(self.on_text_changed)

        layout = QHBoxLayout(self)
        layout.addWidget(self.active)
        layout.addWidget(self.text)

    def on_click(self):
        self.text.setEnabled(self.active.isChecked())
        self.data_changed.emit(self.get_data())

    def on_text_changed(self, text):
        is_active = bool(text.strip())
        self.active.setChecked(is_active)
        self.text.setEnabled(is_active)
        self.data_changed.emit(self.get_data())

    def get_data(self):
        text = self.text.text().strip()
        active = self.active.isChecked() and bool(text)
        return text if active else None

    def set_data(self, text: str):
        text = text or ""
        is_active = bool(text.strip())
        self.active.setChecked(is_active)
        self.text.setEnabled(is_active)
        self.text.setText(text)
        self.data_changed.emit(self.get_data())


class DateEditable(QFrame):
    data_changed = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        j = QSpinBox()
        j.setMinimum(0)
        j.setMaximum(31)
        j.setToolTip("Jour")
        m = QSpinBox()
        m.setMinimum(0)
        m.setMaximum(12)
        m.setToolTip("Mois")
        a = QSpinBox()
        a.setMinimum(0)
        a.setMaximum(2500)
        a.setToolTip("Année")
        j.setAlignment(Qt.AlignCenter)
        m.setAlignment(Qt.AlignCenter)
        a.setAlignment(Qt.AlignCenter)
        j.setSpecialValueText("-")
        m.setSpecialValueText("-")
        a.setSpecialValueText("-")
        layout.addWidget(j, 0, 0)
        layout.addWidget(m, 0, 1)
        layout.addWidget(a, 0, 2, 1, 2)

        j.valueChanged.connect(lambda v: self.data_changed.emit(self.get_data()))
        m.valueChanged.connect(lambda v: self.data_changed.emit(self.get_data()))
        a.valueChanged.connect(lambda v: self.data_changed.emit(self.get_data()))
        a.editingFinished.connect(self.on_editing)
        self.ws = (a, m, j)

    def _change_year_text_color(self, is_ok):
        color = "black" if is_ok else "red"
        self.ws[0].setStyleSheet(f"color : {color}")

    def on_editing(self):
        current_year = self.ws[0].value()
        if not current_year:
            return
        self._change_year_text_color(not current_year < 100)
        self.ws[0].setValue(current_year)


    def get_data(self):
        d = [self.ws[0].value(), self.ws[1].value(), self.ws[2].value()]
        try:
            return datetime.date(*d)
        except ValueError:
            return

    def set_data(self, d):
        if d is None:
            self.ws[0].clear()
            self.ws[1].clear()
            self.ws[2].clear()
        else:
            self.ws[0].setValue(d.year)
            self.ws[1].setValue(d.month)
            self.ws[2].setValue(d.day)
        self.on_editing()


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
    data_changed = pyqtSignal(object, object)

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
        self.setSizeAdjustPolicy(QPlainTextEdit.AdjustToContents)
        self.setMinimumHeight(30)
        self.setPlaceholderText(placeholder)
        self.setReadOnly(not is_editable)
        self.textChanged.connect(lambda: self.data_changed.emit(self.toPlainText()))

    def get_data(self):
        return self.toPlainText()

    def set_data(self, text):
        self.setPlainText(text)


class OptionsButton(QPushButton):
    """Bouton to open window to acces advanced options.
    CLASS_PANEL_OPTIONS is responsible for doing the actual modification"""

    TITLE = "Advanced options"
    CLASS_PANEL_OPTIONS = None

    options_changed = pyqtSignal()

    def __init__(self, acces, is_editable):
        super(OptionsButton, self).__init__(self.TITLE)
        self.clicked.connect(self.show_options)
        self.acces = acces
        self.is_editable = is_editable

    def show_options(self):
        f = self.CLASS_PANEL_OPTIONS(self.acces, self.is_editable)
        if f.exec_():
            self.options_changed.emit()

    def set_data(self, *args):
        pass




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
    w.set_data(value)
    return w


def OptionnalText(value, is_editable):
    return _get_widget(is_editable and OptionnalTextEditable or DefaultFixe, value)

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
        proportion = min(proportion, 100)
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
