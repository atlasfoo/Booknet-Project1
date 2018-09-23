import hashlib
import requests

def encrypt(ps):
    pswd=hashlib.sha256()
    pswd.update(ps.encode('utf-8'))
    return pswd.hexdigest()


res = requests.get("https://www.goodreads.com/book/review_counts.json",
                   params={"key": "dwdsoTU7TSH21w2VveT9Q", "isbns": "042528011X"})
print(res.json())
print(res.json()["books"][0]["average_rating"])
