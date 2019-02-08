# coding: utf-8
from typing import List, Tuple

from PyQt5.QtCore import Qt, pyqtSignal, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QFont, QBrush, QPaintEvent, QPainter
from PyQt5.QtWidgets import QAbstractItemView, QTableView, \
    QAbstractScrollArea, QFrame, QLabel, QGridLayout, QLineEdit, QPushButton, QHeaderView, QVBoxLayout, QSizePolicy

from pyDLib.Core.groups import sortableListe
from . import Color, PARAMETERS, fenetres, Icons
from ..Core import formats, groups, data_model, controller

MIN_CHAR_SEARCH = data_model.MIN_CHAR_SEARCH

def _custom_font(is_bold=False, is_italic=False):
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
            if attribut is None:
                return
            if role == Qt.DisplayRole:
                return formats.ASSOCIATION[attribut][0]
            elif role == Qt.DecorationRole:
                if section == sort_state[0]:
                    return Icons.ArrowUp if sort_state[1] else Icons.ArrowDown
            elif role == Qt.TextAlignmentRole:
                return Qt.AlignCenter
            elif role == Qt.FontRole:
                return _custom_font(is_bold=True)
        elif orientation == Qt.Vertical:
            if role == Qt.DecorationRole:
                return Icons.Delete.as_icon()
            elif role == Qt.ToolTipRole:
                return Renderer.SUPPRESS_TOOLTIP

    @staticmethod
    def data(attribut, value, info, role):
        if role == Qt.DisplayRole:
            if attribut is None:
                return formats.abstractRender.default(value)
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
            couleurs = PARAMETERS["OPTIONS"]["level_colors"]
            niveau = min(niveau, len(couleurs) - 1)
            color = couleurs[niveau]
            return QBrush(Color(color))
        elif role == Qt.BackgroundRole:
            sexe = info.get("sexe", None)
            couleur = PARAMETERS["OPTIONS"]["sexe_color"][sexe] if sexe else "transparent"
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

    header: List
    sort_state: Tuple
    collection: groups.sortableListe

    def __init__(self, header):
        super().__init__()
        self.header = header
        self.sort_state = (-1, False)

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self.collection)

    def columnCount(self, parent=None, *args, **kwargs):
        return len(self.header)

    def _acces_data(self, acces, attr):
        return acces[attr] if attr is not None else acces

    def data(self, index: QModelIndex, role=None):
        acces, attr = self.collection[index.row()], self.header[index.column()]
        value = self._acces_data(acces, attr)
        info = self.collection.get_info(key=index.row())
        return self.RENDERER.data(attr, value, info, role)

    def headerData(self, section: int, orientation: Qt.Orientation, role=None):
        attribut = (orientation == Qt.Horizontal) and self.header[section] or None
        return self.RENDERER.headerData(section, orientation, role, attribut, self.sort_state)

    def flags(self, index: QModelIndex):
        """All fields are selectable"""
        if self.IS_EDITABLE and self.header[index.column()] in self.EDITABLE_FIELDS:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        else:
            return super().flags(index) | Qt.ItemIsSelectable

    def sort(self, section: int, order=None):
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

    # TODO: Enhance remove line
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
        try:
            return self.collection[row]
        except IndexError: #invalid index for exemple
            return None

    def set_collection(self, collection):
        """Reset sort state, set collection and emit resetModel signal"""
        self.beginResetModel()
        self.collection = collection
        self.sort_state = (-1, False)
        self.endResetModel()


