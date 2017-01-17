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
import sys

# Variables that contains the user credentials to access Twitter API
access_token = "2871836001-gq2L0XN28Vaakbq7ydTOXM3FsYFEfrwxXuItTdg" #"793165501614678016-TCIFNBzYM70EH0AQTCObrHBUTAjKair"
access_token_secret = "MZhKeFpiEHZTDK4Fgno6hRXDKDmmW6GumDwFI7RfEfEEw" #
consumer_key = "wdaBHumoamxEdAjAmEc4KYo8N" #" "
consumer_secret = "6zu64D3Lg0EGPxnhyj5OxMuHX6wzQAFWW9US2xF8NYSqdcEfKx" #
tweet_count = 0
tweet_sent_count = 0
tweet_max = 3
tweets_sent_text = []
top_trends = []
api = ""
startTime = time.time()
fileHandle = open('tweets-dialog.txt', 'w')
client = False
timeBetween = 500
sent_product_link = False
SCREEN_NAME = "tshirthustle"

track = ['tshirt', 'tee-shirt', 'shirts', 'tshirthustle', 'shopping for t-shirt', 'Shopping For Tee', 'need tees',
         'looking for tshirt', 'looking for t-shirt', 'gift idea', 'shopping 4 t-shirts', 'cos-play']


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

        my_bot.auto_fav("tshirthustle", count=5)
        my_bot.auto_rt("tshirthustle", count=5)

        for x in range(0, 3):
            if last_index == index:
                index = random.randrange(len(track))

            my_bot.auto_follow(track[index])
            my_bot.auto_rt(track[index], count=index)
            my_bot.auto_fav(track[index], count=index)
            wait()

        #bot_unfollow(my_bot)
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
    global top_trends
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


def create_product_lk():
    global top_trends, client
    client = db_connect()
    db = client.ss_products
    random_record = db.products.aggregate([
        {'$match': {'Name': re.compile('T Shirt', re.IGNORECASE)}},
        {'$sample': {'size': 1}}
    ])

    for doc in random_record:
        product = doc

    link = 'http://tshirthustle.com/detail/' +product['productId'] + ' '
    content = link + product['Name'] + ' '.join(top_trends)

    return content


def send_tweet(text):
    global tweets_sent_text, startTime, fileHandle, sent_product_link, tweet_max

    prefixes = ['Sounds Like TSHIRTHUSTLE.COM ','Check out http://tshirthustle.com ',
                'Have U Checked TSHIRTHUSTLE.COM? ', 'Visit TSHIRTHUSTLE.COM Today ',
                'TSHIRTHUSTLE.COM Sale Today ', 'TSHIRTHUSTLE.COM Anyone? ', 'Great Tees http://tshirthustle.com ']

    if sent_product_link:
        text = prefixes[random.randrange(len(prefixes))] + text
    else:
        text = create_product_lk()
        sent_product_link = True

    print len(text)
    text = text[:129]
    print len(text)

    if text in tweets_sent_text:
        print 'Duplicate Tweet Caught!\n'
        return False
    else:
        print 'Sending Tweet\n'
        tweets_sent_text.append(text)
        api.update_status(status=text)
        increment()
        wait()
        startTime = time.time()
        if tweet_count >= tweet_max:
            fileHandle.close()
            #bot_unfollow(TwitterBot())
            exit()  # Tweet every 15 minutes
    return True


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


# This is a basic listener that just prints received tweets to stdout.
class StdOutListener(StreamListener):
    def on_error(self, status):
        fileHandle.close()
        print status

    def on_data(self, data):

        # Reading Tweets
        print 'Reading Tweets\n'
        print time.time() - startTime

        print data

        fileHandle.write(data+'\n')

        tweets_data = []
        tweet = json.loads(data)

        # {"limit":{"track":22,"timestamp_ms":"1477757470194"}}'
        if 'limit' in tweet.keys():
            return True

        if 'retweeted' in tweet.keys():
            try:
                if tweet['retweeted']:
                    tweets_data.append(tweet)
                    send_tweet(tweet["text"])
                elif tweet['favorited']:
                    tweets_data.append(tweet)
                    send_tweet(tweet["text"])
                elif word_in_text('TSHIRTHUSTLE', tweet['text']):
                    tweets_data.append(tweet)
                    send_tweet(tweet["text"])
            except IndexError:
                pass

        if time.time() - startTime >= timeBetween:
            if word_in_text('RT @', tweet['text']):
                send_tweet(tweet["text"])
            elif word_in_text('TSHIRTHUSTLE', tweet['text']):
                send_tweet(tweet["text"])
        return True


if __name__ == '__main__':
    # This handles Twitter authetification and the connection to Twitter Streaming API
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    stream = Stream(auth, l)
    api = API(auth)
    set_trends()

    #print 'Argument List:', str(sys.argv)

    runbot(TwitterBot('tshirthustle-config.txt'))
    wait()
    runbot(TwitterBot())
    wait()

    runbot(TwitterBot('bwaters-config.txt'))

    # bot_unfollow(TwitterBot('tshirthustle-config.txt'))
    # bot_unfollow(TwitterBot())

    # This line filter Twitter Streams to capture data by the keywords: 'tshirt', 'tees', 'tee-shirt', 'shirts'
    stream.filter(track=track)

