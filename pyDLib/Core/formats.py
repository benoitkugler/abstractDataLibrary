# coding: utf-8
"""Defines types support"""


import datetime
import json
import re
from collections import defaultdict

### ---------- JSON support -------------- ###
class JsonEncoder(json.JSONEncoder):
    """Add python types encoding. Customs types should dumps to python types first."""
    def default(self, o):
        if type(o) is datetime.date:
            return {"__date__": True, "year": o.year, "month": o.month, "day": o.day}
        elif type(o) is datetime.datetime:
            return {"__datetime__": True, "year": o.year, "month": o.month, "day": o.day, "hour": o.hour,
                    "minute": o.minute, "second": o.second}
        return super().default(o)


def date_decoder(dic):
    """Add python types decoding. See JsonEncoder"""
    if '__date__' in dic:
        dic.pop('__date__')
        try:
            d = datetime.date(**dic)
        except (TypeError, ValueError):
            raise json.JSONDecodeError("Corrupted date format !", str(dic), 1)
    elif '__datetime__' in dic:
        dic.pop('__datetime__')
        try:
            d = datetime.datetime(**dic)
        except (TypeError, ValueError):
            raise json.JSONDecodeError("Corrupted datetime format !", str(dic), 1)
    else:
        return dic
    return d



### ------ TYPES ----- ###

DATE_DEFAULT = datetime.date(1000, 1, 1)
DATETIME_DEFAULT = datetime.datetime(1000, 1, 1)

REGIONS = {
    'Inconnue': ['00'],
    'Auvergne-Rhône-Alpes': ['01', '03', '07', '15', '26', '38', '42', '43', '63', '69', '73', '74'],
    'Bourgogne-Franche-Comté': ['21', '25', '39', '58', '70', '71', '89', '90'],
    'Bretagne': ['35', '22', '56', '29'],
    'Centre-Val de Loire': ['18', '28', '36', '37', '41', '45'],
    'Corse': ['2A', '2B'],
    'Grand Est': ['08', '10', '51', '52', '54', '55', '57', '67', '68', '88'],
    'Guadeloupe': ['971'],
    'Guyane': ['973'],
    'Hauts-de-France': ['02', '59', '60', '62', '80'],
    'Île-de-France': ['75', '77', '78', '91', '92', '93', '94', '95'],
    'La Réunion': ['974'],
    'Martinique': ['972'],
    'Normandie': ['14', '27', '50', '61', '76'],
    'Nouvelle-Aquitaine': ['16', '17', '19', '23', '24', '33', '40', '47', '64', '79', '86', '87'],
    'Occitanie': ['09', '11', '12', '30', '31', '32', '34', '46', '48', '65', '66', '81', '82'],
    'Pays de la Loire': ['44', '49', '53', '72', '85'],
    'Provence-Alpes-Côte d\'Azur': ['04', '05', '06', '13', '83', '84'],
}