class InternalDataModel(abstractModel):
    """This model stores the data by itself : the data shouldn't be modified from outside.
    If header is None, directly acces item data.
    """

    def __init__(self, collection: groups.sortableListe, header: List):
        header = header if header is not None else [None]
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
        acces, field = self.get_item(index), self.header[index.column()]
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

    def data(self, index: QModelIndex, role=None):
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

    def setData(self, index: QModelIndex, value, role=None):
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
    MIN_WIDTH = 40
    MAX_HEIGHT = None
    MAX_WIDTH = None

    VERTICAL_HEADER_VISIBLE = False

    SELECTION_BEHAVIOR = QAbstractItemView.SelectRows
    SELECTION_MODE = QAbstractItemView.SingleSelection

    DELEGATE_CLASS = None
    """If given, use this class as delegate"""

    RESIZE_COLUMN = False
    """Whe usin delegate, if this is true, resize columns on edit."""

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
        self.setMinimumSize(self.MIN_WIDTH,self.MIN_HEIGHT)
        if self.MAX_HEIGHT:
            self.setMaximumHeight(self.MAX_HEIGHT)
        if self.MAX_WIDTH:
            self.setMaximumWidth(self.MAX_WIDTH)

        self.setEditTriggers(QTableView.DoubleClicked)

        if self.DELEGATE_CLASS is not None:
            self._setup_delegate()

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.on_right_click)

    def _setup_delegate(self):
        """Add resize behavior on edit"""
        delegate = self.DELEGATE_CLASS(self)
        self.setItemDelegate(delegate)
        delegate.sizeHintChanged.connect(lambda index: self.resizeRowToContents(index.row()))
        if self.RESIZE_COLUMN:
            delegate.sizeHintChanged.connect(lambda index: self.resizeColumnToContents(index.column()))
        delegate.closeEditor.connect(lambda ed: self.resizeRowToContents(delegate.row_done_))

    def model(self) -> abstractModel:
        return super(abstractList, self).model()

    def _draw_placeholder(self):
        """To be used in QTreeView"""
        if self.model().rowCount() == 0:
            painter = QPainter(self.viewport())
            painter.setFont(_custom_font(is_italic=True))
            painter.drawText(self.rect().adjusted(0, 0, -5, -5), Qt.AlignCenter | Qt.TextWordWrap,
                             self.PLACEHOLDER)

    def paintEvent(self, paintevent: QPaintEvent):
        """Displays placeholder in case of empty collection"""
        super().paintEvent(paintevent)
        self._draw_placeholder()

    def on_sort(self, i):
        self.sortByColumn(i, 0)
        self.resizeColumnToContents(i)

    def on_click(self, index):
        pass

    def on_right_click(self, pos):
        pass

    def on_double_click(self, index):
        pass

    def on_click_header_vertical(self, section):
        """Default implementation removes the line"""
        self.model().remove_line(section)

    def get_current_item(self):
        """Returns (first) selected item or None"""
        l = self.selectedIndexes()
        if len(l) > 0:
            return self.model().get_item(l[0])

    def search(self,pattern):
        """Intented for main list, which should use interface search"""
        raise NotImplementedError


class MultiSelectList(abstractList):
    """Add data_changed signal, and get_data, set_data methods"""

    data_changed = pyqtSignal(list)
    """Emitted on change of selected Ids"""

    @staticmethod
    def model_from_list(l, header):
        """Return a model with a collection from a list of entry"""
        col = groups.sortableListe(PseudoAccesCategorie(n) for n in l)
        return MultiSelectModel(col, header)


    def model(self) -> MultiSelectModel:
        return super(MultiSelectList, self).model()

    def __init__(self, model: MultiSelectModel):
        super().__init__(model)
        model.dataChanged.connect(lambda : self.data_changed.emit(self.get_data()))
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
    """Emitted on selection"""

    def __init__(self, entete, placeholder=None):
        model = InternalDataModel(sortableListe(), entete)
        super().__init__(model)
        if placeholder is not None:
            self.PLACEHOLDER = placeholder

        self.setMouseTracking(True)  # Lines highlight
        self.setProperty("highlight", True)

    def on_click(self, index):
        acces = self.model().get_item(index)
        self.selected.emit(acces)


class SimpleList(abstractList):
    """Uses an InternelDataModel.
    If header is None, doesn't show header, set only one column, and acces data directly at item.
    Warging : with two many items, if RESIZE_TO_CONTENTS may be slow !
    """

    SHOW_GRID = False
    RESIZE_TO_CONTENTS = True

    def __init__(self, liste, header):
        model = InternalDataModel(liste, header)
        super().__init__(model)
        self.setShowGrid(self.SHOW_GRID)
        self.horizontalHeader().setVisible(header is not None)
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if self.RESIZE_TO_CONTENTS:
            self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.setWordWrap(True)
        self.setTextElideMode(Qt.ElideMiddle)


class abstractMainList(abstractList):
    """Visualize main collections. Use an ExternalDataModel."""

    ENTETE = []

    interface: controller.abstractInterface

    def __init__(self, interface):
        self.interface = interface
        model = self.cree_model()
        super().__init__(model)
        self.interface.add_update_function(self.model()._update)
        self.interface.add_reset_function(self.model()._reset)

    def cree_model(self):
        model = ExternalDataModel(self.get_collection, self.set_data, self.ENTETE)
        return model

    def get_collection(self) -> groups.Collection:
        return groups.Collection()

    def set_data(self, acces, attribut, value):
        raise NotImplementedError

    def select_by_id(self, Id):
        try:
            row_index = self.get_collection().index_from_id(Id)
        except ValueError:
            return
        self.selectRow(row_index)
        self.on_click(self.model().index(row_index, 0))



## -------------  Id search widgets  ------------- ##

class abstractAccesId(fenetres.Window):
    """Takes a search function, which performs Id search.
    If user selects a result, the window is closed, and an Core.data_model.abstractAcces is
    stored in return_value attribute.
    """

    WINDOW_TITLE = "Search"

    LIST_ENTETE = []
    LIST_PLACEHOLDER = "No items found."

    SEARCH_PLACEHOLDER = f"Please type at least {MIN_CHAR_SEARCH} characters..."

    return_value: data_model.abstractAcces

    def __init__(self, search_hook):
        super().__init__(self.WINDOW_TITLE)
        self.return_value = None
        self.search_hook = search_hook

        self.entry = QLineEdit()
        self.entry.setPlaceholderText(self.SEARCH_PLACEHOLDER)

        self.choices_view = SearchList(self.LIST_ENTETE, placeholder=self.LIST_PLACEHOLDER)

        self.entry.textChanged.connect(self.on_search)  # On search

        self.choices_view.selected.connect(self.on_done)  # On click on result

        self.add_widget(self.entry)
        self.add_widget(self.choices_view)

    def on_search(self, pattern):
        collection = self.search_hook(pattern)
        self.choices_view.model().set_collection(collection)

    def on_done(self, acces):
        self.return_value = acces
        self.accept()


