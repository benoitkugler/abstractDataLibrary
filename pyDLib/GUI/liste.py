# coding: utf-8
from typing import List, Tuple

from PyQt5.QtCore import Qt, pyqtSignal, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QFont, QBrush, QPaintEvent, QPainter
from PyQt5.QtWidgets import QAbstractItemView, QTableView, \
    QAbstractScrollArea, QFrame, QLabel, QGridLayout, QLineEdit, QPushButton

from pyDLib.Core.groups import sortableListe
from . import Color, Arrow, DeleteIcon, PARAMETERS, fenetres
from ..Core import formats, groups, data_model, controller


def _custom_font(is_bold=False,is_italic=False):
    font = QFont()
    font.setBold(is_bold)
    font.setItalic(is_italic)
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
                return _custom_font(is_bold=True)
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
            return _custom_font(is_bold=is_bold)
        elif role == Qt.ForegroundRole:
            niveau = info.get('level', 0)
            couleurs = PARAMETERS["level_colors"]
            niveau = min(niveau, len(couleurs) - 1)
            color = couleurs[niveau]
            return QBrush(Color(color))
        elif role == Qt.BackgroundRole:
            sexe = info.get("sexe", None)
            couleur = PARAMETERS["sexe_color"][sexe] if sexe else "transparent"
            return QBrush(Color(couleur))
        elif role == Qt.EditRole:
            return value


### ------------------- Models ------------------- ###


class abstractModel(QAbstractTableModel):
    """Model to visualize a list of items (ie dict like objects).
    This list may be a Core.groups.collection (list of acces, indexed by Id) or a list of static objects (Core.groups.sortableList)
    header defines the fields to display.
    IS_EDITABLE allows to edit items by double-clicking, EDITABLE_FIELDS list the fields which may be edited.
    """

    EDITABLE_FIELDS = []
    IS_EDITABLE = False
    RENDERER = Renderer


    header : List
    sort_state : Tuple
    collection : groups.sortableListe

    def __init__(self, header):
        super().__init__()
        self.header = header
        self.sort_state = (-1, False)


    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.collection)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.header)

    def data(self, index : QModelIndex, role=None):
        acces , attr  = self.collection[index.row()] ,  self.header[index.column()]
        value = acces[attr]
        info = self.collection.get_info(key=index.row())

        return self.RENDERER.data(attr, value, info, role)

    def headerData(self, section : int, orientation : Qt.Orientation, role=None):
        attribut = (orientation == Qt.Horizontal) and self.header[section] or None
        return self.RENDERER.headerData(section, orientation, role, attribut, self.sort_state)

    def flags(self, index : QModelIndex):
        """All fields are selectable"""
        if self.IS_EDITABLE and self.header[index.column()] in self.EDITABLE_FIELDS:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        else:
            return super().flags(index) | Qt.ItemIsSelectable

    def sort(self, section : int, order=None):
        """Order is defined by the current state of sorting"""
        attr = self.header[section]
        old_i, old_sort = self.sort_state
        self.beginResetModel()
        if section == old_i:
            self.collection.sort(attr, not old_sort)
            self.sort_state = (section, not old_sort)
        else:
            self.collection.sort(attr, True)
            self.sort_state = (section, True)
        self.endResetModel()

    def remove_line(self, section):
        """Base implementation just pops the item from collection.
        Re-implements to add global behaviour
        """
        self.beginResetModel()
        self.collection.pop(section)
        self.endResetModel()

    def _update(self):
        """Emit dataChanged signal on all cells"""
        self.dataChanged.emit(self.createIndex(0, 0), self.createIndex(len(self.collection), len(self.header)))

    def _reset(self):
        """Emit resetModel """
        self.beginResetModel()
        self.endResetModel()

    def get_item(self, index):
        """ Acces shortcut

        :param index: Number of row or index of cell
        :return: Dict-like item
        """
        row = index.row() if hasattr(index, "row") else index
        return self.collection[row]

    def set_collection(self, collection):
        """Reset sort state, set collection and emit resetModel signal"""
        self.beginResetModel()
        self.collection = collection
        self.sort_state = (-1, False)
        self.endResetModel()


