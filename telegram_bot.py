import requests
import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
def send_photo(image_path, caption=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"

    with open(image_path, "rb") as photo:
        data = {
            "chat_id": CHAT_ID,
            "caption": caption or ""
        }

        files = {
            "photo": photo
        }

        requests.post(url, data=data, files=files)