DEPARTEMENTS = {
    '00': 'Inconnu',
    '01': 'Ain',
    '02': 'Aisne',
    '03': 'Allier',
    '04': 'Alpes-de-Haute-Provence',
    '05': 'Hautes-Alpes',
    '06': 'Alpes-Maritimes',
    '07': 'Ardèche',
    '08': 'Ardennes',
    '09': 'Ariège',
    '10': 'Aube',
    '11': 'Aude',
    '12': 'Aveyron',
    '13': 'Bouches-du-Rhône',
    '14': 'Calvados',
    '15': 'Cantal',
    '16': 'Charente',
    '17': 'Charente-Maritime',
    '18': 'Cher',
    '19': 'Corrèze',
    '2A': 'Corse-du-Sud',
    '2B': 'Haute-Corse',
    '21': 'Côte-d\'Or',
    '22': 'Côtes-d\'Armor',
    '23': 'Creuse',
    '24': 'Dordogne',
    '25': 'Doubs',
    '26': 'Drôme',
    '27': 'Eure',
    '28': 'Eure-et-Loir',
    '29': 'Finistère',
    '30': 'Gard',
    '31': 'Haute-Garonne',
    '32': 'Gers',
    '33': 'Gironde',
    '34': 'Hérault',
    '35': 'Ille-et-Vilaine',
    '36': 'Indre',
    '37': 'Indre-et-Loire',
    '38': 'Isère',
    '39': 'Jura',
    '40': 'Landes',
    '41': 'Loir-et-Cher',
    '42': 'Loire',
    '43': 'Haute-Loire',
    '44': 'Loire-Atlantique',
    '45': 'Loiret',
    '46': 'Lot',
    '47': 'Lot-et-Garonne',
    '48': 'Lozère',
    '49': 'Maine-et-Loire',
    '50': 'Manche',
    '51': 'Marne',
    '52': 'Haute-Marne',
    '53': 'Mayenne',
    '54': 'Meurthe-et-Moselle',
    '55': 'Meuse',
    '56': 'Morbihan',
    '57': 'Moselle',
    '58': 'Nièvre',
    '59': 'Nord',
    '60': 'Oise',
    '61': 'Orne',
    '62': 'Pas-de-Calais',
    '63': 'Puy-de-Dôme',
    '64': 'Pyrénées-Atlantiques',
    '65': 'Hautes-Pyrénées',
    '66': 'Pyrénées-Orientales',
    '67': 'Bas-Rhin',
    '68': 'Haut-Rhin',
    '69': 'Rhône',
    '70': 'Haute-Saône',
    '71': 'Saône-et-Loire',
    '72': 'Sarthe',
    '73': 'Savoie',
    '74': 'Haute-Savoie',
    '75': 'Paris',
    '76': 'Seine-Maritime',
    '77': 'Seine-et-Marne',
    '78': 'Yvelines',
    '79': 'Deux-Sèvres',
    '80': 'Somme',
    '81': 'Tarn',
    '82': 'Tarn-et-Garonne',
    '83': 'Var',
    '84': 'Vaucluse',
    '85': 'Vendée',
    '86': 'Vienne',
    '87': 'Haute-Vienne',
    '88': 'Vosges',
    '89': 'Yonne',
    '90': 'Territoire de Belfort',
    '91': 'Essonne',
    '92': 'Hauts-de-Seine',
    '93': 'Seine-Saint-Denis',
    '94': 'Val-de-Marne',
    '95': 'Val-d\'Oise',
    '971': 'Guadeloupe',
    '972': 'Martinique',
    '973': 'Guyane',
    '974': 'La Réunion',
    '976': 'Mayotte',
}
DEPARTEMENTS = defaultdict(lambda: "Inconnu", **DEPARTEMENTS)

SEXES = {"M": "Homme", "F": "Femme"}

MODE_PAIEMENT = {"vir": "Virement", "cheque": "Chèque", "esp": "Espèces", "cb": "Carte bancaire"}
"""Mode de paiements"""


class abstractSearch():
    """
    abstractSearch functions, which take `objet` and a `pattern` and return a matching boolean.
    """

    REGEXP_TELEPHONE = re.compile("[^0-9]")

    @staticmethod
    def nothing(objet, pattern):
        """ Renvoie constamment *False* """
        return False

    @staticmethod
    def in_string(objet, pattern):
        """ abstractSearch dans une chaine, sans tenir compte de la casse. """
        return bool(re.search(pattern, str(objet), flags=re.I)) if objet else False

    @staticmethod
    def in_date(objet, pattern):
        """ abstractSearch dans une date datetime.date"""
        if objet:
            pattern = re.sub(" ", '', pattern)
            objet_str = abstractRender.date(objet)
            return bool(re.search(pattern, objet_str))
        return False

    @staticmethod
    def in_dateheure(objet, pattern):
        """ abstractSearch dans une date-heure datetime.datetime (cf abstractRender.dateheure) """
        if objet:
            pattern = re.sub(" ", '', pattern)
            objet_str = abstractRender.dateheure(objet)
            return bool(re.search(pattern, objet_str))
        return False

    @staticmethod
    def in_telephones(objet, pattern):
        """ abstractSearch dans une liste de téléphones. Ignore les caractères non numérique du `pattern`. """
        objet = objet or []
        pattern = abstractSearch.REGEXP_TELEPHONE.sub('', pattern)
        if pattern == '' or not objet:
            return False
        return max(bool(re.search(pattern, t)) for t in objet)