class InternalDataModel(abstractModel):
    """This model stores the data by itself : the data shouldn't be modified from outside."""

    def __init__(self, collection: groups.sortableListe, header : List):
        super().__init__(header)
        self.collection = collection

    def _reset(self):
        """Default implementation is to set an empty collection"""
        self.set_collection(groups.sortableListe())

    def set_item(self, index, new_item):
        """ Changes item at index in collection. Emit dataChanged signal.

        :param index: Number of row or index of cell
        :param new_item: Dict-like object
        """
        row = index.row() if hasattr(index, "row") else index
        self.collection[row] = new_item
        self.dataChanged.emit(self.index(row, 0), self.index(row, self.rowCount() - 1))


class ExternalDataModel(abstractModel):
    """This model uses external collection.
    The acces to collection attribute calls collection_hook.
    Setting data of one field for one item calls set_data_hook.
    """

    def __init__(self, collection_hook, set_data_hook, header):
        self.collection_hook = collection_hook
        self.set_data_hook = set_data_hook
        super().__init__(header)

    @property
    def collection(self):
        """Uses given collection getter"""
        return self.collection_hook()

    def set_collection(self, collection):
        raise NotImplementedError("ExternalDataModel does not own it's collection !")

    def set_data(self, index, value):
        """Uses given data setter, and emit modelReset signal"""
        acces ,field = self.get_item(index) , self.header[index.column()]
        self.beginResetModel()
        self.set_data_hook(acces, field, value)
        self.endResetModel()


class MultiSelectModel(InternalDataModel):
    """Allows to select multiples lines of the collection.
    Item must have Id attribute.
    """

    collection = groups.Collection

    def __init__(self, collection, header):
        super().__init__(collection, header)
        self.selected_ids = set()

    def flags(self, index):
        default = super().flags(index)
        if index.column() == 0:
            return default | Qt.ItemIsUserCheckable
        return default

    def data(self, index : QModelIndex, role=None):
        if role == Qt.CheckStateRole and index.column() == 0:
            c_id = self.get_item(index).Id
            b = (c_id in self.selected_ids) and Qt.Checked or Qt.Unchecked
            return b
        if role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter
        if role == Qt.ToolTipRole:
            return super().data(index, Qt.DisplayRole)
        return super().data(index, role)

    def _set_id(self, Id, is_added, index):
        """Update selected_ids and emit dataChanged"""
        if is_added:
            self.selected_ids.add(Id)
        else:
            self.selected_ids.remove(Id)

        self.dataChanged.emit(index, index)

    def setData(self, index : QModelIndex, value, role=None):
        """Update selected_ids on click on index cell."""
        if not (index.isValid() and role == Qt.CheckStateRole):
            return False
        c_id = self.get_item(index).Id
        self._set_id(c_id, value == Qt.Checked, index)
        return True

    def set_by_Id(self, Id, is_added):
        """Update selected_ids with given Id"""
        row = self.collection.index_from_id(Id)
        if row is None:
            return
        self._set_id(Id, is_added, self.index(row, 0))




### -------------------- Views -------------------- ###


