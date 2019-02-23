"""Defines in memory data storage and acces"""
import json
import logging
import re
from typing import Optional, Union, Any, Set

from . import StructureError
from . import groups, sql, formats, security

MIN_CHAR_SEARCH = 2


class abstractAcces:
    """Proxy object of one entity of a table.
    properties accesed are dynamic.
    storage on database is made through `modifications` attribute, which stores dumped datas
    """

    TABLE = ""
    """name of table acces refers to"""

    FIELDS_OPTIONS: Set[str] = set()
    """Fields names of data grouped in the DB, which should be still be acceded as one field"""

    modifications: dict
    Id: Union[None, int, str]

    def __init__(self, base: 'abstractBase', Id: Union[None, str, int]) -> None:
        """

        :param base: Pointer to the base
        :param Id: Identifier of the entity
        """
        self.Id = Id
        self.base = base
        self.modifications = {}  # temporary in memory modifications

    def __getitem__(self, item: str) -> Any:
        """Gives priority to modifications"""
        if item in self.FIELDS_OPTIONS:
            if "options" in self.modifications:
                return self.modifications["options"].get(item, None)
            elif self.Id is not None:
                options = getattr(self.base, self.TABLE)[
                    self.Id].get("options", {}) or {}
                return options.get(item, None)
            else:
                return None
        else:
            if item in self.modifications:
                return self.modifications[item]
            elif self.Id is not None:
                return getattr(self.base, self.TABLE)[self.Id].get(item, None)
            else:
                return None

    def modifie(self, key: str, value: Any) -> None:
        """Store the modification. `value` should be dumped in DB compatible format."""
        if key in self.FIELDS_OPTIONS:
            self.modifie_options(key, value)
        else:
            self.modifications[key] = value

    def modifie_many(self, dic: dict):
        """Convenience function which calls modifie on each element of dic"""
        for i, v in dic.items():
            self.modifie(i, v)

    def _dict_to_SQL(self, dic):
        r = sql.abstractRequetesSQL.update(self.TABLE, dic, self.Id)
        return sql.Executant([r])

    def save(self) -> sql.Executant:
        """Prepare a SQL request to save the current modifications.
        Returns actually a LIST of requests (which may be of length one).
        Note than it can include modifications on other part of the data.
        After succes, the base should be updated.
        """
        r = self._dict_to_SQL(self.modifications)
        self.modifications.clear()
        return r

    def __str__(self):
        return f"Acces of table {self.TABLE} with id {self.Id} and modifications {self.modifications}"

    def modifie_options(self, field_option, value):
        """Set options in modifications.
        All options will be stored since it should be grouped in the DB."""
        options = dict(self["options"] or {}, **{field_option: value})
        self.modifications["options"] = options


def _convert_id(i):
    """Try to convert i to int. If it fails, returns i"""
    try:
        i = int(i)
    except ValueError:
        pass
    return i


class abstractDictTable(dict):
    """Represents one table : dict {id : dict_attributes}.
    `id` are converted in int if possible.
    """

    CHAMP_ID = "id"
    """Default value for field use in conversion from list to dict"""

    ACCES = abstractAcces
    """Class of corresping acces. Used for research functions"""

    @classmethod
    def _from_dict_dict(cls, dic):
        """Takes a dict {id : dict_attributes} """
        return cls({_convert_id(i): v for i, v in dic.items()})

    @classmethod
    def _from_list_dict(cls, list_dic):
        """Takes a list of dict like objects and uses `champ_id` field as Id"""
        return cls({_convert_id(dic[cls.CHAMP_ID]): dict(dic) for dic in list_dic})

    @classmethod
    def from_data(cls, data):
        if type(data) is list:
            return cls._from_list_dict(data)
        else:
            return cls._from_dict_dict(data)

    def __init__(self, data):
        super().__init__(data or {})

    def dumps(self):
        """Returns a list of dict. To be consistent with SQL-DB format."""
        return list(self.values())

    @staticmethod
    def _record_to_string(row):
        return str(row["id"])

    def base_recherche_rapide(self, base, pattern, to_string_hook=None):
        """
        Search pattern in string build from entries.

        :param pattern: String to search for
        :param to_string_hook: Callable dict -> str to map record to string. Default to _record_to_string
        :return:
        """
        Ac = self.ACCES
        if pattern == "*":
            return groups.Collection(Ac(base, i) for i in self)

        if len(pattern) >= MIN_CHAR_SEARCH:  # Needed chars.
            sub_patterns = pattern.split(" ")
            try:
                regexps = tuple(re.compile(sub_pattern, flags=re.I)
                                for sub_pattern in sub_patterns)
            except re.error:
                return groups.Collection()

            def search(string):
                for regexp in regexps:
                    if not regexp.search(string):
                        return False
                return True

            to_string_hook = to_string_hook or self._record_to_string
            return groups.Collection(Ac(base, i) for i, p in self.items() if search(to_string_hook(p)))

        return groups.Collection()

    def select_by_field(self, base, field, value):
        """Return collection of acces whose field equal value"""
        Ac = self.ACCES
        return groups.Collection(Ac(base, i) for i, row in self.items() if row[field] == value)

    def select_by_critere(self, base, criteria):
        """
        :param base: Reference on whole base
        :param criteria: Callable abstractAcces -> Bool, acting as filter
        :return: Collection on acces passing the criteria
        """
        Ac = self.ACCES
        return groups.Collection(Ac(base, i) for i in self if criteria(Ac(base, i)))

    def to_collection(self, base):
        Ac = self.ACCES
        return groups.Collection(Ac(base, i) for i in self)