class abstractBaseAccesId(abstractAccesId):
    """Use the method given SEARCH_FUNCTION_NAME of Core.data_model.abstractBase object"""

    SEARCH_FUNCTION_NAME = ""

    def __init__(self, base):
        search_hook = getattr(base, self.SEARCH_FUNCTION_NAME)
        super(abstractBaseAccesId, self).__init__(search_hook)


class abstractBoutonAccesId(QPushButton):
    """Button given acces to search window"""

    data_changed = pyqtSignal(object)

    WINDOW = None
    """Search window class, inherits abstractBaseAccesId."""

    PLACEHOLDER = "Add..."

    AS_ACCES = False
    """If true, returns and emit an acces object instead of an Id"""

    acces: data_model.abstractAcces

    @staticmethod
    def format_acces_from_field(field, acces):
        """Display given field of acces.
        Field must be registered in formats.ASSOCIATION.
        """
        return formats.ASSOCIATION[field][2](acces[field])

    def __init__(self, is_editable, base):
        super().__init__(self.PLACEHOLDER)
        self.setEnabled(is_editable)
        self.base = base
        self.clicked.connect(self.on_click)
        self.acces = None

    def on_click(self):
        fen = self.WINDOW(self.base)
        if fen.exec_():
            self.acces = fen.return_value
            self.set_label()
            self.data_changed.emit(self.get_data())

    def _format_acces(self, acces):
        """Might use format_acces_from_field"""
        raise NotImplementedError

    def _acces_from_id(self, id):
        raise NotImplementedError

    def set_label(self):
        label = self._format_acces(self.acces)
        self.setText(label)

    def get_data(self):
        if self.AS_ACCES:
            return self.acces
        if self.acces is None:
            return None
        return self.acces.Id

    def set_data(self, Id):
        acces = self._acces_from_id(Id)
        self.acces = acces
        self.set_label()


### ------------------ Misc ------------------ ###

class SearchField(QLineEdit):
    """Lineedit + reset button.
    Uses search_hook to actually performs the search. Calls it with None to reset.
    """
    def __init__(self,search_hook,placeholder = "Search...",tooltip= "Reset"):
        super(SearchField, self).__init__()
        self.setPlaceholderText(placeholder)
        self.setClearButtonEnabled(True)
        self.textChanged.connect(lambda s : search_hook(s or None))


class CadreView(QFrame):
    """Add controls on view"""

    view: abstractList

    def __init__(self, view, titre):
        super().__init__()
        self.view = view

        label = QLabel(titre)
        label.setObjectName("list-view-title")
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
        """Should return control widgets"""
        return

    def get_search_field(self,**kwargs):
        return SearchField(self.view.search,**kwargs)

    def set_title(self, t):
        self.label.setText(t)


class PseudoAccesCategorie(dict):

    def __init__(self, f):
        super().__init__(nom=f)
        self.Id = f

    def __str__(self):
        return self.Id


class abstractMutableList(QFrame):
    """Provides a view and acces to add or remove and element."""

    data_changed = pyqtSignal(list)

    LIST_PLACEHOLDER = "No items."
    LIST_HEADER = []
    BOUTON = None

    @staticmethod
    def from_list(liste):
        return sortableListe(PseudoAccesCategorie(i) for i in (liste or ()))

    def __init__(self, collection, is_editable, *button_args):
        super().__init__()
        collection = sortableListe() if collection is None else collection
        self.view = self._create_view(collection, is_editable)
        self.view.model().modelReset.connect(lambda: self.data_changed.emit(self.get_data()))
        self.view.model().dataChanged.connect(lambda: self.data_changed.emit(self.get_data()))

        add_button = self.BOUTON(is_editable, *button_args)
        add_button.data_changed.connect(self.on_add)
        self.add_button = add_button

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        layout.addWidget(self.view)
        if is_editable:
            layout.addWidget(add_button)

    def _create_view(self, collection, is_editable):
        v = SimpleList(collection, self.LIST_HEADER)
        v.PLACEHOLDER = self.LIST_PLACEHOLDER
        v.verticalHeader().setVisible(is_editable)
        return v

    def on_add(self, item):
        self.view.model().beginResetModel()
        self.view.model().collection.append(item)
        self.view.model().endResetModel()

    def set_data(self, collection):
        self.view.model().set_collection(collection)

    def get_data(self):
        return self.view.model().collection

