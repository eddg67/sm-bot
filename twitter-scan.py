# Import the necessary methods from tweepy library
from pymongo import MongoClient
from TwitterFollowBot import TwitterBot
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from tweepy import API
import json
import re
import time
import random
import os
import sys
import requests

# Variables that contains the user credentials to access Twitter API
consumer_key = "wdaBHumoamxEdAjAmEc4KYo8N"  # " "
consumer_secret = "6zu64D3Lg0EGPxnhyj5OxMuHX6wzQAFWW9US2xF8NYSqdcEfKx"  #
tweet_count = 0
tweet_sent_count = 0
tweet_max = 2
tweets_sent_text = []
top_trends = []
product_ids = []
api = ""
startTime = time.time()
client = False
timeBetween = 500
sent_product_link = False
SCREEN_NAME = "tshirthustle"

track = ['shopping for t-shirt', 'Shopping For Tee', 'need tees', 'need new tees', 'need some new tee',
         'looking for tshirt', 'looking for t-shirt', 'shopping 4 t-shirts', 'need new t-shirt',
         'tshirt shopping', 'tee shopping']


def db_connect():
    global client
    if not client:
        client = MongoClient('localhost', 27017)

    return client


def runbot(my_bot):
    global track
    index = random.randrange(len(track))
    last_index = 0

    my_bot.sync_follows()

    try:
        my_bot.auto_follow_followers()

        user = my_bot.BOT_CONFIG.get('TWITTER_HANDLE')

        if user is 'tshirthustle':
            my_bot.auto_rt("@tsh", count=5)
        else:
            my_bot.auto_fav("@tshirthustle", count=5)
            my_bot.auto_rt("@tshirthustle", count=5)

        for x in range(0, 3):
            if last_index == index:
                index = random.randrange(len(track))

            my_bot.auto_follow(track[index])
            if user != 'tshirthustle' and track[index] != 'tshirthustle.com':
                my_bot.auto_rt(track[index], count=index)
                my_bot.auto_fav(track[index], count=index)
                wait()

    except IndexError:
        pass


def unfollow():
    count = 0
    followers = api.followers_ids(SCREEN_NAME)
    friends = api.friends_ids(SCREEN_NAME)
    for f in friends:
        try:
            api.create_friendship(f)
            if f not in followers:
                count += 1
                api.destroy_friendship(f)
                if count > 10:
                    break
        except IndexError:
            pass


def bot_unfollow(my_bot):
    my_bot.sync_follows()

    try:
        my_bot.auto_unfollow_nonfollowers()
    except IndexError:
        pass


def set_trends():
    global top_trends, api
    trends1 = api.trends_place(23424977)

    data = trends1[0]
    trends = data['trends']
    top_trends = [trend['name'] for trend in trends]


def increment():
    global tweet_count
    tweet_count += 1


def word_in_text(word, text):
    word = word.lower()
    text = text.lower()
    match = re.search(word, text)
    if match:
        return True
    return False


def extract_link(text):
    regex = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    match = re.search(regex, text)
    if match:
        return match.group()
    return ''


def extract_username(text):
    regex = r'@[\w]+'
    match = re.search(regex, text)
    if match:
        return match.group()
    return ''


def send_product_lk():
    global top_trends, client, sent_product_link
    content = ''
    client = db_connect()
    db = client.ss_products
    random_record = db.products.aggregate([
        {'$match': {'$and': [
            {"Big Image": {'$ne': ""}},
            {'$or': [
                {'Name': re.compile('T Shirt', re.IGNORECASE)},
                {'Name': re.compile('Tee', re.IGNORECASE)},
                {'Name': re.compile('TShirt', re.IGNORECASE)}
            ]}]
        }},
        {'$sample': {'size': 1}}
    ])

    for doc in random_record:
        product = doc
    if product['productId'] not in product_ids:
        link = 'http://tshirthustle.com/detail/' + product['productId'] + ' '
        content = link + product['Name'] + '  ' + ' '.join(top_trends)
        product_ids.append(product['productId'])
        try:
            tweet_image(product['Big Image'], content)
            sent_product_link = True
            increment()
        except Exception:
            pass

    return content


