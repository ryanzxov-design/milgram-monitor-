import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
import os

# URL страницы с результатами
URL = "https://milgram.jp/judge/result/season_3"

# Имена заключенных (только активные в 3 сезоне)
PRISONERS = {
    "002": "Yuno",
    "003": "Fuuta",
    "004": "Muu"
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
        
        # Ищем паттерн "XX.XX% ―" который используется для результатов голосования
        voting_percentages = re.findall(r'(\d+\.?\d*)\s*%\s*―', page_text)
        
        print(f"Найдено процентов голосования: {voting_percentages}")
        
        if not voting_percentages:
            # Если не нашли с "―", пробуем другой способ
            all_percentages = re.findall(r'(\d+\.?\d*)\s*%', page_text)
            print(f"Все проценты на странице: {all_percentages}")
            
            # Фильтруем: берем только проценты от 5 до 95 (исключаем 0, 50, 100)
            voting_percentages = [p for p in all_percentages if 5 <= float(p) <= 95 and float(p) != 50.0]
            print(f"Отфильтрованные проценты (5-95%, не 50%): {voting_percentages}")
        
        # Конвертируем в float и берем только первые 3
        percentages = [float(p) for p in voting_percentages[:3]]
        
        if len(percentages) < 3:
            print(f"⚠️  Найдено только {len(percentages)} процентов, ожидается 3")
            return None
        
        current_time = datetime.now()
        date_str = current_time.strftime("%Y-%m-%d")
        time_str = current_time.strftime("%H:%M:%S")
        
        results = []
        
        # Создаем данные для каждого заключенного
        prisoner_list = list(PRISONERS.items())
        for idx, (number, name) in enumerate(prisoner_list):
            if idx < len(percentages):
                # ВАЖНО: на странице показан процент ВИНОВНОСТИ (赦さない)
                guilty_percent = percentages[idx]
                innocent_percent = round(100.0 - guilty_percent, 2)
                
                results.append({
                    "Имя": f"{name} ({number})",
                    "Дата": date_str,
                    "Время": time_str,
                    "Процент невиновен": innocent_percent,
                    "Процент виновен": guilty_percent
                })
        
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
        # Если файл существует, читаем его и добавляем новые данные
        try:
            df_existing = pd.read_excel(filename)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_excel(filename, index=False)
            print(f"✓ Данные добавлены в существующий файл {filename}")
        except Exception as e:
            print(f"⚠️  Ошибка при чтении файла: {e}")
            print(f"   Создаю новый файл...")
            df_new.to_excel(filename, index=False)
    else:
        # Создаем новый файл
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
        for entry in data:
            print(f"  {entry['Имя']:15} → "
                  f"Невиновен: {entry['Процент невиновен']:6.2f}% | "
                  f"Виновен: {entry['Процент виновен']:6.2f}%")
        print(f"{'─' * 60}")
    else:
        print("❌ Не удалось получить данные")
    
    print("\n✓ Готово!")
