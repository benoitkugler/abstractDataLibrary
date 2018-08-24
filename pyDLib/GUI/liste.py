# coding: utf-8

import os

from PyQt5.QtCore import Qt, pyqtSignal, QAbstractTableModel
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QAbstractItemView, QTableView, \
    QAbstractScrollArea, QFrame, QLabel, QGridLayout
from pyDLib.Core.groups import sortableListe

from . import Color, IMAGES_PATH, Arrow, DeleteIcon
from ..Core import formats

def _bold_font(is_bold):
    font = QFont()
    font.setBold(is_bold)
    return font

class Renderer():
    """Helper functions to unify visualisation"""

    SUPPRESS_TOOLTIP = "Supprimer la ligne"

    @staticmethod
    def headerData(section, orientation, role, attribut, sort_state):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return formats.ASSOCIATION[attribut][0]
            elif role == Qt.DecorationRole:
                if section == sort_state[0]:
                    return Arrow(is_up = sort_state[1])
            elif role == Qt.TextAlignmentRole:
                return Qt.AlignCenter
            elif role == Qt.FontRole:
                return _bold_font(True)
        elif orientation == Qt.Vertical:
            if role == Qt.DecorationRole:
                return DeleteIcon()
            elif role == Qt.ToolTipRole:
                return Renderer.SUPPRESS_TOOLTIP

    @staticmethod
    def data(attribut, value, info, role):
        if role == Qt.DisplayRole:
            fonction_aff = formats.ASSOCIATION[attribut][2]
            return fonction_aff(value)
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        elif role == Qt.FontRole:
            info_font = info.get('font', {})
            is_bold = info_font.get(attribut, False)
            return _bold_font(is_bold)
        elif role == Qt.ForegroundRole:
            niveau = info.get('niveau', 0)
            couleurs = Core.CONFIG["couleurs_niveaux"]
            niveau = min(niveau, len(couleurs) - 1)
            color = couleurs[niveau]
            return QBrush(Color(color))
        elif role == Qt.BackgroundRole:
            if attribut == 'lienid':
                is_auth = value and (value >= 0) or 0
                color = Core.CONFIG["couleur_authentifie"][int(is_auth)]
                return QBrush(QColor(color))
            elif attribut == "etat":
                if info.get("attestation_demande", None):
                    return QBrush(Color(Core.CONFIG["attestation-alert-color"]))
            sexe = info.get("sexe", None)
            couleur = sexe and Core.CONFIG["couleur_sexe"][sexe] or "transparent"
            return QBrush(Color(couleur))
        elif role == Qt.EditRole:
            return value

    @staticmethod
    def sort(model, section, attr):
        old_i, old_sort = model.sort_state
        model.beginResetModel()
        if section == old_i:
            model.collection.sort(attr, not old_sort)
            model.sort_state = (section, not old_sort)
        else:
            model.collection.sort(attr, True)
            model.sort_state = (section, True)
        model.endResetModel()


## Implémente un QModel pour visualiser une collection.
# La collection est interne.
# On définit ensuite l'entête, qui précise les champs à afficher. La collection précise les ids des entrées à afficher.
# La collection doit contenir des acces pouvant afficher les champs contenus dans l'entête.
# Il faut implementer la fonction de recherche (effective) _search, la fonction de reset _reset
#
class abstractModel(QAbstractTableModel):
    MODIFIABLES = []
    IS_EDITABLE = False

    def __init__(self, ENTETE):
        super().__init__()
        self.ENTETE = ENTETE
        # Etat de tri actuel (column,sens)
        self.sort_state = (-1, False)

    # Ré-implémentation
    def rowCount(self, index):
        return len(self.collection)

    # Ré-implémentation
    def columnCount(self, index):
        return len(self.ENTETE)

    # Ré-implémentation
    def data(self, index, role):
        acces = self.collection[index.row()]
        attr = self.ENTETE[index.column()]
        value = acces[attr]
        info = self.collection.get_info(key=index.row())
        if role == Qt.UserRole and attr == "nom_banque":
            return self.get_noms_banques()
        if role == Qt.ToolTipRole and attr == "cotisation_annuelle":
            return "Années de cotisations : {}".format(acces["cotisations"] or "Aucune")

        return Renderer.data(attr, value, info, role)

    # Ré-implémentation
    def headerData(self, section, orientation, role):
        attribut = (orientation == Qt.Horizontal) and self.ENTETE[section] or None
        return Renderer.headerData(section, orientation, role, attribut, self.sort_state)

    # Ré-implémentation
    def flags(self, index):
        if self.IS_EDITABLE and self.ENTETE[index.column()] in self.MODIFIABLES:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        else:
            return super().flags(index) | Qt.ItemIsSelectable

    def sort(self, section, order):
        attr = self.ENTETE[section]
        Renderer.sort(self, section, attr)

    def supprime_ligne(self, section):
        self.beginResetModel()
        self.collection.pop(section)
        self.endResetModel()

    def _update(self):
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(len(self.collection), len(self.ENTETE)))

    def _reset(self):
        self.beginResetModel()
        self.endResetModel()

    def get_item(self, index):
        """ Raccourci d'accès

        :param index: Number of row or index of cell
        :return: Acces
        """
        if hasattr(index, "row"):
            return self.collection[index.row()]
        else:
            return self.collection[index]

    def set_collection(self, collection):
        self.beginResetModel()
        self.collection = collection
        self.sort_state = (-1, False)
        self.endResetModel()


