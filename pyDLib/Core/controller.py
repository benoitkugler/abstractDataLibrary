"""Implements theory_main objects : interfaces wrapper by interInterfaces """
import json
import logging
import os
from typing import Dict, Type, List, Optional

from . import data_model, groups, formats, sql, threads, security
from . import init_all, StructureError


class Callbacks:

    def __getattr__(self, key):
        def f(*args, **kwargs):
            logging.error(
                f"No callback with name {key}, args {args} and kwargs {kwargs} registered !")

        return f


class abstractInterface:
    """Base class for the main driver of the application. GUI parts will register callbacks through
    set_callback, add_reset_function, add_update_function.
    Then, the interface update datas and refresh the rendering with update_rendering, reset_rendering.
    It's up to the interface to choose between a soft update or a hard one (with reset)
    """

    ACCES: Type[data_model.abstractAcces] = data_model.abstractAcces
    """Default acces. Used in the convenient function get_acces"""

    CALLBACKS: List[str] = []
    """Functions that a GUI module should provide. 
    Note : a callback update_toolbar should be also set (by the mai GUI application)"""

    TABLE: Optional[str] = None
    """Default table used to build main collection (through get_all)"""

    base: data_model.abstractBase
    collection: groups.Collection
    main: 'abstractInterInterfaces'

    def __init__(self, main: 'abstractInterInterfaces', permission):
        """
        Constructeur.

        :param main: Abstract theory_main
        :param permission: Integer coding permission for this module
        """
        self.main = main
        self.base = main.base
        self.permission = permission

        self.sortie_erreur_GUI = lambda s, wait=False: print(s)
        self.sortie_standard_GUI = lambda s, wait=False: print(s)

        self.updates = []  # graphiques updates
        self.resets = []  # graphiques resets

        self.callbacks = Callbacks()  # Containers for callbacks
        self.set_callback("update_toolbar", lambda: None)

        self.threads = []  # Active threads

        self.collection = self.get_all()

    def reset(self):
        self._reset_data()
        self._reset_render()

    def update(self):
        self._update_data()
        self._update_render()

    def _reset_data(self):
        self.collection = self.get_all()

    def _update_data(self):
        pass

    def _reset_render(self):
        for f in self.resets:
            f()
        self.callbacks.update_toolbar()

    def _update_render(self):
        for f in self.updates:
            f()
        self.callbacks.update_toolbar()

    def add_reset_function(self, f):
        self.resets.append(f)

    def remove_reset_function(self, f):
        try:
            self.resets.remove(f)
        except ValueError:
            logging.exception("Unknown reset function !")

    def add_update_function(self, f):
        self.updates.append(f)

    def remove_update_function(self, f):
        try:
            self.updates.remove(f)
        except ValueError:
            logging.exception("Unknown update function !")

    def set_callback(self, name, function):
        setattr(self.callbacks, name, function)

    def get_acces(self, Id) -> data_model.abstractAcces:
        return self.ACCES(self.base, Id)

    def get_all(self) -> groups.Collection:
        table = getattr(self.base, self.TABLE)
        c = groups.Collection(self.ACCES(self.base, i) for i in table)
        return c

    def recherche(self, pattern, entete, in_all=False):
        """abstractSearch in fields of collection and reset rendering.
        Returns number of results.
        If in_all is True, call get_all before doing the search."""
        if in_all:
            self.collection = self.get_all()
        self.collection.recherche(pattern, entete)
        self._reset_render()
        return len(self.collection)

    def launch_background_job(self, job, on_error=None, on_success=None):
        """Launch the callable job in background thread.
        Succes or failure are controlled by on_error and on_success
        """
        if not self.main.mode_online:
            self.sortie_erreur_GUI(
                "Local mode activated. Can't run background task !")
            self.reset()
            return

        on_error = on_error or self.sortie_erreur_GUI
        on_success = on_success or self.sortie_standard_GUI

        def thread_end(r):
            on_success(r)
            self.update()

        def thread_error(r):
            on_error(r)
            self.reset()

        logging.info(
            f"Launching background task from interface {self.__class__.__name__} ...")
        th = threads.worker(job, thread_error, thread_end)
        self._add_thread(th)

    def _add_thread(self, th):
        self.threads.append(th)
        th.done.connect(lambda: self.threads.remove(th))
        th.error.connect(lambda: self.threads.remove(th))

    def get_labels_stats(self):
        """Should return a list of labels describing the stats"""
        raise NotImplementedError

    def get_stats(self):
        """Should return a list of numbers, compliant to get_labels_stats"""
        raise NotImplementedError

    def get_actions_toolbar(self):
        """Return a list of toolbar constitution. One element has the form
            ( identifier , callback , tooltip , enabled ).
            This function is called every time the toolbar updates"""
        return []

    @staticmethod
    def filtre(liste_base, criteres) -> groups.Collection:
        """
        Return a filter list, bases on criteres

        :param liste_base: Acces list
        :param criteres: Criteria { `attribut`:[valeurs,...] }
        """

        def choisi(ac):
            for cat, li in criteres.items():
                v = ac[cat]
                if not (v in li):
                    return False
            return True

        return groups.Collection(a for a in liste_base if choisi(a))

    def copy_to_clipboard(self, text):
        self.main.callbacks.copy_to_clipboard(text)


