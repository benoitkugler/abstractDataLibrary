"""Implements severals windows """
from PyQt5.QtWidgets import QMessageBox, QPushButton, QDialog, QVBoxLayout

from . import AppIcon, PARAMETERS

# TODO : implements dialog box
# class ChargementError(QMessageBox):
#
#     def __init__(self):
#         QMessageBox.__init__(self)
#         self.setIcon(QMessageBox.Warning)
#         self.setText("Erreur de chargement de la base de données")
#
#         self.setInformativeText("""
#         Il est conseillé de vérifier la connexion internet et de relancer l'application.<br/>
#         Sinon, vous pouvez continuer en mode <b>hors connexion</b>.
#         </i>Vous ne pourrez qu'accéder aux données déjà présente sur votre ordinateur, et aucun changement ne sera enregistré sur la base en ligne.</i>""")
#
#         yesb = self.addButton("Continuer hors-connexion", QMessageBox.YesRole)
#         nob = self.addButton("Quitter", QMessageBox.NoRole)
#         autreb = self.addButton("Mettre à jour et quitter", QMessageBox.DestructiveRole)
#         self.setDefaultButton(QMessageBox.No)
#         self.exec_()
#         if self.clickedButton() == yesb:
#             self.return_value = True
#         elif self.clickedButton() == nob:
#             self.return_value = False
#         elif self.clickedButton() == autreb:
#             self.return_value = 2
#
#
# class FatalError(QMessageBox):
#
#     def __init__(self, details):
#         QMessageBox.__init__(self)
#         self.setIcon(QMessageBox.Critical)
#         self.setText("Erreur de chargement !")
#
#         self.setInformativeText(details)
#         self.addButton(QPushButton("Quitter"), QMessageBox.NoRole)
#
#         self.setDefaultButton(QMessageBox.No)
#         self.return_value = self.exec_()
#
#
# class Avertissement(QMessageBox):
#
#     def __init__(self, message):
#         QMessageBox.__init__(self)
#         self.setIcon(QMessageBox.Warning)
#         self.setText(message)
#         self.exec_()
#
#
# class Confirmation(QMessageBox):
#
#     def __init__(self, message, yes="Confirmer", no="Annuler", info="", autre_bouton=None, push_button=None):
#         super().__init__()
#         self.setWindowTitle("Confirmation")
#         self.setIcon(QMessageBox.Question)
#         self.setText(message)
#         self.setInformativeText(info)
#         yesb = self.addButton(yes, QMessageBox.YesRole)
#         nob = self.addButton(no, QMessageBox.NoRole)
#         if autre_bouton:
#             autreb = self.addButton(autre_bouton, QMessageBox.DestructiveRole)
#         if push_button:
#             self.addButton(push_button, QMessageBox.ActionRole)
#         self.setDefaultButton(QMessageBox.No)
#         self.exec_()
#         if self.clickedButton() == yesb:
#             self.return_value = True
#         elif self.clickedButton() == nob:
#             self.return_value = False
#         elif self.clickedButton() == autreb:
#             self.return_value = 2



class Window(QDialog):
    """Standalone window, with icon and style sheet."""

    def __init__(self, titre, parent=None, **kwargs):
        QDialog.__init__(self, parent, **kwargs)
        self.setWindowTitle(titre)
        self.setWindowIcon(AppIcon())

        style = PARAMETERS["WIDGETS_STYLE"] + PARAMETERS["TABS_STYLE"]
        self.setStyleSheet(style)


    def add_widget(self, w):
        """Convenience function"""
        if self.layout():
            self.layout().addWidget(w)
        else:
            layout = QVBoxLayout(self)
            layout.addWidget(w)
