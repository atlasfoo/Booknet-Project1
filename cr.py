import hashlib

ps='1234'.encode('utf-8')
pswd=hashlib.sha256()
pswd.update(ps)
print(pswd.hexdigest())