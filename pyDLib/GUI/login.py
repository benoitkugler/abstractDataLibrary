"""Implements login screen at app startup"""
import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QFrame, QSizePolicy,
                             QLabel, QPushButton, QLineEdit, QCheckBox,
                             QStackedWidget, QHBoxLayout, QVBoxLayout, QGridLayout)

from . import UserAvatar, SuperUserAvatar, fenetres, Icons
from ..Core import StructureError, ConnexionError


def _get_visuals(user):
    """
    Renvoi les éléments graphiques d'un utilisateur.

    :param user: Dictionnaire d'infos de l'utilisateur
    :return QPixmap,QLabel: Image et nom
    """
    pixmap = SuperUserAvatar() if user["status"] == "admin" else UserAvatar()
    label = user["label"]
    return pixmap, QLabel(label)


def _get_label(message):
    b = QLabel(message)
    b.setAlignment(Qt.AlignCenter)
    b.setObjectName('login-main-title')
    return b


class UserLogo(QFrame):
    """Clickable profile"""

    clicked = pyqtSignal()

    def __init__(self, user, enabled=True):
        """
        Create profile widget from user informations dict.
        """
        super().__init__()
        self.setObjectName("user-profile")
        self.enabled = enabled
        self.setProperty("follow-mouse", enabled)

        image, label = _get_visuals(user)

        grid = QGridLayout(self)
        i = QLabel()
        i.setPixmap(image)
        i.setAlignment(Qt.AlignCenter)

        text = label
        text.setAlignment(Qt.AlignCenter)

        grid.addWidget(i, 0, 0)
        grid.addWidget(text, 1, 0)

    def mouseReleaseEvent(self, event):
        if self.enabled:
            self.setProperty('state', False)
            self.setStyle(self.style())
            self.clicked.emit()

    def mousePressEvent(self, event):
        if self.enabled:
            self.setProperty('state', True)
            self.setStyle(self.style())


class UserForm(QFrame):
    """Login form."""

    validated = pyqtSignal(str, str, bool)
    """ Emit (`id_user`,`mdp`,`autolog`)"""

    canceled = pyqtSignal()

    def __init__(self, user):
        super().__init__()
        self.setObjectName("login-form")
        self.user = user
        self.loader = None

        self.entree = QLineEdit()
        self.entree.returnPressed.connect(self.on_valid)
        self.entree.setFocus()

        self.retour_mdp = QLabel("")
        self.retour_mdp.setObjectName("password-flash")
        self.retour_mdp.setAlignment(Qt.AlignCenter)

        self.autolog = QCheckBox("Se connecter automatiquement")

        self.button_valid = QPushButton("Démarrer")
        self.button_valid.setObjectName("round")
        self.button_valid.clicked.connect(self.on_valid)

        retour = QPushButton()
        retour.setIcon(QIcon(Icons.Back))
        retour.setToolTip("Retour à la liste des utilisateurs")
        retour.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        retour.clicked.connect(self.canceled.emit)

        autobox = QHBoxLayout()
        autobox.addStretch()
        autobox.addWidget(self.autolog)
        autobox.addStretch()

        grid = QGridLayout()
        grid.addWidget(QLabel("Mot de passe :"), 0, 0)
        grid.addWidget(self.entree, 0, 1)
        grid.addWidget(self.retour_mdp, 2, 0, 1, 2)
        grid.addLayout(autobox, 1, 0, 1, 2)

        form_layout = QVBoxLayout()
        form_layout.addWidget(_get_label("Connexion"))
        form_layout.addStretch()
        form_layout.addLayout(grid)
        form_layout.addStretch()
        form_layout.addWidget(self.button_valid)

        final = QHBoxLayout(self)
        final.addWidget(retour)
        final.addWidget(UserLogo(self.user, False))
        final.addLayout(form_layout)

    def on_valid(self):
        mdp = self.entree.text()
        autolog = self.autolog.isChecked()
        id_user = self.user["id"]
        # Animation de transition
        self.button_valid.setText("Vérification du mot de passe...")
        self.button_valid.repaint()
        self.validated.emit(id_user, mdp, autolog)

    def show_mdp_invalide(self):
        self.retour_mdp.setText("Le mot de passe est incorrect.")
        self.button_valid.setText("Démarrer")
        self.entree.clear()
        self.entree.setFocus()

    def simule_input(self, mdp, autolog):
        self.entree.setText(mdp)
        self.autolog.setChecked(autolog)
        self.on_valid()

    def focus(self):
        self.entree.setFocus()


