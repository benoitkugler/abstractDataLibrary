"""Defines main application object.
Starting of the programm should be controlled by a launcher script
"""
import json
import logging
import os

from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPoint, QTimer
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import (QMainWindow, QToolBar, QStackedWidget, QTabWidget, qApp, QShortcut,
                             QLabel, QCheckBox, QPushButton, QFormLayout, QLineEdit, QScrollArea, QApplication)

from . import PARAMETERS, AppIcon, Icons
from . import common, load_options, login
from .fenetres import Window, WarningBox
from .. import Core
from ..Core import StructureError, ConnexionError, load_changelog, controller, load_credences


def init_version(v):
    global APP_VERSION
    APP_VERSION = v


class abstractMainTabs(QTabWidget):
    """Modules container"""

    interface_changed = pyqtSignal(controller.abstractInterface)
    popup_asked = pyqtSignal(str, object)

    Id_to_Classes = {}
    """Dict. { module_name : (GUI_module_class , label) }"""

    def __init__(self, theory_main: controller.abstractInterInterfaces, status_bar):
        super().__init__()
        self.interfaces = theory_main.interfaces
        self.setObjectName("main-tabs")
        self.tabBar().setObjectName("main-tabs-bar")

        self.currentChanged.connect(
            lambda i: self.interface_changed.emit(self.get_interface(i)))

        self._index_interfaces = []
        logging.info("Loading of modules : " +
                     ", ".join(self.interfaces.keys()))

        for module_name in sorted(self.interfaces.keys()):
            i = self.interfaces[module_name]
            i.set_callback(
                "grab_focus", lambda m=module_name: self.set_current_interface(m))
            classe, label = self.Id_to_Classes[module_name]
            self._index_interfaces.append(module_name)
            onglet = classe(status_bar, i)
            onglet.popup_asked.connect(self.popup_asked.emit)
            self.addTab(onglet, label)

    def get_interface(self, index):
        return self.interfaces[self._index_interfaces[index]]

    def set_current_interface(self, module_name):
        index = self._index_interfaces.index(module_name)
        self.setCurrentIndex(index)


class abstractToolBar(QToolBar):
    """Main tool bar, constiting in two parts :
        - one is common to all modules
        - one if defined by the current interface"""

    def __init__(self, main_appli):
        super().__init__()
        self.main_appli = main_appli
        self.interface = None

        self.ICONES = PARAMETERS["OPTIONS"]["icones"]
        size = PARAMETERS["OPTIONS"]["toolbar_button_size"]
        self.setIconSize(QSize(size, size))
        self.setMovable(False)
        self._update()

    def get_icon(self, id_action):
        try:
            chemin = self.ICONES[id_action]
            chemin = os.path.join(PARAMETERS["IMAGES_PATH"], chemin)
            return QIcon(chemin)
        except KeyError:
            return Icons.Default

    def _set_boutons_communs(self):
        """Should add actions"""
        pass

    def _set_boutons_interface(self, buttons):
        """Display buttons given by the list of tuples (id,function,description,is_active)"""
        for id_action, f, d, is_active in buttons:
            icon = self.get_icon(id_action)
            action = self.addAction(QIcon(icon), d)
            action.setEnabled(is_active)
            action.triggered.connect(f)

    def set_interface(self, interface):
        """Add update toolbar callback to the interface"""
        self.interface = interface
        self.interface.callbacks.update_toolbar = self._update
        self._update()

    def _update(self):
        """Update the display of button after querying data from interface"""
        self.clear()
        self._set_boutons_communs()
        if self.interface:
            self.addSeparator()
            l_actions = self.interface.get_actions_toolbar()
            self._set_boutons_interface(l_actions)