def send_tweet(tweet):
    global tweets_sent_text, startTime, sent_product_link, tweet_max, api

    prefixes = ['Sounds Like TSHIRTHUSTLE.COM ', 'Check out http://tshirthustle.com ',
                'Have U Checked TSHIRTHUSTLE.COM? ', 'Visit TSHIRTHUSTLE.COM Today ',
                'TSHIRTHUSTLE.COM Sale Today ', 'TSHIRTHUSTLE.COM Anyone? ', 'Great Tees http://tshirthustle.com ',
                'How about TSHIRTHUSTLE.COM ? ', 'Maybe we can help TSHIRTHUSTLE.COM? ']

    text = tweet["text"].replace('RT @', '')
    user = extract_username(text)
    t_id = tweet["id_str"]

    print(text)
    print(user)
    print(t_id)

    print
    len(text)
    text = text[:129]
    print
    len(text)

    if text in tweets_sent_text:
        print
        'Duplicate Tweet Caught!\n'
        return False
    else:
        print
        'Sending Tweet\n'
        tweets_sent_text.append(text)
        # api.update_status(status=text)
        increment()
        wait()
        startTime = time.time()
        if tweet_count >= tweet_max:
            # bot_unfollow(TwitterBot())
            exit()  # Tweet every 15 minutes
    return True


def tweet_image(url, message):
    global tweets_sent_text, startTime, sent_product_link, tweet_max, api
    filename = 'temp.jpg'
    request = requests.get(url, stream=True)
    if request.status_code == 200:
        with open(filename, 'wb') as image:
            for chunk in request:
                image.write(chunk)

        message = message[:129]
        api.update_with_media(filename, status=message)
        os.remove(filename)
    else:
        print("Unable to download image")


def wait():
    # type: () -> object
    min_time = 10
    max_time = 80
    if min_time > max_time:
        temp = min_time
        min_time = max_time
        max_time = temp

    wait_time = random.randint(min_time, max_time)

    if wait_time > 0:
        print("Choosing time between %d and %d - waiting %d seconds before action" % (min_time, max_time, wait_time))
        time.sleep(wait_time)

    return wait_time


def get_token():
    f = open('tshirthustle-config.txt', 'r')
    token = f.readline().split(':')[1].strip()
    f.close()

    return token


def get_secret():
    f = open('tshirthustle-config.txt', 'r')
    lines = f.readlines()
    secret = lines[1].split(':')[1].strip()
    f.close()

    return secret


def process_unfollower():
    config = ['ab-config.txt', 'tshirthustle-config.txt', 'bwaters-config.txt']
    random.shuffle(config)

    for item in config:
        print
        item + '\n'
        bot_unfollow(TwitterBot(item))
        wait()

    exit()


def process_autofollow():
    config = ['ab-config.txt', 'tshirthustle-config.txt', 'bwaters-config.txt']
    random.shuffle(config)

    for item in config:
        print
        item + '\n'
        runbot(TwitterBot(item))
        wait()

    exit()


def process_stream():
    global api
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(get_token(), get_secret())
    stream = Stream(auth, l)
    api = API(auth)
    set_trends()
    stream.filter(track=track, languages=['en'])


# This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):
    def on_error(self, status):
        print
        status

    def on_data(self, data):

        # Reading Tweets
        print
        'Reading Tweets\n'
        print
        time.time() - startTime

        print(data)

        tweets_data = []
        tweet = json.loads(data)

        # {"limit":{"track":22,"timestamp_ms":"1477757470194"}}'
        if 'limit' in tweet.keys():
            return True

        if 'retweeted' in tweet.keys():
            try:
                if tweet['retweeted']:
                    tweets_data.append(tweet)
                    send_product_lk()
                    # send_tweet(tweet)
                elif tweet['favorited']:
                    tweets_data.append(tweet)
                    send_product_lk()
                    # send_tweet(tweet)
            except IndexError:
                pass

        if time.time() - startTime >= timeBetween:
            send_product_lk()
        return True


if __name__ == '__main__':
    # This handles Twitter authetification and the connection to Twitter Streaming API

    print
    'Argument List:', str(sys.argv)
    if len(sys.argv) > 1:
        print
        sys.argv[1]
        if sys.argv[1] == 'follow':
            process_autofollow()
        elif sys.argv[1] == 'unfollow':
            process_unfollower()
        elif sys.argv[1] == 'stream':
            process_stream()
        else:
            process_stream()
            process_autofollow()

    process_stream()
