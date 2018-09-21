import hashlib

def encrypt(ps):
    pswd=hashlib.sha256()
    pswd.update(ps.encode('utf-8'))
    return pswd.hexdigest()