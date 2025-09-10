# Main.py
import os
from flask import Flask, request
import telebot
import yt_dlp

# ----------------- الإعدادات -----------------
TOKEN = os.environ.get("TELEGRAM_TOKEN")  # ضع توكن البوت هنا أو في Environment
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # رابط الويب هوك على ريندر
WEBHOOK_PATH = os.environ.get("WEBHOOK_PATH", "webhook")
PORT = int(os.environ.get("PORT", 5000))

if not TOKEN or not WEBHOOK_URL:
    raise RuntimeError("ضع TELEGRAM_TOKEN و WEBHOOK_URL في Environment")

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# ----------------- دوال التحميل -----------------
def download_twitter_video(url):
    """
    تحميل الفيديو من تويتر باستخدام yt-dlp
    """
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': 'video.mp4',
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return "video.mp4"

# ----------------- رسائل بوت -----------------
HELP_TEXT = """
مرحبا! أرسل لي رابط تغريدة تحتوي على فيديو، وسأرسل لك الفيديو مباشرة.
مثال:
https://twitter.com/username/status/1234567890
"""

# ----------------- أوامر البوت -----------------
@bot.message_handler(commands=["start", "help"])
def send_help(message):
    bot.send_message(message.chat.id, HELP_TEXT)

@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_tweet(message):
    url = message.text.strip()
    if "twitter.com" not in url:
        bot.send_message(message.chat.id, "❌ هذا ليس رابط تويتر صالح.")
        return
    
    bot.send_message(message.chat.id, "⏳ جاري تحميل الفيديو...")
    try:
        video_file = download_twitter_video(url)
        with open(video_file, "rb") as vid:
            bot.send_video(message.chat.id, vid)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ أثناء التحميل:\n{e}")

# ----------------- Webhook -----------------
@app.route(f"/{WEBHOOK_PATH}", methods=["POST"])
def webhook():
    try:
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}")
    return "", 200

def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(f"{WEBHOOK_URL}/{WEBHOOK_PATH}")
    print(f"[WEBHOOK SET] {WEBHOOK_URL}/{WEBHOOK_PATH}")

# ----------------- Main -----------------
if __name__ == "__main__":
    set_webhook()
    print(f"[RUNNING] Webhook listening on port {PORT}…")
    app.run(host="0.0.0.0", port=PORT)
