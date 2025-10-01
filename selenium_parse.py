import asyncio
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.error import TimedOut

# === Налаштування Telegram ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

# === Цільова сторінка ===
URL = "https://coins.bank.gov.ua/catalog.html"

# === Шлях до файла з ID монет ===
SEEN_FILE = "seen.txt"

bot = Bot(token=BOT_TOKEN)

def load_seen_ids():
    """Завантажує ID вже надісланих монет з файла"""
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        # Парсимо лише ID до символу '|'
        return set(line.split("|")[0].strip() for line in f.readlines())

def save_seen_coin(coin_id, name):
    """Додає ID та назву нової монети до файла"""
    with open(SEEN_FILE, "a", encoding="utf-8") as f:
        f.write(f"{coin_id}|{name}\n")

async def check_new_coins():
    print("🔍 Перевіряємо сайт за допомогою Selenium...")

    from selenium.webdriver.chrome.options import Options  # додай сюди

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(URL)

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".label3.product_label"))
        )
    except Exception as e:
        print("❌ Помилка очікування елементів:", e)
        driver.quit()
        return

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, 'html.parser')
    print(f"✅ Отримано довжину HTML: {len(html)}")

    coins = soup.find_all("div", class_="product")
    print(f"🪙 Знайдено монет: {len(coins)}")

    seen_ids = load_seen_ids()

    for coin in coins:
        # Перевіряємо чи є мітка "у продажу"
        label_div = coin.find("div", class_="product_labels")
        if not label_div:
            continue
        product_label = label_div.find("div", class_="label3 product_label")
        if not product_label:
            continue
        if "у продажу" not in product_label.text.lower():
            continue

        description = coin.find("div", class_="p_description")
        if not description:
            continue

        checkbox = description.find("input", id=lambda x: x and x.startswith("compare_"))
        if not checkbox:
            continue

        coin_id = checkbox["id"].replace("compare_", "")
        if coin_id in seen_ids:
            continue  # вже бачили цю монету

        name_tag = description.find("a", class_="model_product")
        name = name_tag.text.strip() if name_tag else "Невідома монета"
        link = name_tag['href'] if name_tag else "#"
        full_link = f"https://coins.bank.gov.ua{link}"

        p_tags = description.find_all("p")
        year_or_date = " | ".join(p.text.strip() for p in p_tags if p.text.strip())

        message = f"🆕 Нова монета!\n\n🪙 *{name}*\n📆 {year_or_date}\n🔗 [Переглянути]({full_link})"
        print("📨 Відправляємо повідомлення в Telegram:")
        print(message)

        try:
            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
            await asyncio.sleep(1)  # затримка, щоб не перевантажити API
            save_seen_coin(coin_id, name)  # Зберігаємо ID та назву монети
        except TimedOut:
            print("⚠️ Помилка: таймаут при відправці повідомлення. Пропускаємо.")

if __name__ == "__main__":
    asyncio.run(check_new_coins())
