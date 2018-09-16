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