class abstractList(QTableView):
    """Base class for view widgets.
    Should use a model based on InternalDataModel or ExternalDataModel"""

    PLACEHOLDER = "Empty list."
    """To display for an empty collection"""

    MIN_HEIGHT = 60
    VERTICAL_HEADER_VISIBLE = False
    
    SELECTION_BEHAVIOR = QAbstractItemView.SelectRows
    SELECTION_MODE = QAbstractItemView.SingleSelection
        
    def __init__(self, model):
        super().__init__()
        self.setObjectName("list-view")
        self.setModel(model)

        self.horizontalHeader().sectionClicked.connect(self.on_sort)  # sort on header click
        self.horizontalHeader().setStretchLastSection(True)
        
        self.verticalHeader().setVisible(self.VERTICAL_HEADER_VISIBLE)
        self.verticalHeader().sectionClicked.connect(self.on_click_header_vertical)

        self.doubleClicked.connect(self.on_double_click)
        self.clicked.connect(self.on_click)

        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(self.SELECTION_BEHAVIOR)
        self.setSelectionMode(self.SELECTION_MODE)
        
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.setMinimumHeight(self.MIN_HEIGHT)

        self.setEditTriggers(QTableView.DoubleClicked)
        
    def model(self) -> abstractModel:
        return super(abstractList, self).model()

    def paintEvent(self, paintevent : QPaintEvent):
        """Displays placeholder in case of empty collection"""
        super().paintEvent(paintevent)
        if self.model().rowCount() == 0:
            painter = QPainter(self.viewport())
            painter.setFont(_custom_font(is_italic=True))
            painter.drawText(self.rect().adjusted(0, 0, -5, -5), Qt.AlignCenter | Qt.TextWordWrap,
                             self.PLACEHOLDER)

    def on_sort(self, i):
        self.sortByColumn(i,None)
        self.resizeColumnToContents(i)

    def on_click(self, index):
        pass

    def on_double_click(self, index):
        pass

    def on_click_header_vertical(self, section):
        """Default implementation removes the line"""
        self.model().remove_line(section)


class MultiSelectList(abstractList):
    """Add data_changed signal, and get_data, set_data methods"""

    data_changed = pyqtSignal(list)
    """Emitted on change of selected Ids"""

    def model(self) -> MultiSelectModel:
        return super(MultiSelectList, self).model()

    def __init__(self, model : MultiSelectModel):
        super().__init__(model)
        self.setProperty('with_checkbox', True)
        self.setWordWrap(True)

    def get_data(self):
        return list(self.model().selected_ids)

    def set_data(self, ids_list):
        ids_list = ids_list or []
        self.model().beginResetModel()
        self.model().selected_ids = set(ids_list)
        self.model().endResetModel()
        self.data_changed.emit(self.get_data())


class SearchList(abstractList):
    MIN_HEIGHT = 200
    PLACEHOLDER = "Aucune entrée ne correspont à la recherche."

    selected = pyqtSignal(data_model.abstractAcces)

    """Emitted on selection. Returns Id,label"""

    def __init__(self, entete, placeholder=None):
        model = InternalDataModel(sortableListe(),entete)
        super().__init__(model)
        if placeholder is not None:
            self.PLACEHOLDER = placeholder

        self.setMouseTracking(True)   # Lines highlight
        self.setProperty("highlight", True)

    def on_click(self, index):
        acces = self.model().get_item(index)
        self.selected.emit(acces)





class abstractMainList(abstractList):
    """Visualize main collections. Use an ExternalDataModel."""

    ENTETE = []

    interface : controller.abstractInterface

    def __init__(self, interface):
        self.interface = interface
        model = self.cree_model()
        super().__init__(model)
        self.interface.add_update_function(self._update)
        self.interface.add_reset_function(self._reset)

    def cree_model(self):
        model = ExternalDataModel(self.get_collection, self.set_data, self.ENTETE)
        return model

    def get_collection(self):
        return []

    def set_data(self, acces, attribut, value):
        pass


class CadreView(QFrame):
    view: abstractList

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




## -------------  Id search widgets  ------------- ##

class abstractAccesId(fenetres.Window):
    """Takes a search function, which performs Id search.
    If user selects a result, the window is closed, and an Core.data_model.abstractAcces is
    stored in return_value attribute.
    """

    WINDOW_TITLE = "Search"

    LIST_ENTETE = []
    LIST_PLACEHOLDER = "No items found."

    SEARCH_PLACEHOLDER = f"Please type at least {data_model.MIN_CHAR_SEARCH} characters..."


    def __init__(self, search_hook):
        super().__init__(self.WINDOW_TITLE)
        self.return_value = None
        self.search_hook = search_hook

        self.entry = QLineEdit()
        self.entry.setPlaceholderText(self.SEARCH_PLACEHOLDER)

        self.choices_view = SearchList(self.LIST_ENTETE,placeholder=self.LIST_PLACEHOLDER)

        self.entry.textChanged.connect(self.on_search)  # On search

        self.choices_view.selected.connect(self.on_done) # On click on result

        self.addWidget(self.entry)
        self.addWidget(self.choices_view)

    def on_search(self,pattern):
        collection = self.search_hook(pattern)
        self.choices_view.model().set_collection(collection)

    def on_done(self, acces):
        self.return_value = acces
        self.accept()