class modelInterne(abstractModel):

    def __init__(self, collection, ENTETE):
        self.collection = collection
        super().__init__(ENTETE)

    def _reset(self):
        self.beginResetModel()
        self.collection = []
        self.endResetModel()

    def set_item(self, index, value):
        """ Raccourci d'accès

        :param index: Number of row or index of cell
        :return: Acces
        """
        row = index.row() if hasattr(index, "row") else index
        self.collection[row] = value
        self.dataChanged.emit(self.index(row, 0), self.index(row, len(self.ENTETE) - 1))

class modelExterne(abstractModel):

    def __init__(self, fonction_collection, fonction_set_data, ENTETE):
        self.fonction_collection = fonction_collection
        self.fonction_set_data = fonction_set_data
        super().__init__(ENTETE)

    def __getattr__(self, key):
        if key == "collection":
            return self.fonction_collection()
        return super().__getattr__(key)

    def set_data(self, index, value):
        acces = self.collection[index.row()]
        attribut = self.ENTETE[index.column()]
        self.beginResetModel()
        self.fonction_set_data(acces, attribut, value)
        self.endResetModel()


class abstractListe(QTableView):
    PLACEHOLDER = "Il n'y a pas d'entrées correspondantes."

    MIN_HEIGHT = 60
    VERTICAL_HEADER_VISIBLE = False

    def __init__(self, model):
        super().__init__()
        self.setObjectName("listes")
        self.setModel(model)

        # Click sur le header pour trier
        self.horizontalHeader().sectionClicked.connect(self.on_sort)
        self.horizontalHeader().setStretchLastSection(True)
        # Visibilité du header vertical
        self.verticalHeader().setVisible(self.VERTICAL_HEADER_VISIBLE)
        self.verticalHeader().sectionClicked.connect(self.on_click_header_vertical)

        ## En cas de click, double-click
        self.doubleClicked.connect(self.on_double_click)
        self.clicked.connect(self.on_click)

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QTableView.SingleSelection)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.setMinimumHeight(self.MIN_HEIGHT)

        self.setEditTriggers(QTableView.DoubleClicked)

    # Place holder en cas de liste vide
    def paintEvent(self, paintevent):
        super().paintEvent(paintevent)
        if self.model().rowCount(self.rootIndex()) == 0:
            painter = QPainter(self.viewport())
            font = QFont()
            font.setItalic(True)
            painter.setFont(font)
            painter.drawText(self.rect().adjusted(0, 0, -5, -5), Qt.AlignCenter | Qt.TextWordWrap, self.PLACEHOLDER)

    # Pour raison d'inter-opérabilité
    def deselect(self):
        self.clearSelection()

    def _reset(self):
        self.model()._reset()

    def _update(self):
        self.model()._update()

    ## Appelé sur un click sur le header
    def on_sort(self, i):
        self.sortByColumn(i, Qt.AscendingOrder)
        self.resizeColumnToContents(i)

    def on_click(self, index):
        pass

    def on_double_click(self, index):
        pass

    def on_click_header_vertical(self, section):
        """A ré-implémenter. Par défault supprime la ligne."""
        self.model().supprime_ligne(section)

