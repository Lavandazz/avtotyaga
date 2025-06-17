import requests
import os
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/117.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

response = requests.get('https://автотяга.рф/catalog/isuzu/', headers=headers)
short_url = 'https://автотяга.рф'
soup = BeautifulSoup(response.text, 'html.parser')
BASE_PATH = 'categories_auto'
FILENAME = "auto_parts.xlsx"

# создание основкой папки для ексель файлов
if not os.path.exists(BASE_PATH):
    os.makedirs(BASE_PATH, exist_ok=True)


def find_categories_and_link():
    """ Получаем модели, категории и ссылки на них транспорта """
    products = soup.find_all('div', class_='card-category__inner')
    dict_categories = {}

    for product in products:
        # Извлекаем название категории
        name_category_auto = product.find('h4').text.strip()
        # Ищем все элементы <li> с классом card-category__list-item
        podclass_items = product.find_all('li', class_='card-category__list-item')
        # Создаем список для хранения подкатегорий
        podcategories = []

        for item in podclass_items:
            # Извлекаем ссылку и название подкатегории
            a_element = item.find('a')
            if a_element:
                link_url = a_element.get('href')
                name_part = a_element.text.strip().replace('/', '_')
                podcategories.append((name_part, link_url))

        # Добавляем данные в словарь
        dict_categories[name_category_auto] = podcategories

    return dict_categories


def create_folders_and_parse_data(dict_categories: dict):
    for category, subcategories in dict_categories.items():
        # Создаем папки для категории автомобилей
        folder_name = category.replace('/', '_').replace(' ', '_')
        os.makedirs(f'{BASE_PATH}/{folder_name}', exist_ok=True)

        for subcategory, url in subcategories:
            list_parts = []
            page = 1
            while True:
                # Формируем URL для текущей страницы
                pagen_url = f"{short_url}{url}?PAGEN_1={page}"
                print(f"Парсим страницу {page}: {pagen_url}")

                # Загружаем страницу
                response_url = requests.get(pagen_url)
                soup_for_url = BeautifulSoup(response_url.content, 'html.parser')
                parts = soup_for_url.find_all("div", class_="card-main")  # поиск запчастей

                for part in parts:
                    auto_part = part.find("h3").text.strip()
                    price_part = (part.find("p", class_="card-main__price").
                                  text.strip().replace('₽', '').replace(' ', ''))
                    link_part = part.find("h3").find('a').get('href')
                    link_part = short_url + link_part
                    list_parts.append((auto_part, price_part, link_part))
                paginator_btn = soup_for_url.find("a", class_="pagination__item is-active")

                if paginator_btn:
                    if int(paginator_btn.text) != page:
                        break
                    print(paginator_btn.text)
                    page += 1  # Переходим на следующую страницу
                else:
                    break

            if list_parts:
                print(list_parts)
                save_to_excel(folder_name, subcategory, list_parts)


def save_to_excel(folder_name: str, subcategory: str, data: list):
    """Сохраняет данные в Excel-файл."""
    import pandas as pd
    # Создаем DataFrame из списка данных
    df = pd.DataFrame(data, columns=["Название запчасти", "Цена", "Ссылка"])

    # Создаем имя файла
    file_name = f"{subcategory.replace('/', '_').replace(' ', '_')}.xlsx"
    file_path = os.path.join(BASE_PATH, folder_name, file_name)

    # Сохраняем DataFrame в Excel
    df.to_excel(file_path, index=False)
    print(f"Файл {file_path} успешно создан.")


dict_cat = find_categories_and_link()
create_folders_and_parse_data(dict_cat)
