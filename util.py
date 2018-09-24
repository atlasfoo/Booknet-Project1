import hashlib
import requests

def encrypt(ps):
    pswd=hashlib.sha256()
    pswd.update(ps.encode('utf-8'))
    return pswd.hexdigest()


for i in range(5-1):
    print(i)
