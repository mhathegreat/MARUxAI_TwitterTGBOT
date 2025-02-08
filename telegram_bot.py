import os
import requests
import tweepy
import logging
import google.generativeai as genai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext

# Load API keys from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")  # Needed for Twitter API v2
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Setup Twitter API v1.1 for posting tweets
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Logging
logging.basicConfig(level=logging.INFO)


def get_tweet_text(tweet_url):
    """ Fetch tweet text using Twitter API v2 """
    tweet_id = tweet_url.split("/")[-1]

    url = f"https://api.twitter.com/2/tweets/{tweet_id}?tweet.fields=text"
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            tweet_data = response.json()
            return tweet_data["data"]["text"]
        else:
            logging.error(
                f"Error fetching tweet: {response.status_code} - {response.text}"
            )
            return None
    except Exception as e:
        logging.error(f"Error fetching tweet: {e}")
        return None


async def generate_ai_response(tweet_text):
    """ Generate AI-powered response based on the tweet """
    prompt = f"Generate a cyberpunk AI cat-themed response to this tweet:\n\n{tweet_text}"

    try:
        response = model.generate_content(prompt)
        return response.text.strip() if response and hasattr(
            response, "text") else "😼🚀 $MARU to the moon!"
    except Exception as e:
        logging.error(f"Error generating AI response: {e}")
        return "😼🚀 $MARU to the moon!"


async def quote_tweet(update: Update, context: CallbackContext):
    """ Handles /quote command to generate a quote retweet """
    if not context.args:
        await update.message.reply_text("Usage: /quote TWEET_LINK")
        return

    tweet_url = context.args[0]
    tweet_text = get_tweet_text(tweet_url)

    if not tweet_text:
        await update.message.reply_text("⚠️ Could not fetch the tweet.")
        return

    ai_response = await generate_ai_response(tweet_text)
    quoted_tweet = f"{ai_response}\n\n🔗 {tweet_url}"

    try:
        api.update_status(quoted_tweet)
        await update.message.reply_text("✅ Quote retweeted successfully!")
    except Exception as e:
        await update.message.reply_text("⚠️ Error posting tweet.")
        logging.error(f"Error posting tweet: {e}")


async def reply_tweet(update: Update, context: CallbackContext):
    """ Handles /reply command to reply to a tweet """
    if not context.args:
        await update.message.reply_text("Usage: /reply TWEET_LINK")
        return

    tweet_url = context.args[0]
    tweet_id = tweet_url.split("/")[-1]
    tweet_text = get_tweet_text(tweet_url)

    if not tweet_text:
        await update.message.reply_text("⚠️ Could not fetch the tweet.")
        return

    ai_response = await generate_ai_response(tweet_text)

    try:
        api.update_status(ai_response, in_reply_to_status_id=tweet_id)
        await update.message.reply_text("✅ Replied successfully!")
    except Exception as e:
        await update.message.reply_text("⚠️ Error posting reply.")
        logging.error(f"Error posting reply: {e}")


# Start Telegram Bot
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("quote", quote_tweet))
    app.add_handler(CommandHandler("reply", reply_tweet))

    app.run_polling()


if __name__ == "__main__":
    main()
