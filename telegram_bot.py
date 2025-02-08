import os
import tweepy
import logging
import google.generativeai as genai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes

# Load API keys from .env file
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Setup Twitter API
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Logging
logging.basicConfig(level=logging.INFO)


def generate_ai_response(tweet_text):
    """ Generate AI-powered response based on the tweet """
    prompt = f"Generate a cyberpunk AI cat-themed response to this tweet:\n\n{tweet_text}"

    try:
        response = model.generate_content(prompt)
        return response.text.strip() if response and hasattr(
            response, "text") else "😼🚀 $MARU to the moon!"
    except Exception as e:
        logging.error(f"Error generating AI response: {e}")
        return "😼🚀 $MARU to the moon!"


def get_tweet_text(tweet_url):
    """ Extract tweet text from a URL """
    tweet_id = tweet_url.split("/")[-1]
    try:
        tweet = api.get_status(tweet_id, tweet_mode="extended")
        return tweet.full_text
    except Exception as e:
        logging.error(f"Error fetching tweet: {e}")
        return None


def quote_tweet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Handles /quote command to generate a quote retweet """
    if len(context.args) != 1:
        update.message.reply_text("Usage: /quote TWEET_LINK")
        return

    tweet_url = context.args[0]
    tweet_text = get_tweet_text(tweet_url)

    if not tweet_text:
        update.message.reply_text("⚠️ Could not fetch the tweet.")
        return

    ai_response = generate_ai_response(tweet_text)
    quoted_tweet = f"{ai_response}\n\n🔗 {tweet_url}"

    try:
        api.update_status(quoted_tweet)
        update.message.reply_text("✅ Quote retweeted successfully!")
    except Exception as e:
        update.message.reply_text("⚠️ Error posting tweet.")
        logging.error(f"Error posting tweet: {e}")


def reply_tweet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Handles /reply command to reply to a tweet """
    if len(context.args) != 1:
        update.message.reply_text("Usage: /reply TWEET_LINK")
        return

    tweet_url = context.args[0]
    tweet_id = tweet_url.split("/")[-1]
    tweet_text = get_tweet_text(tweet_url)

    if not tweet_text:
        update.message.reply_text("⚠️ Could not fetch the tweet.")
        return

    ai_response = generate_ai_response(tweet_text)

    try:
        api.update_status(ai_response, in_reply_to_status_id=tweet_id)
        update.message.reply_text("✅ Replied successfully!")
    except Exception as e:
        update.message.reply_text("⚠️ Error posting reply.")
        logging.error(f"Error posting reply: {e}")


# Start Telegram Bot
async def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("quote", quote_tweet))
    application.add_handler(CommandHandler("reply", reply_tweet))

    await application.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())