class modelMultiSelect(modelInterne):
    ENTETE = []

    def __init__(self, collection):
        super().__init__(collection, self.ENTETE)
        self.selected_ids = set()

    def flags(self, index):
        default = super().flags(index)
        if index.column() == 0:
            return default | Qt.ItemIsUserCheckable
        return default

    def data(self, index, role):
        if role == Qt.CheckStateRole and index.column() == 0:
            c_id = self.collection[index.row()].Id
            b = (c_id in self.selected_ids) and Qt.Checked or Qt.Unchecked
            return b
        if role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter
        if role == Qt.ToolTipRole:
            return super().data(index, Qt.DisplayRole)
        return super().data(index, role)

    def _set_id(self, Id, is_added, index):
        if is_added:
            self.selected_ids.add(Id)
        else:
            self.selected_ids.remove(Id)

        self.dataChanged.emit(index, index)

    def setData(self, index, value, role):
        if not (index.isValid() and role == Qt.CheckStateRole):
            return False
        c_id = self.collection[index.row()].Id
        self._set_id(c_id, value == Qt.Checked, index)
        return True

    def set_by_Id(self, Id, is_added):
        try:
            row = [a.Id for a in self.collection].index(Id)
        except IndexError:
            return
        self._set_id(Id, is_added, self.index(row, 0))



class listeMultiSelect(abstractListe):

    def __init__(self, model):
        super().__init__(model)
        self.setProperty('with_checkbox', True)
        self.horizontalHeader().setStretchLastSection(True)
        self.setWordWrap(True)


class listeRecherche(abstractListe):
    MIN_HEIGHT = 200
    PLACEHOLDER = "Aucune entrée ne correspont à la recherche."
    ENTETE = []
    selected = pyqtSignal(object, str)
    """En cas de sélection : identifiant,label"""

    def __init__(self, fonction_recherche):
        model = modelInterne(sortableListe(), self.ENTETE)
        super().__init__(model)
        self.fonction_recherche = fonction_recherche

        self.horizontalHeader().setStretchLastSection(True)

        # Hilight des lignes
        self.setMouseTracking(True)
        self.setProperty("highlight", True)

        # Mise en cache
        self.Affichage = formats.Affichage

    def on_search(self, pattern):
        collection = self.fonction_recherche(pattern)
        self.model().set_collection(collection)

    def on_click(self, index):
        acces = self.model().get_item(index)
        label = self.get_label(acces)
        self.selected.emit(acces.Id, label)

    def get_label(self, acces):
        label = "Acces numéro {}".format(acces.Id)
        return label


class listeRechercheProduit(listeRecherche):
    ENTETE = ["fou", "c", 'libf', "cond"]

    def get_label(self, acces):
        label = self.Affichage.default(acces['libf'])
        return label


class listeRechercheIngredient(listeRecherche):
    ENTETE = ["nom"]

    def get_label(self, acces):
        return self.Affichage.default(acces["nom"])


class listeRechercheRecette(listeRecherche):
    ENTETE = ["nom"]

    def get_label(self, acces):
        return self.Affichage.default(acces["nom"])


class abstractListePrincipale(abstractListe):
    ENTETE = []

    def __init__(self, interface):
        self.interface = interface
        model = self.cree_model()
        super().__init__(model)
        self.interface.add_update_function(self._update)
        self.interface.add_reset_function(self._reset)

    def cree_model(self):
        model = modelExterne(self.get_collection, self.set_data, self.ENTETE)
        return model

    def get_collection(self):
        return []

    def set_data(self, acces, attribut, value):
        pass


class CadreView(QFrame):
    view: abstractListe

    def __init__(self, view, titre):
        super().__init__()
        self.view = view

        label = QLabel(titre)
        label.setObjectName("titre-liste")
        self.label = label
        layout = QGridLayout(self)
        layout.setContentsMargins(11, 0, 11, 11)
        layout.addWidget(label, 0, 0)
        layout.setColumnStretch(0, 2)
        wd = self.widget_haut_droit()
        if wd is not None:
            layout.addWidget(wd, 0, 1)
        layout.addWidget(self.view, 1, 0, 1, 2)

    def widget_haut_droit(self):
        return

    def set_title(self, t):
        self.label.setText(t)