class EcranConnexion(QFrame):
    """Wrapper for profiles and loggin form"""

    user_selected = pyqtSignal(str)
    """ Emit user id"""

    def __init__(self, theory_main):
        super().__init__()
        self.setObjectName("login-users")
        self.theory_main = theory_main

        l_users = self.get_users()

        b = _get_label("Bienvenue")

        grid = QVBoxLayout(self)
        grid.addWidget(b)
        grid.addStretch()
        grid.addWidget(l_users)
        grid.addStretch()

    def get_users(self):
        zone = QFrame()
        grid = QHBoxLayout()
        grid.addStretch()
        for i in sorted(self.theory_main.users.keys()):
            u = self.theory_main.users[i]
            logo = UserLogo(u)
            logo.clicked.connect(lambda i=i: self.user_selected.emit(i))
            grid.addWidget(logo)
        grid.addStretch()
        final = QVBoxLayout(zone)
        final.addLayout(grid)
        final.addStretch()
        return zone


class Loading(QStackedWidget):
    """Main widget for login"""

    loaded = pyqtSignal()
    """Ask for launching"""

    canceled = pyqtSignal()
    """Ask for closing"""

    updated = pyqtSignal()
    """ Ask for update"""

    def __init__(self, status_bar, theory_main):
        super().__init__()
        self.status_bar = status_bar
        self.theory_main = theory_main

        self.widget_users = EcranConnexion(self.theory_main)
        self.widget_formulaire = None

        self.widget_users.user_selected.connect(self.on_choice_user)

        self.addWidget(self.widget_users)

    def on_choice_user(self, id_user):
        u = self.theory_main.users[id_user]
        w = self.widget(1)
        if w:
            self.removeWidget(w)
        self.widget_formulaire = UserForm(u)
        self.widget_formulaire.validated.connect(self.on_valid_formulaire)
        self.widget_formulaire.canceled.connect(self.retour)
        self.insertWidget(1, self.widget_formulaire)
        self.setCurrentIndex(1)
        self.widget_formulaire.focus()

        mdp = self.theory_main.has_autolog(id_user)
        if mdp:  # Auto-connection
            self.widget_formulaire.simule_input(mdp, True)

    def on_valid_formulaire(self, id_user, mdp, autolog):
        try:
            r = self.theory_main.loggin(id_user, mdp, autolog)
        except (ConnexionError, StructureError):
            logging.exception("Can't check password !")
            self.propose_load_local()
        else:
            if r:
                self.widget_formulaire.button_valid.setText("Démarrage...")
                self.status_bar.showMessage("Base de données distante chargée avec succès", 3000)
                self.loaded.emit()
            else:
                self.widget_formulaire.show_mdp_invalide()

    def retour(self):
        self.setCurrentIndex(0)

    def propose_load_local(self):
        fen = fenetres.LoadingError()
        if fen.return_value == True:
            try:
                self.theory_main.loggin_local()
            except StructureError as e:
                fenetres.FatalError("Base local introuvable ou corrompue !", details=str(e))
                self.canceled.emit()
            else:
                self.status_bar.showMessage("Base de données locale chargée avec succès.", 3000)
                self.loaded.emit()
        elif fen.return_value == 2:
            self.updated.emit()
        else:
            self.canceled.emit()
