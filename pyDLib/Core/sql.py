"""Defines SQL basic interaction. Two variantes are proposed :
    - local DB accessed with SQLite
    - remote DB accessed with PostgreSQL
"""
import datetime
import json
import logging
import os
import re
import sqlite3

try:
    import psycopg2
    import psycopg2.extras
    has_psycopg2 = True
except ImportError:
    has_psycopg2 = False

from . import formats
from . import ConnexionError, StructureError


def init_module(remote_credences=None,local_path=None):
    """Connnexion informations : remote_credences for remote acces OR local_path for local access"""
    if remote_credences is not None:
        RemoteConnexion.HOST = remote_credences["DB"]["host"]
        RemoteConnexion.USER = remote_credences["DB"]["user"]
        RemoteConnexion.PASSWORD = remote_credences["DB"]["password"]
        RemoteConnexion.NAME = remote_credences["DB"]["name"]
        MonoExecutant.ConnectionClass = RemoteConnexion
        Executant.ConnectionClass = RemoteConnexion
        abstractRequetesSQL.setup_marks("pscycopg2")
    elif local_path is not None:
        LocalConnexion.PATH = local_path
        MonoExecutant.ConnectionClass = LocalConnexion
        Executant.ConnectionClass = LocalConnexion
        abstractRequetesSQL.setup_marks("sqlite3")
    else:
        raise ValueError("Sql module should be init with one of remote or local mode !")
    logging.info("Sql module initialized.")


class MonoExecutant(tuple):

    ConnectionClass = None

    def __call__(self):
        if self:
            return self.ConnectionClass().execute(self)
        return []


class Executant(list):

    ConnectionClass = None

    def __call__(self):
        if self:
            return self.ConnectionClass().execute(self)
        return []

    def __bool__(self):
        return sum(bool(x) for x in self) >= 1


class abstractConnexion:
    """Base class for the two connexions classes.
    Wraps real SQL connexion object."""

    SQL = None
    """SQL module to use"""


    def __init__(self, DSN,autocommit,**kwargs):
        try:
            connexion = self.SQL.connect(DSN,**kwargs)
        except self.SQL.Error as e:
            raise ConnexionError(f"Impossible de se connecter à la base de données distante. Details : {e}")
        else:
            self.connexion = connexion
            self.set_autocommit(autocommit)

    def set_autocommit(self,autocommit):
        self.connexion.autocommit = autocommit

    def cursor(self):
        raise NotImplementedError

    def _execute_one(self,cursor,req,args):
        cursor.execute(req,args)
        try:
            res = cursor.fetchall()
        except self.SQL.ProgrammingError:
            logging.exception("")
            res = []
        return res


    def execute(self, requete_SQL):
        """Execute one or many requests
        requete_SQL may be a tuple(requete,args) or a list of such tuples
        Return the result or a list of results
        """
        try:
            cursor = self.cursor()
            if isinstance(requete_SQL,tuple):
                res = self._execute_one(cursor,*requete_SQL)
            else:
                res = []
                for r in requete_SQL:
                    if r:
                        res.append(self._execute_one(cursor,*r))

        except self.SQL.Error as e:
            raise StructureError(f"SQL error ! Details : \n {e}")
        else:
            self.connexion.commit()
        finally:
            self.connexion.close()
        return res


sqlite3.register_converter("json",lambda s : json.loads(s,object_hook=formats.date_decoder))
sqlite3.register_adapter(list,lambda l : json.dumps(l,cls=formats.JsonEncoder))
sqlite3.register_converter("list",lambda s : json.loads(s,object_hook=formats.date_decoder))

class LocalConnexion(abstractConnexion):
    """Connexion to local SQLite DB."""

    PATH = None

    connexion : sqlite3.Connection
    SQL = sqlite3

    REGEXP_TABLE = re.compile("(INSERT INTO|UPDATE)\s*(\w*)",flags=re.I)
    REGEXP_ID = re.compile("id =\s*(\w*)",flags=re.I)

    def __init__(self,autocommit=False):
        DSN = os.path.join(self.PATH,"db.sqlite")
        super().__init__(DSN,autocommit,detect_types=self.SQL.PARSE_DECLTYPES)

    def set_autocommit(self,autocommit):
        pass

    def _execute_one(self,cursor,req : str,args):
        if re.search("RETURNING \*",req,flags=re.I):
            req = req.replace("RETURNING *","")
            super()._execute_one(cursor,req,args) # no intersting result so far
            match = self.REGEXP_TABLE.search(req)
            table = match.group(2)
            if match.group(1).upper().strip() == "UPDATE":
                Id = args["__id"]
            else:
                Id = cursor.lastrowid
            cursor.execute(f"SELECT * FROM {table} WHERE id = {Id}")
            return cursor.fetchall()
        return super(LocalConnexion, self)._execute_one(cursor,req,args)


    def cursor(self):
        self.connexion.row_factory = sqlite3.Row
        return self.connexion.cursor()




class RemoteConnexion(abstractConnexion):
    """Connexion to local PostgreSQL DB"""

    SQL = psycopg2 if has_psycopg2 else None

    HOST = ""
    USER = ""
    PASSWORD = ""
    NAME = ""

    def __init__(self, autocommit=False, dev=False):
        # If dev is asked, use basename_dev
        name = dev and self.NAME.split("_")[0] + "_dev" or self.NAME
        DSN = "host={} user={} password={} dbname={}".format(self.HOST, self.USER, self.PASSWORD, name)
        super().__init__(DSN,autocommit)

    def cursor(self):
        return self.connexion.cursor(cursor_factory=psycopg2.extras.DictCursor)



