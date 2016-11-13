from pymongo import MongoClient
import random
from math import floor,ceil

client = False

def db_connect():
    return MongoClient('localhost', 27017)

client = db_connect()

print client

db = client.ss_products

print db
count = db.products.count()
rand = random.randint(1, count)  # rand will be a floating point between 0 to 1.
print floor(rand * db.products.count())
random_record = db.products.aggregate([{'$sample': {'size': 1}}])

for doc in random_record:
    print(doc['productId'])


for doc in db.products.find({}).limit(1).skip(rand * db.products.count()):
    print(doc)
# db.products.find_one({ 'random' => { '$gte' => rand } })







