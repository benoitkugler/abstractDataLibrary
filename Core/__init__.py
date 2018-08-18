import logging
import os
from datetime import datetime
from zipfile import ZipFile, BadZipFile

from Core import StructureError
from Core.base_locale import Base, Preferences


import Core.threads as threads
from Core import base_locale
from Core.acces import abstractAcces
from Core.collection import *
from Core.formats import ASSOCIATION

## Implémente un objet ayant comme attribut des callback, et un callback par défault si l'attribut cherché n'est pas présent.
class Callbacks:

    def __getattr__(self, key):
        def f(*args):
            print("Il n'y a pas de callback enregistré sous ce nom : " + key)

        return f

class abstractInterface:
    """Implémente le squelette d'une classe gérant la partie abstraite (intelligente) d'un onglet.
# Les fonctions _update et _reset peuvent être appelées à chaque fois que des données sont modifiées.
# Les évènements liés sont gérés par un système de callback. On inscrit un callback, puis on peut le déclencher en appelant la méthode du même nom. Les évènements graphiques indirects peuvent ainsi être pris en charge."""

    ## Classe de l'accés par défautl de l'interface
    ACCES = None
    ## Liste des noms des actions nécessaire à l'interface
    CALLBACKS = []

    """Table par défault pour la construction de la collection principale. (méthode get_all)"""
    TABLE = None

    base: base_locale.BaseLocale

    def __init__(self, main, permission):
        """
        Constructeur.

        :param main: Référence au controlleur abstrait (permet entre autre l'accès à la base locale)
        :param permission: Entier codant les permissions (dépend de chaque module)
        """
        self.main = main
        self.base = main.base
        self.permission = permission

        # Action par défault
        def f(s):
            print(s)

        self.sortie_erreur_GUI = f
        self.sortie_standard_GUI = f
        # Liste d'action à effectuer en cas d'actualisation de l'affichage
        self.updates = []
        self.resets = []

        # Objet contenant les actions nécessaires
        self.callbacks = Callbacks()

        # Liste de threads actifs
        self.threads = []

    def _reset(self):
        for f in self.resets:
            f()
        self.callbacks.update_toolbar()

    def add_reset_function(self, f):
        self.resets.append(f)

    def remove_reset_function(self, f):
        try:
            self.resets.remove(f)
        except ValueError:
            print("La fonction de reset n'était pas enregistrée !")

    def add_update_function(self, f):
        self.updates.append(f)

    def remove_update_function(self, f):
        try:
            self.updates.remove(f)
        except ValueError:
            print("La fonction d'update n'était pas enregistrée !")

    def add_thread(self, th):
        self.threads.append(th)

        def clean():
            self.threads.remove(th)

        th.done.connect(clean)

    ## Execute les fonctions de mise à jour de l'affichage.
    #
    def _update(self):
        for f in self.updates:
            f()
        self.callbacks.update_toolbar()

    ##Renvoie un acces avec l'id demandé
    def get_acces(self, Id) -> abstractAcces:
        return self.ACCES(self.base, Id)

    ## Renvoie la collection générale
    #
    def get_all(self):
        table = getattr(self.base, self.TABLE)
        c = Collection(self.ACCES(self.base, i) for i in table)
        return c

    ## Effectue une recherche sur la collection actuelle et met à jour l'affichage
    # @param text Chaine à rechercher
    # @return Nombre de résultats
    def recherche(self, text, entete):
        self.collection.recherche(text, entete)
        # reset graphique
        for f in self.resets:
            f()
        return len(self.collection)

    ## Exécute une fonction dans un thread séparé
    def lance_job(self, requete, sortie_erreur_GUI=None, sortie_standard_GUI=None):
        sortie_erreur_GUI = sortie_erreur_GUI or self.sortie_erreur_GUI
        sortie_standard_GUI = sortie_standard_GUI or self.sortie_standard_GUI

        def f(r):
            sortie_standard_GUI(r)
            self._update()

        def g(r):
            sortie_erreur_GUI(r)
            self._reset()

        print(self.__class__.__name__, " : Execution d'une tâche...")
        if self.main.mode_online:
            th = threads.worker(requete, g, f)
            self.add_thread(th)
        else:
            self.sortie_erreur_GUI("Mode local actif : pas de modifications à distance")
            self._reset()

    # A implémenter
    def get_labels_stats(self):
        return []

    # A implémenter
    def get_stats(self):
        return []

    ## (A implémenter) Renvoie une liste permettant de construire les bouttons spécifiques à cette interface.
    # Cette fonction est appelée régulièrement pour mettre à jour les informations.
    # Les éléments de la liste sont de la forme (id,function,description,is_actif)
    def get_actions_toolbar(self):
        return []

    @staticmethod
    def filtre(liste_base, criteres):
        """
        Renvoie une liste filtrée en fonction des critères

        :param liste_base: Liste d'accès
        :param criteres: Dictionnaire de critère sous la forme `attribut`:[valeurs,...]
        :return: La liste filtrée
        """

        def choisi(ac):
            for cat, li in criteres.items():
                v = ac[cat] or ASSOCIATION[cat][3]
                if not v in li:
                    return False
            return True

        return [a for a in liste_base if choisi(a)]




class InterInterfaces:
    """
    Classe d'entrée des tâches abstraites.
    Responsable notamment du loggin et du chargement de la base.
    """


    def __init__(self):
        # Création de la base locale
        self.base = Base()

        # Paramètres de chargement
        self.modules = {"produits":2,"recettes":2,"menus":2}

        self.interfaces = {}

        self.preferences = Preferences.from_local_DB()

        self.resets = []
        self.callbacks = Callbacks()

    def set_reset_function(self, f):
        self.resets.append(f)

    def reset_interfaces(self):
        for i in self.interfaces.values():
            i._reset()

    def set_callback(self, name, f):
        setattr(self.callbacks, name, f)

    def load_modules(self):
        for module, permission in self.modules.items():
            i = getattr(Core.interfaces, module).Interface(self, permission)
            self.interfaces[module] = i

    def export_data(self, bases, savedir):
        """Packs and zip asked bases (from base).
        Saves archive in given savepath"""
        date = datetime.today()
        savepath = os.path.join(savedir, f"ACVEintendance{date.day}{date.month}{date.year}.zip")
        with ZipFile(savepath, mode="w") as archive:
            for b in bases:
                basepath = self.preferences.PATH if b == "preferences" else getattr(self.base, b).PATH
                try:
                    archive.write(basepath, arcname=os.path.basename(basepath))
                except FileNotFoundError:
                    logging.warning(f"Aucun fichier pour la base {b}")
        return savepath

    def import_data(self, filepath):
        """Unziip archive. Chech integrity.
        Overwrite current base"""
        newbases = {}
        try:
            with ZipFile(filepath) as archive:
                keys = [os.path.splitext(b)[0] for b in archive.namelist()]
                try:
                    for b, key in zip(archive.namelist(), keys):
                        with archive.open(b) as fo:
                            baseobject = Preferences.from_fileobject(
                                fo) if key == "preferences" else self.base.cree_base(key, fileobject=fo)
                            newbases[key] = baseobject
                except StructureError:
                    raise
                else:  # les fichiers sont valides, on peut extraire
                    archive.extractall(Core.base_locale.CHEMIN_DB)

        except BadZipFile as e:
            raise StructureError(f"Archive invalide : {e}")
        else:
            for key, base in newbases.items():  # chargement en mémoire vive
                if key == "preferences":
                    self.preferences = base
                else:
                    setattr(self.base, key, base)
            self.reset_interfaces()
            return keys