class abstractListTable(list):
    """Represents one table : list [dict_attributes]"""

    @classmethod
    def from_data(cls, list_dict):
        """Takes a list of dict like objects and build a table"""
        return cls(dict(d) for d in list_dict)

    def __init__(self, data):
        super().__init__(data or [])

    def dumps(self):
        return self


class abstractBase:
    """ Tables structure. Dict { table_name : table_class }.
    table_class should inherit abstractDictTable or abstract ListTable"""

    TABLES = {}

    LOCAL_DB_PATH = None
    """Local file path"""

    @classmethod
    def load_from_db(cls, callback_etat=print, out=None):
        """Launch data fetching then load data received.
        The method _load_remote_db should be overridden.
        If out is given, datas are set in it, instead of returning a new base object.
        """
        dic = cls._load_remote_db(callback_etat)
        callback_etat("Chargement...", 2, 3)
        if out is None:
            return cls(dic)
        cls.__init__(out, datas=dic)

    @classmethod
    def _load_remote_db(cls, callback_etat):
        """ Should use remote DB or server.

        :param callback_etat: callable (`msg` : str , `current_step` : int, `max_step` :int) -> None
        :return: Dictionnary of tables
        """
        return {}

    @classmethod
    def _parse_text_DB(self, s):
        """Returns a dict of table interpreted from s.
        s should be Json string encoding a dict { table_name :  [fields_name,...] , [rows,... ] }"""
        dic = self.decode_json_str(s)
        new_dic = {}
        for table_name, (header, rows) in dic.items():
            newl = [{c: ligne[i]
                     for i, c in enumerate(header)} for ligne in rows]
            new_dic[table_name] = newl
        return new_dic

    @staticmethod
    def decode_json_str(json_str):
        try:
            dic = json.loads(json_str, object_hook=formats.date_decoder)
        except json.JSONDecodeError as e:
            raise StructureError(f"Données corrompues ! {e.doc}")
        return dic

    @classmethod
    def load_from_local(cls):
        """Load datas from local file."""
        try:
            with open(cls.LOCAL_DB_PATH, 'rb') as f:
                b = f.read()
                s = security.protege_data(b, False)
        except (FileNotFoundError, KeyError):
            logging.exception(cls.__name__)
            raise StructureError(
                "Erreur dans le chargement de la sauvegarde locale !")
        else:
            return cls(cls.decode_json_str(s))

    def __init__(self, datas=None):
        """
        Creates tables from data.
        :param datas: one of
            - list : list of tables content. The order is the one of sorted(TABLES.keys())
            - dict : {table_name : table_content }
        """
        if type(datas) is dict:
            for table_name, table_data in datas.items():
                table = self._get_table(table_name, table_data)
                setattr(self, table_name, table)

        elif type(datas) is list:
            for i, table_name in enumerate(sorted(self.TABLES.keys())):
                table = self._get_table(table_name, datas[i])
                setattr(self, table_name, table)

    def dumps(self):
        """Return a dictionnary of current tables"""
        return {table_name: getattr(self, table_name).dumps() for table_name in self.TABLES}

    @classmethod
    def _get_table(cls, nom, data):
        if nom in cls.TABLES:
            return cls.TABLES[nom].from_data(data)
        return None

    def load_partiel(self, **kwargs):
        for i, v in kwargs.items():
            assert i in self.TABLES
            table = self._get_table(i, v)
            setattr(self, i, table)

    def save_to_local(self, callback_etat=print):
        """
        Saved current in memory base to local file.
        It's a backup, not a convenient way to update datas

        :param callback_etat: state callback, taking  str,int,int as args
        """
        callback_etat("Aquisition...", 0, 3)
        d = self.dumps()
        s = json.dumps(d, indent=4, cls=formats.JsonEncoder)
        callback_etat("Chiffrement...", 1, 3)
        s = security.protege_data(s, True)
        callback_etat("Enregistrement...", 2, 3)
        try:
            with open(self.LOCAL_DB_PATH, 'wb') as f:
                f.write(s)
        except (FileNotFoundError):
            logging.exception(self.__class__.__name__)
            raise StructureError("Chemin de sauvegarde introuvable !")
