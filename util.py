import hashlib

def encrypt(ps):
    pswd=hashlib.sha256()
    pswd.update(ps)
    return pswd.hexdigest()