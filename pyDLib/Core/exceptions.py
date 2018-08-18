class ConnexionError(Exception):
    """In case of networkin error"""
    pass


class StructureError(Exception):
    """In case of data integrity error"""
    pass