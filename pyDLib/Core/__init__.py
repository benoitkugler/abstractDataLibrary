import json
import logging
import re


class ConnexionError(Exception):
    """In case of networkin error"""
    pass


class StructureError(Exception):
    """In case of data integrity error"""
    pass


CREDENCES = None

FICHIER_CREDENCES = "credences/credences"
FICHIER_CREDENCES_DEV = "credences/credences_dev"


def id_from_name(s):
    s = s.lower()
    return re.sub("[^a-zA-Z0-9]", "", s)


def protege_data(datas_str, sens):
    """
    Used to crypt/decrypt data before saving locally.
    Override if securit is needed.
    bytes -> str when decrypting
    str -> bytes when crypting

    :param datas_str: When crypting, str. when decrypting bytes
    :param sens: True to crypt, False to decrypt
    """
    return bytes(datas_str, encoding="utf8") if sens else str(datas_str, encoding="utf8")


def load_credences(dev=False):
    global CREDENCES
    path = dev and FICHIER_CREDENCES_DEV or FICHIER_CREDENCES
    try:
        with open(path, 'rb') as f:
            encrypt = f.read()
            json_str = protege_data(encrypt, False)
            CREDENCES = json.loads(json_str)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise StructureError(f"Invalid credences file ! Details : {e}")
    logging.info(f"Credences loaded from {path}")


PARAMETERS_PATH = {"CONFIG": "configuration/options.json"}
PARAMETERS = {}

def load_configuration():
    try:
        for name, path in PARAMETERS_PATH.items():
            with open("configuration/options.json", encoding='utf-8') as f:
                dic = json.load(f)
            PARAMETERS[name] = dic
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise StructureError("Invalid configuration files ! Détails : {}".format(e))

def init_modules():
    """Should pass to python modules init_module the required parameters"""
    pass


def init_all(dev=False):
    load_credences(dev=dev)
    load_configuration()
    init_modules()


## ------------------- Version notes ------------------- ##

CHANGELOG_PATH = "configuration/changelog.html"
def load_changelog():
    try:
        with open(CHANGELOG_PATH, encoding="utf-8") as f:
            s = f.read()
    except FileNotFoundError:
        s = "Aucune note de version disponible."
    return s