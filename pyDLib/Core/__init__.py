import json
import logging
import re

from . import security


class ConnexionError(Exception):
    """In case of networkin error"""
    pass


class StructureError(Exception):
    """In case of data integrity error"""
    pass


CREDENCES = None

FICHIER_CREDENCES = "credences/credences"
FICHIER_CREDENCES_DEV = "credences/credences_dev"
FICHIER_CREDENCES_LOCAL_DEV = "credences/credences_local_dev"



def id_from_name(s):
    s = s.lower()
    return re.sub("[^a-zA-Z0-9]", "", s)


def load_credences(dev=False):
    global CREDENCES
    path = {True: FICHIER_CREDENCES_DEV, False: FICHIER_CREDENCES, "local_dev": FICHIER_CREDENCES_LOCAL_DEV}[dev]
    try:
        with open(path, 'rb') as f:
            encrypt = f.read()
            json_str = security.protege_data(encrypt, False)
            CREDENCES = json.loads(json_str)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise StructureError(f"Invalid credences file ! Details : {e}")
    logging.info(f"Credences loaded from {path}")


PARAMETERS_PATH = {"CONFIG": "configuration/options.json"}
PARAMETERS = {}

def load_configuration():
    try:
        for name, path in PARAMETERS_PATH.items():
            with open(path, encoding='utf-8') as f:
                dic = json.load(f)
            PARAMETERS[name] = dic
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise StructureError("Invalid configuration files ! Détails : {}".format(e))


def init_modules(dev=False):
    """Should pass to python modules init_module function the required parameters"""
    pass


def init_all(dev=False):
    load_credences(dev=dev)
    load_configuration()
    init_modules(dev=dev)


## ------------------- Version notes ------------------- ##

CHANGELOG_PATH = "configuration/changelog.html"
def load_changelog():
    try:
        with open(CHANGELOG_PATH, encoding="utf-8") as f:
            s = f.read()
    except FileNotFoundError:
        s = "Aucune note de version disponible."
    return s