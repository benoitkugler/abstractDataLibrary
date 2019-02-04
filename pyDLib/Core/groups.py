"""Defines list structure with sorting and search functions"""

from . import formats


class sortableListe(list):
    """Minimal implementation to work with GUI models"""

    def sort(self, attribut, order=False):
        """
        Implément un tri par attrbut.

        :param str attribut: Nom du champ concerné
        :param bool order: Ordre croissant ou décroissant
        """
        value_default = formats.ASSOCIATION[attribut][3]

        if type(value_default) is str:  # case insensitive sort
            get = lambda d : (d[attribut] or value_default).casefold()
        elif type(value_default) is dict: #can't sort dicts
            get = lambda d : sorted((d[attribut] or value_default).values())
        else:
            get = lambda d : d[attribut] or value_default

        list.sort(self, key=get, reverse=order)

    def sort_by_niveau(self):
        def g(acces):
            return self.get_info(Id=acces.Id).get('niveau', 0)

        list.sort(self, key=g, reverse=True)

    def get_info(self, key=None, Id=None):
        return {}

    def index_from_id(self,Id):
        """Return the row of given Id if it'exists, otherwise None. Only works with pseudo-acces"""
        try:
            return [a.Id for a in self].index(Id)
        except IndexError:
            return



class Collection(sortableListe):
    """List of acces. Implements search function.
    Ensure unicity of ids.
    `infos` attribut stores rendering meta data on accesses (font, color)
    """

    @classmethod
    def from_ids(cls,acces_class,base,ids):
        return cls( acces_class(base, i) for i in set(ids))

    def __init__(self, l_acces=()):
        super().__init__(l_acces)
        self.infos = {}

    def clear(self):
        list.__init__(self)
        self.infos = {}

    def append(self, acces, **kwargs):
        """Append acces to list. Quite slow since it checks uniqueness.
        kwargs may set `info` for this acces.
        """
        if acces.Id in set(ac.Id for ac in self):
            raise ValueError("Acces id already in list !")
        list.append(self, acces)
        if kwargs:
            self.infos[acces.Id] = kwargs

    def remove_id(self,key):
        """Suppress acces with id = key"""
        self.infos.pop(key, "")
        new_l = [a for a in self if not (a.Id == key)]
        list.__init__(self, new_l)

    def __repr__(self):
        if len(self) > 0:
            s = "Collection of  " + str(type(self[0])) + " : \n "
            return s + "\n".join(f"Id : {p.Id}" for p in self)
        else:
            return "Empty collection !"

    def __str__(self):
        return "\n".join(str(a) for a in self)

    def get_info(self, key=None, Id=None) -> dict:
        """Returns information associated with Id or list index"""
        if key is not None:
            Id = self[key].Id
        return self.infos.get(Id,{})

    def set_info(self, Id, key, value):
        current_info = self.infos.get(Id, {})
        current_info[key] = value
        self.infos[Id] = current_info

    def recherche(self, pattern, entete):
        """Performs a search field by field, using functions defined in formats.
        Matchs are marked with info[`font`]

        :param pattern: String to look for
        :param entete: Fields to look into
        :return: Nothing. The collection is changed in place
        """

        new_liste = []
        sub_patterns = pattern.split(" ")
        for p in self:
            d_font = {att: False for att in entete}
            row_valid = True
            for sub_pattern in sub_patterns:
                found = False
                for att in entete:
                    fonction_recherche = formats.ASSOCIATION[att][1]
                    attr_found = bool(fonction_recherche(p[att], sub_pattern))
                    if attr_found:
                        found = True
                        d_font[att] = True
                if not found:
                    row_valid = False
                    break
            if row_valid:
                new_liste.append(p)
                info = dict(self.get_info(Id=p.Id),font=d_font)
                self.infos[p.Id] = info

        list.__init__(self, new_liste)


    def extend(self, collection):
        """Merges collections. Ensure uniqueness of ids"""
        l_ids = set([a.Id for a in self])
        for acces in collection:
            if not acces.Id in l_ids:
                list.append(self,acces)
                info = collection.get_info(Id=acces.Id)
                if info:
                    self.infos[acces.Id] = info





