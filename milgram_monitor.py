import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import os

URL = "https://milgram.jp/judge/result/season_3"

ALL_PRISONERS = {
    "002": "Yuno",
    "003": "Fuuta",
    "004": "Muu",
    "007": "Kazui",
    "008": "Amane",
    "009": "Mikoto",
    "010": "Kotoko"
}

def fetch_voting_data():
    """Получает данные голосования со страницы"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(URL, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text()
        
        voting_percentages = re.findall(r'(\d+\.?\d*)\s*%\s*―', page_text)
        
        print(f"Найдено процентов голосования: {voting_percentages}")
        
        if not voting_percentages:
            
            all_percentages = re.findall(r'(\d+\.?\d*)\s*%', page_text)
            print(f"Все проценты на странице: {all_percentages}")
            
            voting_percentages = [p for p in all_percentages if 5 <= float(p) <= 95 and float(p) != 50.0]
            print(f"Отфильтрованные проценты (5-95%, не 50%): {voting_percentages}")
        
        percentages = [float(p) for p in voting_percentages]
        
        valid_percentages = [p for p in percentages if p != 50.0]
        
        print(f"Валидные проценты (исключая 50%): {valid_percentages}")
        
        current_time = datetime.now()
        date_str = current_time.strftime("%Y-%m-%d")
        time_str = current_time.strftime("%H:%M:%S")
        
        results = []
        
        prisoner_numbers = ["002", "003", "004", "007", "008", "009", "010"]
        percentage_index = 0
        
        for number in prisoner_numbers:
            if percentage_index < len(valid_percentages):
                name = ALL_PRISONERS.get(number, f"Prisoner {number}")
                
                innocent_percent = valid_percentages[percentage_index]
                guilty_percent = round(100.0 - innocent_percent, 2)
                
                results.append({
                    "Имя": f"{name} ({number})",
                    "Дата": date_str,
                    "Время": time_str,
                    "Процент невиновен": innocent_percent,
                    "Процент виновен": guilty_percent
                })
                
                percentage_index += 1
        
        if len(results) == 0:
            print("⚠️  Не найдено ни одного валидного процента")
            return None
            
        return results
    
    except Exception as e:
        print(f"Ошибка при получении данных: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_to_excel(data, filename="milgram_voting_data.xlsx"):
    """Добавляет данные в единый Excel файл"""
    df_new = pd.DataFrame(data)
    
    if os.path.exists(filename):
        try:
            df_existing = pd.read_excel(filename)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_excel(filename, index=False)
            print(f"✓ Данные добавлены в существующий файл {filename}")
            print(f"  Всего записей в файле: {len(df_combined)}")
        except Exception as e:
            print(f"⚠️  Ошибка при чтении файла: {e}")
            print(f"   Создаю новый файл...")
            df_new.to_excel(filename, index=False)
    else:
        df_new.to_excel(filename, index=False)
        print(f"✓ Создан новый файл {filename}")
    
    return filename

if __name__ == "__main__":
    print("=" * 60)
    print(f"ЗАПУСК МОНИТОРИНГА - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    data = fetch_voting_data()
    
    if data:
        save_to_excel(data, "milgram_voting_data.xlsx")
        
        print("\n📊 ТЕКУЩИЕ РЕЗУЛЬТАТЫ:")
        print(f"{'─' * 60}")
        print(f"  Отслеживается заключенных: {len(data)}")
        print(f"{'─' * 60}")
        for entry in data:
            print(f"  {entry['Имя']:15} → "
                  f"Невиновен: {entry['Процент невиновен']:6.2f}% | "
                  f"Виновен: {entry['Процент виновен']:6.2f}%")
        print(f"{'─' * 60}")
    else:
        print("❌ Не удалось получить данные")
    
    print("\n✓ Готово!")