class abstractBaseAccesId(abstractAccesId):
    """Use the method given SEARCH_FUNCTION_NAME of Core.data_model.abstractBase object"""

    SEARCH_FUNCTION_NAME = ""

    def __init__(self,base):
        search_hook = getattr(base,self.SEARCH_FUNCTION_NAME)
        super(abstractBaseAccesId, self).__init__(search_hook)


class BoutonAccesId(QPushButton):
    """Button given acces to search window"""

    data_changed = pyqtSignal(object)

    WINDOW = None
    """Search window class, inherits abstractBaseAccesId.
    Must implements """

    acces : data_model.abstractAcces

    @staticmethod
    def format_acces_from_field(field,acces):
        """Display given field of acces.
        Field must be registered in formats.ASSOCIATION.
        """
        return formats.ASSOCIATION[field][1](acces[field])

    def __init__(self, placeholder, is_editable, base):
        super().__init__(placeholder)
        self.setEnabled(is_editable)
        self.base = base
        self.clicked.connect(self.on_click)
        self.acces = None

    def on_click(self):
        fen = self.WINDOW(self.base)
        if fen.exec_():
            self.acces = fen.retour
            self.set_label()
            self.data_changed.emit(self.get_data())

    def _format_acces(self,acces):
        """Might use format_acces_from_field"""
        raise NotImplementedError

    def _acces_from_id(self,id):
        raise NotImplementedError

    def set_label(self):
        label = self._format_acces(self.acces)
        self.setText(label)

    def get_data(self):
        return self.acces.Id

    def set_data(self,Id):
        acces = self._acces_from_id(Id)
        self.acces = acces
        self.set_label()







class viewListe(QTableView):

    def __init__(self, model, is_editable):
        super().__init__()
        self.setObjectName("liste-attribut")
        self.setShowGrid(False)
        self.setModel(model)
        self.horizontalHeader().setVisible(False)
        self.verticalHeader().setVisible(is_editable)
        self.verticalHeader().sectionClicked.connect(model.supprime)
        self.setMinimumHeight(50)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        ##Attention, cette fonction est gourmande. A éviter pour des listes de plus 1000 entrées
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)


class abstractListeModel(QAbstractTableModel):

    def __init__(self, liste, is_editable, base):
        super().__init__()
        self.liste = liste or []
        self.is_editable = is_editable
        self.base = base
        self.set_data(liste)

    def rowCount(self, index):
        return len(self.liste or [])

    def columnCount(self, index):
        return 1

    def headerData(self, section, orientation, role):
        if orientation == Qt.Vertical:
            if role == Qt.DecorationRole:
                return QPixmap(CHEMIN_IMAGES + "delete.png")
            elif role == Qt.ToolTipRole:
                return "Supprimer"
        else:
            return super().headerData(section, orientation, role)

    def set_data(self, liste):
        self.beginResetModel()
        self.liste = liste or []
        self.endResetModel()

    def supprime(self, row):
        self.beginResetModel()
        del self.liste[row]
        self.endResetModel()

    def ajoute(self, element):
        self.beginResetModel()
        self.liste.append(element)
        self.endResetModel()


class modelTels(abstractListeModel):

    def __init__(self, liste, is_editable, base):
        super().__init__(liste, is_editable, None)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.liste[index.row()]


class abstractBoutonNouveau(QFrame):
    ajoute = pyqtSignal(object)
    LABEL = "Ajouter"

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