def cree_local_DB(scheme):
    """Create emmpt DB according to the given scheme : dict { table : [ (column_name, column_type), .. ]}
    Usefull at installation of application (and for developement)
    """
    conn = LocalConnexion()
    req = ""
    for table, fields in scheme.items():
        req += f"DROP TABLE IF EXISTS {table};"
        req_fields = ", ".join(f'{c_name} {c_type}' for c_name, c_type in fields)
        req += f"""CREATE TABLE {table} (  {req_fields} ) ;"""
    cur = conn.cursor()
    cur.executescript(req)
    conn.connexion.commit()
    conn.connexion.close()
    logging.info("Database created with succes.")




class abstractRequetesSQL():
    """Functions to build requests. To actually execute them, call them.
    The syntax is compliant with PostgreSQL standards, but it can be as well used with SQLite.
    To support the RETURNING operation, the resquest is replaced at execution by two requests, the later selecting and returning the data. This is only possible if RETURNING * is at the end of the requests !
    """

    mark_style = named_style = ""

    TYPES_PERMIS = [list, int, float, str, bool, type(None), datetime.date, datetime.datetime]

    @classmethod
    def setup_marks(cls,mode):
        cls.mark_style = "%s" if mode == "psycopg2" else "?"
        cls.named_style = "%({})s" if mode == "psycopg2" else ":{}"

    @classmethod
    def placeholders(cls,dic):
        """Placeholders for fields names and value binds"""
        keys = [str(x) for x in dic]
        entete = ",".join(keys)
        placeholders = ",".join(cls.named_style.format(x) for x in keys)
        entete = f"({entete})"
        placeholders = f"({placeholders})"
        return entete, placeholders

    @classmethod
    def placeholders_set(cls,dic):
        placeholders = " ,".join([("{} = " + cls.named_style).format(k,k) for k in dic])
        return placeholders

    @staticmethod
    def jsonise(dic):
        """Renvoie un dictionnaire dont les champs dont compatibles avec SQL
        Utilise Json. Attention à None : il faut laisser None et non pas null"""
        d = {}
        for k, v in dic.items():
            if type(v) in abstractRequetesSQL.TYPES_PERMIS:
                d[k] = v
            else:
                try:
                    d[k] = json.dumps(v, ensure_ascii=False, cls=formats.JsonEncoder)
                except ValueError as e:
                    logging.exception("Erreur d'encodage JSON !")
                    raise e
        return d

    @staticmethod
    def formate(req, SET=(), table=None, INSERT=(), INSERT2=(), args=None):
        args = args or {}
        SET = abstractRequetesSQL.placeholders_set(SET)
        ENTETE_INSERT, BIND_INSERT = abstractRequetesSQL.placeholders(INSERT)
        ENTETE_INSERT2, BIND_INSERT2 = abstractRequetesSQL.placeholders(INSERT2)
        req = req.format(table=table, SET=SET, ENTETE_INSERT=ENTETE_INSERT, BIND_INSERT=BIND_INSERT,
                         ENTETE_INSERT2=ENTETE_INSERT2, BIND_INSERT2=BIND_INSERT2)
        args = abstractRequetesSQL.jsonise(args)
        return (req, args)


    @staticmethod
    def insert(table, datas, avoid_conflict=False):
        """ Insert row from datas

        :param table: Safe table name
        :param datas: List of dicts.
        :param avoid_conflict: Allows ignoring error if already exists (do nothing then)
        :return:
        """
        if avoid_conflict:
            debut = """INSERT INTO {table} {ENTETE_INSERT} VALUES {BIND_INSERT} ON CONFLICT DO NOTHING"""
        else:
            debut = """INSERT INTO {table} {ENTETE_INSERT} VALUES {BIND_INSERT} RETURNING *"""
        l = [abstractRequetesSQL.formate(debut, table=table, INSERT=d, args=d) for d in datas if d]
        return Executant(l)

    @classmethod
    def update(cls,table, dic, Id):
        """ Update row with Id from table. Set fields given by dic."""
        if dic:
            req = "UPDATE {table} SET {SET} WHERE id = " + cls.named_style.format('__id') +  " RETURNING * "
            r = abstractRequetesSQL.formate(req, SET=dic, table=table, args=dict(dic, __id=Id))
            return MonoExecutant(r)
        return MonoExecutant()


    @staticmethod
    def cree(table, dic, avoid_conflict=False):
        """ Create ONE row from dic and returns the entry created """
        if avoid_conflict:
            req = """ INSERT INTO {table} {ENTETE_INSERT} VALUES {BIND_INSERT} ON CONFLICT DO NOTHING RETURNING *"""
        else:
            req = """ INSERT INTO {table} {ENTETE_INSERT} VALUES {BIND_INSERT} RETURNING *"""
        r = abstractRequetesSQL.formate(req, table=table, INSERT=dic, args=dic)
        return MonoExecutant(r)

    @staticmethod
    def load_data(liste_table):
        """
        :param liste_table: List of safe table name
        :return: List of table contents"""
        l = [ (f"SELECT * FROM {t}" , {} )  for t in liste_table]
        return Executant(l)


    @classmethod
    def supprime(cls,table, **kwargs):
        """ Remove entries matchin given condition
        kwargs is a dict of column name :  value , with length ONE.
        """
        assert len(kwargs) == 1
        field, value = kwargs.popitem()
        req = f"""DELETE FROM {table} WHERE {field} = """ + cls.mark_style
        args = (value,)
        return MonoExecutant((req, args))

    @staticmethod
    def get_users():
        return MonoExecutant(("SELECT * FROM users",))

    @classmethod
    def check_mdp_user(cls,id_user, mdp):
        r = f"SELECT * FROM users WHERE id = {cls.mark_style} AND mdp = {cls.mark_style}"
        return MonoExecutant((r, (id_user, mdp)))


