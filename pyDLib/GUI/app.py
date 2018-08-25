"""Defines main application object.
Starting of the programm should be controlled by a launcher script
"""
import logging
import os

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtWidgets import (QMainWindow, QToolBar, QStackedWidget, QTabWidget, qApp, QShortcut,
                             QLabel, QCheckBox, QPushButton, QFormLayout, QVBoxLayout, QLineEdit)

from . import common, load_options, IMAGES_PATH
from ..Core import StructureError, ConnexionError, load_changelog, controller, load_credences, CREDENCES
from . import PARAMETERS, AppIcon
from .fenetres import Window, WarningBox


def init_version(v):
    global APP_VERSION
    APP_VERSION = v



class Application(QMainWindow):
    theory_main: controller.abstractInterInterfaces

    WINDOW_TITLE = "abstract Data App"

    def __init__(self, theory_main):
        super().__init__()
        self.theory_main = theory_main
        self.no_load = False

        self.initUI()
        self.init_shortcuts()


    def initUI(self):
        self.toolbar = None
        w = QStackedWidget()
        w.setObjectName('block-principal')
        self.setCentralWidget(w)
        style = PARAMETERS["MAIN_STYLE"] + PARAMETERS["WIDGETS_STYLE"] + PARAMETERS["TABS_STYLE"]
        self.centralWidget().setStyleSheet(style)
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setWindowIcon(AppIcon)
        self.move(200, 200)

    def init_shortcuts(self):
        seq2 = QKeySequence(Qt.SHIFT + Qt.ALT + Qt.Key_V)
        hidden_shortcut2 = QShortcut(seq2, self)
        hidden_shortcut2.activated.connect(self.show_version)

    def init_tabs(self):
        self.theory_main.load_modules()

        tb = SideToolBar(self)
        self.set_toolbar(tb)

        self.tabs = MainTabs(self.theory_main, self.statusBar())
        self.tabs.interface_changed.connect(tb.set_interface)

        tb.set_interface(self.theory_main.interfaces[self.tabs.index_interfaces[0]])

        self.centralWidget().addWidget(self.tabs)
        self.centralWidget().setCurrentIndex(1)
        self.showMaximized()

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
            self.main_abstrait.update_credences(url)
            if with_config:
                self.progress_bar = common.LoadingMonitor("Configuration", self)
                self.progress_bar.setLabel("Mise à jour des fichiers de configuration...")
                load_credences()
                self.main_abstrait.update_configuration(self.progress_bar.monitor)
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
        f = Window("Version")
        label = "<p>Version {} </p>".format(APP_VERSION)
        label += load_changelog()
        l = QLabel(label)
        l.setTextFormat(Qt.RichText)
        f.add_widget(l)
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
        infos = "Adresse de chargement de la base : {} <br/>".format(CREDENCES["FILES_URL"]["db"])
        infos += "Nom de la base en accès direct : {} <br/>".format(CREDENCES["DB"]['name'])
        try:
            url = CREDENCES["FILES_URL"]["credences"]
        except (KeyError,TypeError):
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


class SideToolBar(QToolBar):
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

        except KeyError:
            chemin = 'default.png'
        chemin =  os.path.join(IMAGES_PATH,chemin)
        return QIcon(chemin

    def set_boutons_communs(self):
        self.addAction(self.get_icon("reload_css"), "Actualiser le CSS", self.main_appli.reload_css)
        self.addAction(self.get_icon("export_base"), "Exporter", self.main_appli.export_base).setToolTip(
            "Exporter les données et les préférences...")
        self.addAction(self.get_icon("import_base"), "Importer", self.main_appli.import_base).setToolTip(
            "Importer les données et les préférences...")

    ## Affiche les boutons correpondant à la liste de tuple (id,fonction,descriptions,actif), avec l'icône définie par ICONES
    # Attention au loader. Il est détruit si l'interface update_entry !
    def set_boutons_interface(self, l_fonctions):
        for i in l_fonctions:
            id_action, f, d, is_active, *with_loader = i  # loader ignoré
            icon = self.get_icon(id_action)
            action = self.addAction(icon, d)
            action.setEnabled(is_active)
            action.triggered.connect(f)

    def set_interface(self, interface):
        self.interface = interface
        self.interface.callbacks.update_toolbar = self._update
        self._update()

    # Met à jour les bouttons suivant les actions données par l'interface
    def _update(self):
        self.clear()
        self.set_boutons_communs()
        if self.interface:
            self.addSeparator()
            l_actions = self.interface.get_actions_toolbar()
            self.set_boutons_interface(l_actions)


## Partie principale regroupant les modules disponibles pour l'utilisateur.
# Implément les divers Onglets, en fonction du dictionnaire de modules donné en argument
# Chaque module est constitué d'une interface abstraite et d'une classe la prenant en référence
#
class MainTabs(QTabWidget):
    ##Pour communiquer avec la barre d'outils
    interface_changed = pyqtSignal(Core.interfaces.abstractInterface)

    ## Correspondance entre id des modules et  classes. L'interface doit avoir le même nom que l'id.
    Id_to_Classes = {
        "produits": (GUI.Onglets.produits.Produits, " Produits "),
        "recettes": (GUI.Onglets.recettes.Recettes, " Recettes "),
        "menus": (GUI.Onglets.menus.Menus, " Menus ")
    }

    def __init__(self, main_abstrait, status_bar):
        super().__init__()
        self.interfaces = main_abstrait.interfaces
        self.setObjectName("cadre-principal-onglets")
        self.tabBar().setObjectName("barre-onglets")

        self.currentChanged.connect(lambda i: self.interface_changed.emit(self.interfaces[self.index_interfaces[i]]))

        self.index_interfaces = []
        print("Chargement des modules suivants : ", self.interfaces.keys())

        for mod in sorted(self.interfaces.keys()):
            i = self.interfaces[mod]
            classe, label = MainTabs.Id_to_Classes[mod]
            self.index_interfaces.append(mod)
            onglet = classe(status_bar, i)
            self.addTab(onglet, label)