class NouveauTelephone(abstractBoutonNouveau):
    LABEL = "Ajouter un numéro"

    def __init__(self, is_editable, base):
        super().__init__(is_editable)

    def clear(self):
        clear_layout(self.layout())

    def sort_edit(self):
        self.clear()
        self.set_button()

    def enter_edit(self):
        self.clear()
        line_button = self.layout()
        self.entree = QLineEdit()
        self.entree.setObjectName("nouveau-numero-tel")
        self.entree.setAlignment(Qt.AlignCenter)
        self.entree.setPlaceholderText("Ajouter...")
        add = QPushButton()
        add.setIcon(QIcon(QPixmap("images/ok.png")))
        add.clicked.connect(self.on_add)
        self.entree.editingFinished.connect(self.on_add)
        line_button.addWidget(self.entree)
        line_button.addWidget(add)
        line_button.setStretch(0, 3)
        line_button.setStretch(1, 1)

    def on_add(self):
        num = self.entree.text()
        num = num.replace(" ", '')
        if IS_TELEPHONE(num):
            self.entree.clear()
            self.entree.setPlaceholderText("Ajouter...")
            self.ajoute.emit(num)
            self.sort_edit()
        else:
            self.entree.clear()
            self.entree.setPlaceholderText("Numéro invalide")


class NouvelEnfant(abstractBoutonNouveau):
    LABEL = "Ajouter un enfant"

    def __init__(self, is_editable, base):
        self.base = base
        super().__init__(is_editable)

    def set_button(self):
        b = acces_ids.BoutonAjoutIdPersonne("Ajouter un enfant", True, self.base)
        b.setEnabled(self.is_editable)
        b.data_changed.connect(self.ajoute.emit)
        self.layout().addWidget(b)


class abstractBaseListe(QFrame):
    MODEL = None
    BOUTON_NOUVEAU = None

    data_changed = pyqtSignal(list)

    def __init__(self, liste, is_editable, base=None):
        super().__init__()
        model = self.MODEL(liste, is_editable, base)
        self.view = viewListe(model, is_editable)

        model.modelReset.connect(lambda: self.data_changed.emit(model.liste))

        layout = QVBoxLayout(self)
        layout.addWidget(self.view)

        if self.BOUTON_NOUVEAU and is_editable:
            nouveau = self.BOUTON_NOUVEAU(is_editable, base)
            nouveau.ajoute.connect(model.ajoute)
            layout.addWidget(nouveau)

    def set_data(self, liste):
        self.view.model().set_data(liste)

    def get_data(self):
        return list(self.view.model().liste)


class Tels(abstractBaseListe):
    MODEL = modelTels
    BOUTON_NOUVEAU = NouveauTelephone


class DateHeure(QLabel):
    data_changed = pyqtSignal(object)

    def __init__(self, dh, is_editable):
        dh = dh or [1900, 1, 1, 1, 1]
        super().__init__(formats.Affichage.dateheure(dh))


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


## Affiche les coorddonnées des parents
# Utilisé pour surcharger les détails d'un enfant
class InfosParents(QFrame):

    def __init__(self, coord_parents, is_editable):
        super().__init__()
        self.setLayout(QVBoxLayout())
        self.construit(coord_parents)

    def construit(self, coord_parents):
        layout = self.layout()
        for c in coord_parents:
            label_parent, champs = c
            titre = QLabel(label_parent)
            titre.setObjectName("titre-parent")
            titre.setAlignment(Qt.AlignCenter)
            layout.addWidget(titre)
            bloc = QFormLayout()
            for (attr, valeur) in champs:
                label = formats.ASSOCIATION[attr][0]
                w = ASSOCIATION[attr][3](valeur, False)
                bloc.addRow(label, w)
            layout.addLayout(bloc)

    def clear(self):
        clear_layout(self.layout())

    def set_data(self, coord_parents):
        self.clear()
        self.construit(coord_parents)


def Adresse(value, is_editable):
    return Texte(value, is_editable, placeholder="")


class PseudoAccesCategorie(dict):

    def __init__(self, f):
        super().__init__(nom=f)
        self.Id = f