class abstractInterInterfaces:
    """
    Entry point of abstrat tasks.
    Responsible of loading data, preferences, configuration,...
    """

    PATH_PREFERENCES = "preferences.json"

    DEBUG = {}
    """debug modules"""

    BASE_CLASS = data_model.abstractBase

    INTERFACES_MODULE = None
    """Modules containing all interfaces required"""

    base: data_model.abstractBase
    autolog: Dict
    interfaces: Dict[str, abstractInterface]

    def __init__(self):
        self.base = None
        self.users = {}
        self.autolog = {}
        self.modules = {}  # Modules to load

        self.interfaces = {}

        self.preferences = self.load_preferences()

        self.callbacks = Callbacks()

    def load_preferences(self):
        if not os.path.isfile(self.PATH_PREFERENCES):
            logging.warning(
                f"No user preferences file found in {os.path.abspath(self.PATH_PREFERENCES)} !")
            return {}
        with open(self.PATH_PREFERENCES, "r", encoding="utf8") as f:
            try:
                return json.load(f, object_hook=formats.date_decoder)
            except json.JSONDecodeError:
                logging.exception("User preferences file corrupted !")
                return {}

    def update_preferences(self, key, value):
        if key is not None:
            self.preferences[key] = value
        with open(self.PATH_PREFERENCES, "w", encoding="utf8") as f:
            json.dump(self.preferences, f, cls=formats.JsonEncoder)
        logging.info(f"Preference {key} updated.")

    def load_remote_data(self, callback_etat=print):
        """
        Load remote data. On succes, build base.
        On failure, raise :class:`~.Core.exceptions.StructureError`, :class:`~.Core.exceptions.ConnexionError`

        :param callback_etat: State renderer str , int , int -> None
        """
        callback_etat("Chargement des utilisateurs", 0, 1)
        self._load_users()
        self.base = self.BASE_CLASS.load_from_db(callback_etat=callback_etat)

    def _load_users(self):
        """Default implentation requires users from DB.
        Should setup `users` attribute"""
        r = sql.abstractRequetesSQL.get_users()()
        self.users = {d["id"]: dict(d) for d in r}

    def reset_interfaces(self):
        """Reset data and rendering for all interfaces"""
        for i in self.interfaces.values():
            i.reset()

    def set_callback(self, name, f):
        """Store a callback accessible from all interfaces"""
        setattr(self.callbacks, name, f)

    def load_modules(self):
        """Should instance interfaces and set them to interface, following `modules`"""
        if self.INTERFACES_MODULE is None:
            raise NotImplementedError("A module containing interfaces modules "
                                      "should be setup in INTERFACES_MODULE !")
        else:
            for module, permission in self.modules.items():
                i = getattr(self.INTERFACES_MODULE,
                            module).Interface(self, permission)
                self.interfaces[module] = i

    def export_data(self, bases, savedir):
        """Packs and zip asked bases (from base).
        Saves archive in given savedir"""
        raise NotImplementedError

    def import_data(self, filepath):
        """Unziip archive. Chech integrity.
        Overwrite current base"""
        raise NotImplementedError

    def init_modules(self, dev=False):
        """load_credences, load_configuration, init_modules from Core should be overridden"""
        init_all(dev)

    def update_credences(self, url):
        """Download and update credences file.
        Modules should be re-initialized after"""
        raise NotImplementedError

    def update_configuration(self, monitor=print):
        """Download and update configuration files. Url is given in credences"""
        raise NotImplementedError

    def has_autolog(self, user_id):
        """
        Read auto-connection parameters and returns local password or None
        """
        try:
            with open("local/init", "rb") as f:
                s = f.read()
                s = security.protege_data(s, False)
                self.autolog = json.loads(s).get("autolog", {})
        except FileNotFoundError:
            return

        mdp = self.autolog.get(user_id, None)
        return mdp

    def loggin(self, user_id, mdp, autolog):
        """Check mdp and return True it's ok"""
        r = sql.abstractRequetesSQL.check_mdp_user(user_id, mdp)
        if r():
            # update auto-log params
            self.autolog[user_id] = autolog and mdp or False
            self.modules = self.users[user_id]["modules"]  # load modules list

            dic = {"autolog": self.autolog, "modules": self.modules}
            s = json.dumps(dic, indent=4, ensure_ascii=False)
            b = security.protege_data(s, True)
            with open("local/init", "wb") as f:
                f.write(b)

            self.mode_online = True  # authorization to execute bakground tasks
            return True
        else:
            logging.debug("Bad password !")

    def loggin_local(self):
        try:
            with open("local/init", "rb") as f:
                s = f.read()
                s = security.protege_data(s, False)
                modules = json.loads(s)["modules"]
        except (KeyError, FileNotFoundError) as e:
            raise StructureError(
                "Impossible des lire les derniers modules utilisés !")
        else:
            self.modules = {k: 0 for k in modules}  # low permission
            self.mode_online = False

        self.base = self.BASE_CLASS.load_from_local()

    def launch_debug(self, mode_online):
        self.mode_online = mode_online
        self.modules = self.DEBUG
        self.base = self.BASE_CLASS.load_from_local()
        self.load_modules()

    def direct_load_remote_db(self):
        tables = [t for t in sorted(self.base.TABLES)]
        l = sql.abstractRequetesSQL.load_data(tables)()
        self.base = self.BASE_CLASS(l)
