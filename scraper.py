# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import time

BASE_URL = "https://mnsht.net"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_html(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return response.text


def extract_news_links():
    html = get_html(BASE_URL)

    soup = BeautifulSoup(html, "lxml")

    links = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        # أخبار الموقع غالباً بالشكل ده
        if href.startswith("/"):

            full_url = urljoin(BASE_URL, href)

            # لازم يكون رقم خبر
            if full_url.count("/") == 3:

                if full_url not in links:
                    links.append(full_url)

    return links


def extract_article(url):

    try:

        html = get_html(url)

        soup = BeautifulSoup(html, "lxml")

        # العنوان
        title = ""

        h1 = soup.find("h1")

        if h1:
            title = h1.get_text(strip=True)

        # الصورة
        image = None

        # أول صورة داخل المقال
        article_img = soup.find("img")

        if article_img:

            src = article_img.get("src")

            if src:
                image = urljoin(BASE_URL, src)

        # المحتوى
        content = ""

        paragraphs = soup.find_all("p")

        text_list = []

        for p in paragraphs:

            txt = p.get_text(strip=True)

            if len(txt) > 30:
                text_list.append(txt)

        content = "\n".join(text_list)

        # التاريخ
        date = ""

        time_tag = soup.find("time")

        if time_tag:
            date = time_tag.get_text(strip=True)

        return {
            "title": title,
            "url": url,
            "image": image,
            "content": content,
            "date": date
        }

    except Exception as e:

        print("ERROR:", url, e)

        return None


def save_json(data):

    with open("news.json", "w", encoding="utf-8") as f:

        json.dump(data, f, ensure_ascii=False, indent=4)


def main():

    print("جاري استخراج الروابط...")

    links = extract_news_links()

    print(f"تم العثور على {len(links)} رابط\n")

    news_data = []

    for i, link in enumerate(links[:20], start=1):

        print(f"[{i}] {link}")

        article = extract_article(link)

        if article:

            news_data.append(article)

            print("TITLE:", article["title"])
            print("IMAGE:", article["image"])
            print("-" * 50)

        time.sleep(1)

    save_json(news_data)

    print("\nتم حفظ الأخبار في news.json")


if __name__ == "__main__":
    main()