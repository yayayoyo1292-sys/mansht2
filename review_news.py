import sqlite3
import json
import os

CATEGORIES = {
    "1": "رياضة",
    "2": "سياسة",
    "3": "فن",
    "4": "اجتماعية",
    "s": "skip"
}

conn = sqlite3.connect("news.db")
cursor = conn.cursor()


try:
    cursor.execute("ALTER TABLE news ADD COLUMN reviewed INTEGER DEFAULT 0")
    conn.commit()
except sqlite3.OperationalError:
    pass


cursor.execute("""
    SELECT id, title, category, confidence 
    FROM news 
    WHERE confidence < 0.65
    AND reviewed = 0
    ORDER BY created_at DESC
    LIMIT 50
""")

rows = cursor.fetchall()

if not rows:
    print("✅ No articles to review")
    exit()

reviewed = []

for news_id, title, predicted_cat, confidence in rows:
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 60)
    print(f"📰 {title}")
    print(f"🤖 Predicted: {predicted_cat} ({confidence:.2f})")
    print("=" * 60)
    print("1 → رياضة")
    print("2 → سياسة")
    print("3 → فن")
    print("4 → اجتماعية")
    print("s → skip")
    print("q → quit")
    print()

    choice = input("اختار: ").strip().lower()

    if choice == "q":
        break
    elif choice in CATEGORIES and choice != "s":
        correct_category = CATEGORIES[choice]
        cursor.execute("""
            UPDATE news 
            SET category = ?, reviewed = 1 
            WHERE id = ?
        """, (correct_category, news_id))
        reviewed.append((title, correct_category))
        print(f"✅ Saved as: {correct_category}")
    elif choice == "s":
        cursor.execute(
            "UPDATE news SET reviewed = 1 WHERE id = ?",
            (news_id,)
        )

conn.commit()
conn.close()

print(f"\n✅ Reviewed {len(reviewed)} articles")