class Application(QMainWindow):
    theory_main: controller.abstractInterInterfaces
    current_popup: common.Popup

    POPUP_TIMEOUT = 10000
    """Time (in ms) for the popup to fade"""

    WINDOW_TITLE = "abstract Data App"

    TABS_CLASS = abstractMainTabs
    TOOLBAR_CLASS = abstractToolBar

    def __init__(self, theory_main):
        super().__init__()
        self.theory_main = theory_main
        self.no_load = False
        self.current_popup = None

        self._initUI()
        self._init_shortcuts()

        self._set_callbacks()

    def _set_callbacks(self):
        self.theory_main.set_callback(
            "copy_to_clipboard", lambda text: QApplication.clipboard().setText(text))

    def _initUI(self):
        self.toolbar = None
        w = QStackedWidget()
        w.setObjectName('block-principal')
        self.setCentralWidget(w)
        style = PARAMETERS["MAIN_STYLE"] + PARAMETERS["WIDGETS_STYLE"]
        self.setStyleSheet(style)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setWindowIcon(AppIcon())
        self.move(200, 200)

    def _init_shortcuts(self):
        seq2 = QKeySequence(Qt.SHIFT + Qt.ALT + Qt.Key_V)
        hidden_shortcut2 = QShortcut(seq2, self)
        hidden_shortcut2.activated.connect(self.show_version)

    def init_login(self, from_local=False):
        """Display login screen. May ask for local data loading if from_local is True."""
        if self.toolbar:
            self.removeToolBar(self.toolbar)
        widget_login = login.Loading(self.statusBar(), self.theory_main)
        self.centralWidget().addWidget(widget_login)
        widget_login.loaded.connect(self.init_tabs)
        widget_login.canceled.connect(self._quit)
        widget_login.updated.connect(self.on_update_at_launch)
        if from_local:
            widget_login.propose_load_local()
        else:
            self.statusBar().showMessage("Données chargées depuis le serveur.", 5000)

    def init_tabs(self, maximized=True):
        self.theory_main.load_modules()

        tb = self.TOOLBAR_CLASS(self)
        self.set_toolbar(tb)

        self.tabs = self.TABS_CLASS(self.theory_main, self.statusBar())
        self.tabs.interface_changed.connect(tb.set_interface)
        self.tabs.popup_asked.connect(self.show_popup)

        tb.set_interface(
            self.theory_main.interfaces[self.tabs._index_interfaces[0]])

        self.centralWidget().addWidget(self.tabs)
        self.centralWidget().setCurrentIndex(1)

        if maximized:
            self.showMaximized()

    def show_popup(self, text, title):
        if self.current_popup:
            self.current_popup.hide()
        if text:
            self.current_popup = common.Popup(self, text, title)
            QTimer.singleShot(self.POPUP_TIMEOUT, self.current_popup.hide)
            self.current_popup.show()
            self._move_popup()

    def _move_popup(self):
        if self.current_popup is None:
            return
        p_window = QPoint(self.size().width(), self.size().height())
        p_popup = QPoint(self.current_popup.size().width(),
                         self.current_popup.size().height())
        tb_w = self.toolbar.size().width() + 5
        p = self.mapToGlobal(p_window - p_popup - QPoint(tb_w, 0))
        self.current_popup.move(p)

    def resizeEvent(self, event):
        self._move_popup()
        super().resizeEvent(event)

    def moveEvent(self, event):
        self._move_popup()
        super().moveEvent(event)

    def set_toolbar(self, tb):
        if self.toolbar:
            self.removeToolBar(self.toolbar)
        self.addToolBar(Qt.RightToolBarArea, tb)
        self.toolbar = tb

    def _quit(self):
        self.no_load = True
        qApp.quit()

    def start_check_updates(self):
        self.progress_bar = common.LoadingMonitor("Mise à jour", self)
        self.progress_bar.setLabel("Vérification des mises à jour :")

    def reload_css(self):
        load_options()
        style = PARAMETERS["MAIN_STYLE"] + PARAMETERS["WIDGETS_STYLE"]
        self.setStyleSheet(style)
        self.theory_main.reset_interfaces()

    def on_update(self):
        try:
            r = self.show_panel_update()
        except (ConnexionError, StructureError) as e:
            self.statusBar().showMessage("Erreur pendant la mise à jour : {}".format(e), 4000)
            r = None
        if not r:
            return
        self.statusBar().showMessage("Mise à jour réussie", 3000)
        self.progress_bar.accept()
        self.theory_main.init_modules()
        self.reload_css()

    def show_panel_update(self):
        f = UpdateConfiguration()
        f.exec_()
        if f.retour:
            url, with_config = f.retour
            self.theory_main.update_credences(url)
            if with_config:
                self.progress_bar = common.LoadingMonitor(
                    "Configuration", self)
                self.progress_bar.setLabel(
                    "Mise à jour des fichiers de configuration...")
                load_credences()
                self.theory_main.update_configuration(
                    self.progress_bar.monitor)
                self.progress_bar.accept()
                return True

    def on_update_at_launch(self):
        try:
            r = self.show_panel_update()
        except (ConnexionError, StructureError):
            WarningBox("Mise à jour impossible. L'application va s'arrêter.")
            r = None
        if r:
            WarningBox("Mise à jour réussie. L'application va s'arrêter.")
        self._quit()

    def show_version(self):
        f = Window("Notes de version")
        label = f"<h2> Version {APP_VERSION} </h2>"
        label += load_changelog()
        notes = QLabel(label)
        notes.setTextFormat(Qt.RichText)
        scroll = QScrollArea()
        scroll.setStyleSheet("border: none;")
        scroll.setWidget(notes)
        scroll.setMinimumWidth(600)
        scroll.setMinimumHeight(550)
        f.add_widget(scroll)
        f.exec_()


class UpdateConfiguration(Window):

    def __init__(self):
        super().__init__("Mise à jour de la configuration")
        self.retour = None
        s = """
        Bienvenue dans l'utilitaire de <i>gestion de configuration</i>.<br/>
        L'<b>adresse</b> (URL) est celle du serveur où est stocké le fichier de 'crédences'.<br/>
        Les <b>fichiers de configuration</b> influent sur le style de l'interface du logiciel, ainsi que la présentation des documents émis.
        """
        infos = "Adresse de chargement de la base : {} <br/>".format(
            Core.CREDENCES["FILES_URL"]["db"])
        infos += "Nom de la base en accès direct : {} <br/>".format(
            Core.CREDENCES["DB"]['name'])
        details = json.dumps(Core.CREDENCES, indent=2).replace("\n", "<br/>")
        infos += f"Détails : {details}"
        try:
            url = Core.CREDENCES["FILES_URL"]["credences"]
        except (KeyError, TypeError):
            logging.exception("Credences download url not found !")
            url = ""
        self.url = QLineEdit(url)
        self.url.setMinimumWidth(400)
        self.with_config = QCheckBox("Mettre à jour la configuration")
        valid = QPushButton("Mettre à jour")
        valid.clicked.connect(self.on_valid)

        layout = QFormLayout(self)
        layout.addRow(QLabel(s))
        layout.addRow(QLabel(infos))
        layout.addRow("URL", self.url)
        layout.addRow(self.with_config)
        layout.addRow(valid)

    def on_valid(self):
        url = self.url.text()
        with_config = self.with_config.isChecked()
        self.retour = url, with_config
        self.accept()
