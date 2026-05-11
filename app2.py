# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sqlite3
import time
import re

BASE_URL = "https://mnsht.net"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

# استخدام Session لتحسين السرعة واستمرارية الاتصال
session = requests.Session()
session.headers.update(HEADERS)

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
    url TEXT UNIQUE,
    image TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# =========================
# HELPERS
# =========================

def get_html():
    response = session.get(BASE_URL, timeout=20)
    response.raise_for_status()
    return response.text

def news_exists(url):
    cursor.execute("SELECT id FROM news WHERE url = ?", (url,))
    return cursor.fetchone() is not None

def clean_image_url(src):
    """تحويل رابط الصورة لصورة أصلية بأعلى جودة"""
    if not src:
        return None
    
    # تحويل الرابط لرابط كامل
    full_url = urljoin(BASE_URL, src)
    
    # 1. إزالة نظام الكاش/التصغير والرجوع للمجلد الأصلي
    full_url = full_url.replace("/UploadCache/libfiles/", "/Upload/libfiles/")
    
    # 2. إزالة أي أبعاد تصغير موجودة في الرابط باستخدام Regex
    # يبحث عن نمط مثل /400x225o/ أو /740x416/ ويحذفه
    full_url = re.sub(r'/\d+x\d+o?/', '/', full_url)
    
    return full_url

# =========================
# EXTRACT NEWS
# =========================

def extract_news(html, limit=5):
    soup = BeautifulSoup(html, "lxml")
    news_list = []
    
    # البحث عن الكروت التي تحتوي على الأخبار
    cards = soup.find_all("div", class_="item-card")
    
    count = 0
    for card in cards:
        if count >= limit:
            break
            
        try:
            a_tag = card.find("a")
            if not a_tag:
                continue
                
            url = urljoin(BASE_URL, a_tag.get("href"))
            
            # تخطي الخبر إذا كان مسجلاً مسبقاً
            if news_exists(url):
                continue
                
            # استخراج العنوان
            h3 = card.find("h3")
            title = h3.get_text(strip=True) if h3 else "بدون عنوان"
            
            # استخراج الصورة من داخل الكارد (أدق من دخول صفحة الخبر)
            img_tag = card.find("img")
            raw_img_src = None
            if img_tag:
                # محاولة جلب الصورة من src أو data-src (بسبب الـ lazy load)
                raw_img_src = img_tag.get("data-src") or img_tag.get("src")
            
            # تنظيف الصورة ورفع جودتها
            final_image = clean_image_url(raw_img_src)
            
            # استبعاد اللوجو إذا تسلل للنتائج (احتياطي)
            if final_image and "logo" in final_image.lower():
                final_image = None

            news_list.append({
                "title": title,
                "url": url,
                "image": final_image
            })
            count += 1

        except Exception as e:
            print(f"CARD ERROR: {e}")
            
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
            """, (item["title"], item["url"], item["image"]))
            conn.commit()

            print("\n🟢 NEW ARTICLE")
            print(f"TITLE: {item['title']}")
            print(f"IMAGE: {item['image']}")

        except sqlite3.IntegrityError:
            pass # الخبر موجود بالفعل

# =========================
# MAIN LOOP
# =========================

def run():
    first_run = True
    try:
        while True:
            print(f"\n🔄 Checking for news... (Time: {time.strftime('%H:%M:%S')})")
            
            try:
                html = get_html()
                
                # جلب 5 في البداية و50 في المحاولات التالية
                limit = 5 if first_run else 50
                news = extract_news(html, limit=limit)
                
                if first_run:
                    first_run = False

                if news:
                    save_news(news)
                    print(f"✅ Added {len(news)} articles.")
                else:
                    print("😴 No new updates.")

            except Exception as e:
                print(f"LOOP ERROR: {e}")

            time.sleep(60)
    except KeyboardInterrupt:
        print("\n👋 App stopped by user.")
    finally:
        conn.close()

if __name__ == "__main__":
    run()