class abstractRender():
    """Printing functions, which take `objet` and return a string."""


    @staticmethod
    def default(objet):
        objet = "" if objet is None else objet
        return str(objet).strip(' \t\n\r')

    @staticmethod
    def boolen(objet):
        """ abstractRender d'un booléen """
        return "Oui" if objet else "Non"

    @staticmethod
    def date(objet):
        """ abstractRender d'une date datetime.date"""
        if objet:
            return "{}/{}/{}".format(objet.day, objet.month, objet.year)
        return ""

    @staticmethod
    def dateheure(objet):
        """ abstractRender d'une date-heure datetime.datetime au format JJ/MM/AAAAàHH:mm """
        if objet:
            return "{}/{}/{} à {:02}:{:02}".format(objet.day, objet.month, objet.year, objet.hour, objet.minute)
        return ""

    @staticmethod
    def telephones(objet):
        """ abstractRender d'une liste de numéro """
        objet = objet or []
        return " ; ".join(str(t) for t in objet)


    @staticmethod
    def pourcent(objet):
        return "" if objet is None else f"{objet} %"

    @staticmethod
    def euros(objet):
        return '{0:.2f} €'.format(objet) if objet is not None else ""

    @staticmethod
    def type_paiement(objet):
        if objet in MODE_PAIEMENT:
            return MODE_PAIEMENT[objet]
        return f"Paiement inconnu : {objet}"

    @staticmethod
    def departement(objet):
        if objet is None:
            return ""
        return DEPARTEMENTS[objet]

    @staticmethod
    def nom_prenom(objet):
        if objet is None:
            return "Anonyme"
        return (objet[0] or "").upper() + " " + (objet[1] or "").capitalize()

    @staticmethod
    def liste(objet):
        objet = objet or []
        return "\n".join(" - ".join(objet[2*i:2*i+1]) for i in range(len(objet)//3) )



def _type_string(label):
    """Shortcut for string like fields"""
    return label, abstractSearch.in_string, abstractRender.default, ""


def _type_date(label):
    """Shortcut for date like fields"""
    return label, abstractSearch.in_date, abstractRender.date, DATE_DEFAULT

def _type_datetime(label):
    """Shortcut for datetime like fields"""
    return label, abstractSearch.in_dateheure, abstractRender.dateheure, DATETIME_DEFAULT

def _type_bool(label,default=False):
    """Shortcut fot boolean like fields"""
    return label, abstractSearch.nothing, abstractRender.boolen, default


"""
Formats definitions.
Warning: a field name is global to the whole app.
Every field name is linked to a tuple (`label`,`recherche`,`affichage`,`default`) :
   - `label` : rendered name
   - `recherche` : search function
   - `affichage` : rendering function
   - `default` : default value
"""
ASSOCIATION = {
    'mail': _type_string("Adresse e-mail"),
    'nom': _type_string("Nom"),
    'nom_jeune_fille': _type_string("Nom de jeune fille"),
    'adresse': _type_string("Adresse"),
    'prenom': _type_string("Prénom"),
    'password': _type_string("Mot de passe"),
    'ville': _type_string("Ville"),
    'ville_naissance': _type_string("Ville de naissance"),
    'securite_sociale': _type_string("Numéro de sécurité sociale"),
    'telephone': _type_string("Téléphone"),
    'immatriculation': _type_string("Immatriculation"),
    'lieu': _type_string("Lieu"),
    'date_naissance': _type_date("Date de naissance"),
    'date': _type_date("Date"),
    'begining': _type_date("Date de début"),
    'end': _type_date("Date de fin"),
    'age': ("Age", abstractSearch.in_string, abstractRender.default, 0),
    'departement_naissance': ("Département de naissance", abstractSearch.in_string, abstractRender.departement, "01"),
    'sexe': ("Sexe", abstractSearch.in_string, abstractRender.default, "M"),
    'tels': ("Téléphone", abstractSearch.in_telephones, abstractRender.telephones, []),
    'code_postal': ("Code postal", abstractSearch.in_string, abstractRender.default, "0"),
    'annee': ("Année", abstractSearch.in_string, abstractRender.default, 0),
    'date_heure_modif': ("Dernière modification", abstractSearch.in_dateheure, abstractRender.dateheure, DATETIME_DEFAULT),
    'valeur': ("Valeur", abstractSearch.in_string, abstractRender.euros, 0),
    'prix': ("Prix", abstractSearch.in_string, abstractRender.euros, float("Inf")),
}


