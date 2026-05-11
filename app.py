# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sqlite3
import time

BASE_URL = "https://mnsht.net"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}
print("APP STARTED")
print("WAITING FOR NEWS...")
# =========================
# DATABASE
# =========================

conn = sqlite3.connect("news.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT UNIQUE,
    url TEXT,
    image TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()


# =========================
# GET HTML
# =========================

def get_html():

    response = requests.get(
        BASE_URL,
        headers=HEADERS,
        timeout=20
    )

    response.raise_for_status()

    return response.text


# =========================
# EXTRACT NEWS
# =========================

def extract_news(html):

    soup = BeautifulSoup(html, "lxml")

    news_list = []

    cards = soup.find_all("div", class_="item-card")

    for card in cards:

        try:

            a = card.find("a")

            if not a:
                continue

            href = a.get("href")

            if not href:
                continue

            url = urljoin(BASE_URL, href)

            # TITLE
            h3 = card.find("h3")

            title = h3.get_text(strip=True)

            # IMAGE
            img = card.find("img")

            image = None

            if img:

                image = (
                    img.get("data-src")
                    or img.get("src")
                )

                if image:
                    image = urljoin(BASE_URL, image)

            news_list.append({
                "title": title,
                "url": url,
                "image": image
            })

        except Exception as e:

            print("CARD ERROR:", e)

    return news_list


# =========================
# SAVE TO DATABASE
# =========================

def save_news(news):

    for item in news:

        try:

            cursor.execute("""
            INSERT INTO news (title, url, image)
            VALUES (?, ?, ?)
            """, (
                item["title"],
                item["url"],
                item["image"]
            ))

            conn.commit()

            print("\n🟢 خبر جديد:")
            print(item["title"])
            print(item["image"])

        except sqlite3.IntegrityError:

            # الخبر موجود بالفعل
            pass


# =========================
# MAIN LOOP
# =========================

def run():

    while True:

        try:

            print("\n🔄 Checking for new news...")

            html = get_html()

            news = extract_news(html)

            print(f"Found {len(news)} articles")

            save_news(news)

        except Exception as e:

            print("ERROR:", e)

        # كل دقيقة
        time.sleep(60)


if __name__ == "__main__":

    run()