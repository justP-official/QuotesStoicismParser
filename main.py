import csv
import time
import random

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://stoicfork.online/citations/"
OUTPUT_FILE = "quotes.csv"

MAX_PAGES = 150
MIN_DELAY = 1
MAX_DELAY = 5

AUTHOR_CLASSES = {
    "fullwidth",
    "text-right",
    "mb-1",
    "-mt-2",
    "text-gray-500",
}

def get_page_url(page: int) -> str:
    if page == 1:
        return BASE_URL

    return f"{BASE_URL}page/{page}/"


def parse_page(session: requests.Session, page: int) -> list[dict]:
    """Извлекает цитаты и авторов с одной страницы сайта."""
    url = get_page_url(page)

    response = session.get(url, timeout=20)

    if response.status_code == 404:
        return []

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    blockquotes = [
        blockquote
        for blockquote in soup.find_all("blockquote")
        if blockquote.find_parent("blockquote") is None
    ]

    results = []

    for blockquote in blockquotes:
        # Собираем текст всех параграфов цитаты.
        paragraphs = blockquote.find_all("p")

        text_parts = [
            p.get_text(" ", strip=True)
            for p in paragraphs
            if p.get_text(strip=True)
        ]

        if not text_parts:
            continue

        # Объединяем параграфы, сохраняя разделение на абзацы.
        quote_text = "\n".join(text_parts)

        # Ищем div с нужными классами.
        author = ""

        for div in blockquote.find_all("div"):
            classes = set(div.get("class", []))

            if AUTHOR_CLASSES.issubset(classes):
                author = div.get_text(" ", strip=True)
                break

        results.append({
            "text": quote_text,
            "author": author,
        })

    return results


def main():
    quotes = []
    session = requests.Session()

    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
    })

    for page in range(1, MAX_PAGES + 1):
        try:
            page_quotes = parse_page(session, page)

        except requests.RequestException as error:
            print(f"Ошибка при загрузке страницы {page}: {error}")
            break

        # Нет цитат — считаем, что страницы закончились.
        if not page_quotes:
            print(f"Цитаты не найдены на странице {page}. Завершение.")
            break

        # Присваиваем уникальные последовательные ID.
        for quote in page_quotes:
            quote["quote_id"] = len(quotes) + 1
            quotes.append(quote)

        print(
            f"Страница {page}: найдено {len(page_quotes)} цитат. "
            f"Всего: {len(quotes)}"
        )

        # Не отправляем запросы слишком часто.
        time.sleep(random.randint(MIN_DELAY, MAX_DELAY))

    if not quotes:
        print("Цитаты не собраны. CSV-файл не создан.")
        return

    # Сохраняем данные в CSV.
    with open(
        OUTPUT_FILE,
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["quote_id", "text", "author"],
        )

        writer.writeheader()
        writer.writerows(quotes)

    print(f"\nГотово! Сохранено {len(quotes)} цитат в {OUTPUT_FILE}")


if __name__ == "__main__":
    main()