class CategoriesProduitList(MultiSelectList):
    data_changed = pyqtSignal(list)

    def __init__(self, categories, base):
        self.familles = base.produits.familles
        model = modelMultiSelect(sortableListe([PseudoAccesCategorie(f) for f in self.familles]))
        model.ENTETE = ["nom"]
        super().__init__(model)

        self.set_data(categories)
        model.dataChanged.connect(lambda: self.data_changed.emit(self.get_data()))

    def get_data(self):
        return list(self.model().selected_ids)

    def set_data(self, categories):
        categories = categories or []
        self.model().beginResetModel()
        self.model().selected_ids = set(categories)
        self.model().endResetModel()
        self.data_changed.emit(self.get_data())



class CategoriesProduit(QFrame):
    """Ajout d'un champ resumant les catégories sélectionnées"""

    data_changed = pyqtSignal(list)

    def __init__(self, categories, is_editable, base):
        super().__init__()
        categories = categories or []
        self.liste = CategoriesProduitList(categories, base)
        self.liste.data_changed.connect(self.on_change)
        self.resume = QTextBrowser()
        self.resume.setHtml(self._sumup_liste(categories))
        self.resume.anchorClicked.connect(self.delete)
        self.resume.setOpenLinks(False)
        self.resume.setReadOnly(True)
        self.resume.setMinimumSize(300, 150)

        button = QPushButton("Ajouter")
        button.clicked.connect(self.show_popup)
        layout = QVBoxLayout(self)
        layout.addWidget(self.resume)
        layout.addWidget(button)
        self.button = button

    def delete(self, s: QUrl):
        tag = s.toString()
        self.liste.model().set_by_Id(tag, False)

    def show_popup(self):
        popup = QFrame(self)
        popup.setWindowFlags(Qt.Popup)
        layout = QHBoxLayout(popup)
        layout.addWidget(self.liste)
        popup.show()
        g_pos = self.button.mapToGlobal(QPoint(0, 0))
        place = qApp.desktop().availableGeometry()
        popup.setMaximumHeight(place.height() - g_pos.y())
        popup.setMaximumWidth(self.resume.width())
        popup.move(g_pos)


    def _sumup_liste(self, l):
        li = "<br/>".join(f"""<a href='{s}' title="Supprimer"><b>(-)</b> </a>{s}""" for s in sorted(l))
        return li

    def on_change(self, l):
        self.resume.setHtml(self._sumup_liste(l))
        self.data_changed.emit(l)

    def get_data(self):
        return self.liste.get_data()

    def set_data(self, l):
        self.liste.set_data(l)


class abstractCollectionView(abstractList):
    """Crée un modèle interne à partir de l'entête"""

    PLACEHOLDER = None
    VERTICAL_HEADER_VISIBLE = True
    MIN_HEIGHT = 200
    ENTETE = None


    def __init__(self, collection):
        model = modelInterne(collection, self.ENTETE)
        super().__init__(model)
        self.setWordWrap(True)
        self.setTextElideMode(Qt.ElideMiddle)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def get_current_acces(self):
        """Renvoi l'acces sélectionné ou None"""
        l = self.selectedIndexes()
        if len(l) > 0:
            return self.model().get_item(l[0])




class viewListeProduit(abstractCollectionView):
    PLACEHOLDER = "Aucun produit associé"
    ENTETE = ["fou", "c", 'libf', "cond", "gabarit"]


class ChoixQuantite(Fenetre):

    def __init__(self, default_quantite):
        super(ChoixQuantite, self).__init__("Choix de la quantité...")
        choix_q = Quantite(default_quantite, True)
        b = QPushButton("Valider")
        b.setEnabled(False)
        choix_q.data_changed.connect(lambda q: b.setEnabled(bool(q.nombre > 0 and q.unite)))

        def on_valid():
            self.quantite = choix_q.get_data()
            self.accept()

        b.clicked.connect(on_valid)

        self.add_widget(choix_q)
        self.add_widget(b)


class viewListeIngredients(abstractCollectionView):
    PLACEHOLDER = "Aucun ingrédient."
    ENTETE = ["nom", "quantite"]

    def on_double_click(self, index):
        ing = self.model().get_item(index)
        f = ChoixQuantite(ing.quantite)
        if f.exec_():
            ing.quantite = f.quantite
            self.model().set_item(index, ing)



