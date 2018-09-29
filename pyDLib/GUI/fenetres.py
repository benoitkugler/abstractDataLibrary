"""Implements severals windows """
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QPushButton, QDialog, QVBoxLayout

from . import AppIcon, PARAMETERS


class abstractDialog(QMessageBox):

    ICON = QMessageBox.Warning
    TITLE = None

    def __init__(self,text="",details=""):
        super(abstractDialog, self).__init__()
        if self.TITLE:
            self.setWindowTitle(self.TITLE)
        self.setIcon(self.ICON)
        self.setText(text)
        if details:
            self.setInformativeText(details)

        self.return_value = None



#

class FatalError(abstractDialog):

    ICON = QMessageBox.Critical
    TITLE = "Erreur"

    def __init__(self, text,details):
        abstractDialog.__init__(self,text=text,details=details)
        self.addButton(QPushButton("Quitter"), QMessageBox.NoRole)
        self.setDefaultButton(QMessageBox.No)
        self.exec_()

class WarningBox(abstractDialog):

    ICON = QMessageBox.Warning
    TITLE = "Avertissement"

    def __init__(self, message):
        super(WarningBox, self).__init__(text=message)
        self.return_value = self.exec_()


class MultiChoiceDialog(abstractDialog):

    def __init__(self,message,yes_label,no_label,other_label=None,action_button=None,details=""):
        super(MultiChoiceDialog, self).__init__(text=message,details=details)
        yesb = self.addButton(yes_label, QMessageBox.YesRole)
        nob = self.addButton(no_label, QMessageBox.NoRole)
        autreb = None
        if other_label:
            autreb = self.addButton(other_label, QMessageBox.DestructiveRole)
        if action_button:
            self.addButton(action_button, QMessageBox.ActionRole)
        self.setDefaultButton(QMessageBox.No)
        self.exec_()
        if self.clickedButton() == yesb:
            self.return_value = True
        elif self.clickedButton() == nob:
            self.return_value = False
        elif self.clickedButton() == autreb:
            self.return_value = 2


class LoadingError(MultiChoiceDialog):

    ICON = QMessageBox.Warning

    def __init__(self):
        text = "Erreur de chargement de la base de données"
        details = """
        Il est conseillé de vérifier la connexion internet et de relancer l'application.<br/>
        Sinon, vous pouvez continuer en mode <b>hors connexion</b>.
        </i>Vous ne pourrez qu'accéder aux données déjà présente sur votre ordinateur, et aucun changement ne sera enregistré sur la base en ligne.</i>"""
        super(LoadingError, self).__init__(text, "Continuer hors-connexion",
                                           "Quitter", other_label="Mettre à jour et quitter",
                                           details=details)



class Confirmation(MultiChoiceDialog):

    ICON = QMessageBox.Question
    TITLE = "Confirmation"

    def __init__(self, message, yes="Confirmer", no="Annuler",**kwargs):
        super(Confirmation, self).__init__(message, yes, no, **kwargs)



class Window(QDialog):
    """Standalone window, with icon and style sheet."""

    def __init__(self, titre, parent=None, **kwargs):
        no_flags = kwargs.pop("no_flags", False)
        QDialog.__init__(self, parent, **kwargs)
        self.setWindowTitle(titre)
        self.setWindowIcon(AppIcon())
        if not no_flags:
            self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)

        style = PARAMETERS["WIDGETS_STYLE"]
        self.setStyleSheet(style)


    def add_widget(self, w):
        """Convenience function"""
        if self.layout():
            self.layout().addWidget(w)
        else:
            layout = QVBoxLayout(self)
            layout.addWidget(w)
