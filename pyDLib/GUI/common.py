"""Common widgets"""

from os.path import expanduser

from PyQt5.QtCore import *
from PyQt5.QtWidgets import (QFrame, QLabel, QPushButton, QLineEdit, QFormLayout, QFileDialog, QCheckBox,
                             QHBoxLayout, QVBoxLayout, QGridLayout, QProgressBar,
                             qApp)

from . import clear_layout
from .fenetres import Window
from .fields import ASSOCIATION
from ..Core import data_model


class LoadingMonitor(Window):

    def __init__(self, titre, parent):
        super().__init__(titre, parent=parent, no_flags=True)

        self.label = QLabel()
        self.progress_bar = QProgressBar()
        self.add_widget(self.label)
        self.add_widget(self.progress_bar)
        self.setModal(True)
        self.show()

    def setLabel(self, text):
        self.label.setText(text)
        qApp.processEvents()
        self.parent().repaint()

    def monitor_dic(self, info):
        max, n, status = info["total"], info["downloaded"], info["status"]
        self.monitor(status, n, max)

    def monitor(self, status, current, max):
        self.progress_bar.setFormat("{}   %p %".format(status))
        self.progress_bar.setMaximum(max)
        self.progress_bar.setValue(current)
        qApp.processEvents()


class ExportFolder(QFileDialog):

    def __init__(self, parent):
        super().__init__(parent, Qt.Widget)
        self.setFileMode(QFileDialog.Directory)
        self.setViewMode(QFileDialog.List)

    def get_directory(self):
        if self.exec():
            return self.selectedFiles()[0]


class ImportFile(QFileDialog):

    def __init__(self, parent, types=None):
        super().__init__(parent, Qt.Widget)
        self.setFileMode(QFileDialog.ExistingFile)
        self.setViewMode(QFileDialog.List)
        if types:
            self.setMimeTypeFilters(types)

    def get_filename(self):
        if self.exec():
            return self.selectedFiles()[0]


class DirectoryAcces(QPushButton):

    def __init__(self):
        self.directory = expanduser("~")
        self.default = expanduser("~")
        super().__init__(self.directory)
        self.clicked.connect(self.on_click)

    def on_click(self):
        cdir = ExportFolder(self)
        d = cdir.get_directory() or self.default
        self.directory = d
        self.setText(d)

    def get_directory(self):
        return self.directory


class FileAcces(QPushButton):

    PLACEHOLDER = "Choisir un fichier..."

    def __init__(self, mimetypes=None):
        self.mimetypes = mimetypes
        self.file = None
        super().__init__(self.PLACEHOLDER)
        self.clicked.connect(self.on_click)

    def on_click(self):
        c = ImportFile(self, types=self.mimetypes)
        d = c.get_filename()
        self.file = d
        self.setText(d or self.PLACEHOLDER)

    def get_file(self):
        return self.file


class SearchBox(QFrame):
    """Box with search field, buttons, and number of results"""

    def __init__(self, interface, search_header):
        QFrame.__init__(self)
        self.setObjectName("search-box")

        self.interface = interface
        self.search_header = search_header
        self.entree = QLineEdit()
        self.entree.returnPressed.connect(self.on_search)

        self.nb_res = QLabel()
        self.nb_res.setObjectName("search-result")
        self.nb_res.setAlignment(Qt.AlignCenter)

        valid = QPushButton("Chercher")
        valid.setObjectName("round")
        valid.setToolTip("Cherche en se restreignant à aux résultats de la recherche précédente.")
        valid.clicked.connect(self.on_search)

        retour = QPushButton("Annuler")
        retour.setObjectName("round")
        retour.setToolTip("Annule les résultats des recherches précédentes.")
        retour.clicked.connect(self.on_cancel)

        box = QGridLayout(self)
        box.addWidget(QLabel("Rechercher :"), 0, 0, 1, 2)
        box.addWidget(self.entree, 1, 0, 1, 2)
        box.addWidget(self.nb_res, 2, 0, 1, 2)
        box.addWidget(valid, 3, 0)
        box.addWidget(retour, 3, 1)

    def on_search(self):
        text = self.entree.text()
        if len(text) > 0:
            nb = self.interface.recherche(text, self.search_header)
            self._res_search(nb)
        else:
            self.interface.reset()
            self._res_search(-1)
        self.entree.setFocus()
        self.entree.selectAll()

    def on_cancel(self):
        self.nb_res.setText("")
        self.entree.clear()
        self.interface.reset()
        self.entree.setFocus()

    def _res_search(self, nb):
        if nb == 1:
            self.nb_res.setText(str(nb) + " résultat")
        elif nb > 1:
            self.nb_res.setText(str(nb) + " résultats")
        elif nb == 0:
            self.nb_res.setText("Pas de résultats")
        else:
            self.nb_res.setText('')


class Statistiques(QFrame):
    """Boxes with lines of statistics"""

    def __init__(self, interface):
        QFrame.__init__(self)
        self.setObjectName("stats-box")
        box = QVBoxLayout(self)

        self.interface = interface
        self.interface.add_update_function(self.set_labels)
        self.interface.add_reset_function(self.set_labels)

        self.layout_stats = QFormLayout()
        box.addWidget(QLabel('Statistiques :'))
        box.addLayout(self.layout_stats)

        self.set_labels()

    def set_labels(self):
        clear_layout(self.layout_stats)
        for l, n in zip(self.interface.get_labels_stats(), self.interface.get_stats()):
            lab = QLabel("<b>{}</b>".format(n))
            self.layout_stats.addRow(l + " : ", lab)


