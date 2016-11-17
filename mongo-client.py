from TwitterFollowBot import TwitterBot

my_bot = TwitterBot()

my_bot.auto_unfollow_nonfollowers()
my_bot.auto_follow("tshirthustle")
my_bot.auto_follow_followers()

my_bot.auto_fav("tshirthustle", count=10000)

my_bot.auto_rt("tshirts", count=10000)


