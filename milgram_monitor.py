import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import os

URL = "https://milgram.jp/judge/result/season_3"
FILENAME = "milgram_voting_data.xlsx"

NAMES = {
    "001": "Haruka",
    "002": "Yuno",
    "003": "Fuuta",
    "004": "Muu",
    "005": "Shidou",
    "006": "Mahiru",
    "007": "Kazui",
    "008": "Amane",
    "009": "Mikoto",
    "010": "Kotoko"
}

ENDED_MARKER = "投票は終了"


def fetch_voting_data():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(URL, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = "utf-8"
        html = response.text

        parts = re.split(r"sub_judge_result_pc_label_(\d{3})\.png", html)

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        results = []

        for i in range(1, len(parts), 2):
            number = parts[i]
            block_text = BeautifulSoup(parts[i + 1], "html.parser").get_text(" ")
            name = NAMES.get(number, f"Prisoner {number}")

            innocent_match = re.search(r"―\s*(\d+(?:\.\d+)?)\s*%", block_text)
            guilty_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*―", block_text)

            if not innocent_match or not guilty_match:
                print(f"{name} ({number}): нет данных голосования, пропуск")
                continue

            innocent = float(innocent_match.group(1))
            guilty = float(guilty_match.group(1))

            if ENDED_MARKER in block_text:
                print(f"{name} ({number}): голосование завершено, пропуск")
                continue

            if innocent == 50.0 and guilty == 50.0:
                print(f"{name} ({number}): голосование не началось, пропуск")
                continue

            print(f"{name} ({number}): активно")
            results.append({
                "Имя": f"{name} ({number})",
                "Дата": date_str,
                "Время": time_str,
                "Процент невиновен": innocent,
                "Процент виновен": guilty
            })

        return results if results else None

    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        return None


def save_to_excel(data, filename=FILENAME):
    df_new = pd.DataFrame(data)

    if os.path.exists(filename):
        df_existing = pd.read_excel(filename)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_combined = df_new

    df_combined.to_excel(filename, index=False)
    print(f"Сохранено в {filename}, всего записей: {len(df_combined)}")


if __name__ == "__main__":
    print(f"Запуск: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    data = fetch_voting_data()

    if data:
        save_to_excel(data)
        for entry in data:
            print(f"{entry['Имя']}: невиновен {entry['Процент невиновен']:.2f}% | "
                  f"виновен {entry['Процент виновен']:.2f}%")
    else:
        print("Активных голосований не найдено, файл не изменён")