class abstractFilter(QFrame):
    """Display checkboxes, and use hook which should
    update state, according to current choices"""

    ENUM = None
    "List or dict of values : labels"

    TITLE = None

    def __init__(self, filter_hook):
        self.filter_hook = filter_hook
        self.etats = {}
        self.checkboxes = []
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(self.TITLE))
        if type(self.ENUM) is list:
            enum = enumerate(self.ENUM)
        else:
            enum = sorted(self.ENUM.items())
        for i, label in enum:
            self.etats[i] = True
            cb = QCheckBox(label)
            cb.setChecked(True)
            cb.clicked.connect(lambda b, i=i: self.on_change(b, i))
            layout.addWidget(cb)
            self.checkboxes.append(cb)

    def on_change(self, b, i):
        self.etats[i] = b
        etats_ok = [i for i, v in self.etats.items() if v]
        self.filter_hook(etats_ok)

    def _reset(self):
        for c in self.checkboxes:
            c.setChecked(True)



# ------------ Detailled modification widget---------------- #


class abstractDetails(QFrame):
    """Visualisation of :class:`~Core.acces.abstractAcces`.
    Modifications are stored in ``modifications`` attribute of acces object"""

    acces: data_model.abstractAcces

    done = pyqtSignal()
    """Signal de fin d'édition"""

    FIELDS = []
    """ Define basic fields to show. Elements have the form `attr` ou (`attr`,{`with_base`:True or False,`with_label`: None or `label`,`kwargs`) 
    """

    NO_CONNECT = []
    """Exceptionnaly not connect this widget to modifications"""

    DEFAULT_EDITABLE = True

    def __init__(self, acces, is_editable = None, no_layout=False):
        is_editable = self.DEFAULT_EDITABLE if is_editable is None else is_editable
        self.acces = acces
        self.is_editable = is_editable
        self.no_layout = no_layout
        self.widgets = {}
        self.champs = []
        super().__init__()

        # Création des widgets
        self.cree_widgets()

        self.layout_champs = QVBoxLayout()

        ## Barre de buttons
        self.barre = QHBoxLayout()

        self.set_widgets_champs()

        total = QVBoxLayout(self)
        total.addLayout(self.layout_champs)
        total.addLayout(self.barre)

        self.init_bouttons()

        if self.is_editable:
            self.connect()

    def cree_widgets(self):
        """Create widgets and store them in self.widgets"""
        for t in self.FIELDS:
            if type(t) is str:
                attr, kwargs = t, {}
            else:
                attr, kwargs = t[0], t[1].copy()
            self.champs.append(attr)
            is_editable = kwargs.pop("is_editable", self.is_editable)
            args = [self.acces[attr], is_editable]
            with_base = kwargs.pop("with_base", False)
            if with_base:
                args.append(self.acces.base)

            if 'with_label' in kwargs:
                label = kwargs.pop('with_label')
            else:
                label = ASSOCIATION[attr][0]
            if kwargs:
                w = ASSOCIATION[attr][3](*args, **kwargs)
            else:
                w = ASSOCIATION[attr][3](*args)

            self.widgets[attr] = (w, label)

    def _set_field(self, layout, field):
        w, label = self.widgets[field]
        if label:
            layout.addRow(label, w)
        else:
            layout.addRow(w)

    def set_widgets_champs(self):
        if self.no_layout:
            return
        self.layout_champs = QFormLayout()
        self.layout_champs.setVerticalSpacing(15)
        for attr in self.champs:
            self._set_field(self.layout_champs, attr)

    def _update(self):
        for attr, (w, _) in self.widgets.items():
            w.set_data(self.acces[attr])

    def connect(self):
        for attr, (w, _) in self.widgets.items():
            if (not attr in self.NO_CONNECT) and hasattr(w, 'data_changed'):
                w.data_changed.connect(lambda arg, attr=attr: self.on_widget_data_changed(attr, arg))

    def on_widget_data_changed(self, key, value):
        self.acces.modifie(key, value)
        if hasattr(self, "boutton_reset"):
            self.boutton_reset.setEnabled(True)

    def cree_boutton_valider(self):
        b = QPushButton("Valider")
        b.clicked.connect(self.done.emit)
        self.boutton_valider = b

    def cree_boutton_reset(self):
        b = QPushButton("Effacer les changements")
        b.setEnabled(bool(self.acces.modifications))
        def on_clear():
            self.acces.modifications.clear()
            self._update()
            b.setEnabled(False)
        b.clicked.connect(on_clear)
        self.boutton_reset = b

    def init_bouttons(self):
        if self.is_editable:
            self.cree_boutton_valider()
            self.cree_boutton_reset()
            self._set_bouttons([self.boutton_valider,self.boutton_reset])

    def _set_bouttons(self, bouttons):
        for b in bouttons:
            self.barre.addWidget(b)


class FenetreDetails(Window):
    """Display a detail widget in a separate window."""

    def __init__(self,widget_details,titre="Détails"):
        super().__init__(titre)
        self.add_widget(widget_details)
        self.retour = False
        widget_details.done.connect(self.on_done)

    def on_done(self):
        self.retour = True
        self.accept()