class viewListeRecettes(abstractCollectionView):
    PLACEHOLDER = "Aucune recette."
    ENTETE = ["nom"]


class viewListeProduitsSecondaire(viewListeProduit):
    VERTICAL_HEADER_VISIBLE = False
    PLACEHOLDER = "Cliquez sur Recherche pour trouver des produits pertinents..."


class CadreListeSecondaireProduits(CadreView):
    acces: Optional[Core.acces.Ingredient]

    def __init__(self, acces, titre=ASSOCIATION["liste_secondaire"][0]):
        super().__init__(viewListeProduitsSecondaire(sortableListe()), titre)
        self.acces = acces

    def recherche(self, with_prix=False):
        self.view.model().set_collection(sortableListe())
        self.view.PLACEHOLDER = "Recherche en cours..."
        self.view.repaint()
        l = self.acces.liste_secondaire(with_prix)
        self.view.PLACEHOLDER = "Aucun produit trouvé. \n Conseil : Ajouter des catégories à l'ingrédient"
        self.view.model().set_collection(l)

    def widget_haut_droit(self):
        bar = QToolBar()
        bar.addAction(SearchIcon(), "Recherche", self.recherche).setToolTip("Rechercher des produits possibles")
        return bar




class abstractAddableCollectionView(QFrame):
    data_changed = pyqtSignal(list)

    VIEW = None
    BOUTON = None
    ACCES = None

    def __init__(self, collection, is_editable, base):
        super().__init__()
        collection = sortableListe() if collection is None else collection
        self.view = self.VIEW(collection)
        self.view.model().modelReset.connect(lambda: self.data_changed.emit(self.get_data()))
        self.view.model().dataChanged.connect(lambda: self.data_changed.emit(self.get_data()))
        self.base = base

        add_button = self.BOUTON(base)
        add_button.data_changed.connect(self.on_add)

        layout = QVBoxLayout(self)
        layout.addWidget(self.view)
        layout.addWidget(add_button)

    def on_add(self, Id):
        acces = self.ACCES(self.base, Id)
        self.view.model().beginResetModel()
        self.view.model().collection.append(acces)
        self.view.model().endResetModel()

    def set_data(self, collection):
        self.view.model().set_collection(collection)

    def get_data(self):
        return self.view.model().collection


class ListePrincipaleProduits(abstractAddableCollectionView):
    VIEW = viewListeProduit
    BOUTON = BoutonAjoutIdProduit
    ACCES = acces.Produit



class ListeIngredients(abstractAddableCollectionView):
    VIEW = viewListeIngredients
    BOUTON = BoutonAjoutIdIngredient
    ACCES = acces.Ingredient

    def __init__(self, collection, base, widget_nb_personnes):
        super().__init__(collection, True, base)
        if widget_nb_personnes is not None:
            widget_nb_personnes.data_changed.connect(self.on_nb_personnes_change)
        self.widget_nb_personnes = widget_nb_personnes

    def on_nb_personnes_change(self, nb):
        self.view.model().beginResetModel()
        self.view.model().collection.set_nb_personnes(nb)
        self.view.model().endResetModel()

    def on_add(self, Id):
        """Demande la quantité"""
        if self.widget_nb_personnes is not None:
            nb_pers_default = self.widget_nb_personnes.get_data()
        else:
            nb_pers_default = None
        default_quantite = Core.formats.Quantite(nb_personnes=nb_pers_default)
        f = ChoixQuantite(default_quantite)
        if f.exec_():
            q = f.quantite

            acces = self.ACCES(self.base, Id, quantite=q)
            try:
                self.view.model().beginResetModel()
                self.view.model().collection.append(acces)
                self.view.model().endResetModel()
            except ValueError as e:
                Avertissement(str(e))



class ListeRecettes(abstractAddableCollectionView):
    VIEW = viewListeRecettes
    BOUTON = BoutonAjoutIdRecette
    ACCES = acces.Recette


