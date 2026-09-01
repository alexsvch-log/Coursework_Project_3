import os

from dotenv import load_dotenv

from src.models.api_adapter import HeadHunter
from src.models.bd_manager import BDManager
from src.models.bd_saver import BDSaver

# Загружаем данные из файла .env в самом начале
load_dotenv()

if __name__ == "__main__":
    # Формируем словарь конфигурации
    config = {
        "dbname": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
    }

    # 2. Исходные данные со списком компаний
    # Исходные данные для файла hh_vacancies.json
    companies_list1: list | dict = [
        {"id": 1002, "name": "Yandex"},
        {"id": 1001, "name": "Ozon Tech"},
        {"id": 1005, "name": "Sber"},
        {"id": 1004, "name": "Tinkoff"},
        {"id": 1003, "name": "VK"},
        {"id": 1007, "name": "Avito"},
        {"id": 1008, "name": "Kaspersky"},
        {"id": 1009, "name": "HeadHunter"},
        {"id": 1010, "name": "Alfa-Bank"},
        {"id": 1011, "name": "MTS Digital"},
    ]
    # Исходные данные для имитации сайта, либо для файла hh_random_api.json (у них разные названия компаний)
    companies_list2: list | dict = [
        {"id": 1, "name": "Яндекс"},
        {"id": 2, "name": "Газпром"},
        {"id": 3, "name": "VK"},
        {"id": 4, "name": "Билайн"},
        {"id": 5, "name": "МТС"},
        {"id": 6, "name": "Сбербанк"},
        {"id": 8, "name": "Финам"},
        {"id": 9, "name": "Ozon"},
        {"id": 10, "name": "Тинькофф"},
    ]
    # Склеиваем все имена через запятую и пробел
    names_str1 = ", ".join(c["name"] for c in companies_list1)
    names_str2 = ", ".join(c["name"] for c in companies_list2)

    # Заранее объявляем переменную со значением по умолчанию
    selected_companies = companies_list1

    # === НАЧАЛО ДИАЛОГА С ПОЛЬЗОВАТЕЛЕМ ===

    print("Выберите список компаний, вакансии в которых вы хотите найти:\n")
    user_input = input(f'Если "{names_str1}" введите 1\nЕсли "{names_str2}" введите 2\n==>  ')
    if user_input == "1":
        selected_companies = companies_list1
        target_filename = "hh_vacancies.json"
        is_force_local = True  # Для первого списка сразу читаем файл
        print(f"Поиск вакансий будет в следующих компаниях:\n{names_str1}")
    else:
        selected_companies = companies_list2
        target_filename = "hh_random_api.json"
        is_force_local = False  # Для второго списка сначала пробуем сеть
        print(f"Поиск вакансий будет в следующих компаниях:\n{names_str2}")

    try:
        # 3. Извлекаем список ID из выбранного пользователем набора данных
        employer_ids = [int(company["id"]) for company in selected_companies]

        # 4. Запрашиваем данные через сетевой адаптер HeadHunter
        hh_api = HeadHunter()
        vacancies_data = hh_api.fetch_data(
            employer_ids=employer_ids, filename=target_filename, force_local=is_force_local, per_page=20
        )

        # 5. Инициализируем DBSaver для записи результатов в базу данных
        db_saver = BDSaver(db_config=config)

        # 6. Запускаем последовательный импорт в таблицы PostgreSQL
        db_saver.create_tables()
        db_saver.clear_tables()

        # Сохраняем именно те организации, по которым вели поиск
        db_saver.save_organizations(companies=selected_companies)

        # Сохраняем полученный массив вакансий
        db_saver.save_vacancies(vacancies_list=vacancies_data)
        #
        # print("\n[Успех]: Конвейер импорта успешно отработал!")
        #
        # # === ВЫВОД  ТАБЛИЦ ПО 5 СТРОК ===
        # db_saver.print_table_preview(table_name="organizations", limit=5)
        # db_saver.print_table_preview(table_name="vacancies", limit=5)

        # === ИНИЦИАЛИЗАЦИЯ И РАБОТА С DB_MANAGER ===
        db_manager = BDManager(db_config=config)
        # Диалог с пользователем с выбором действий
        print(
            "Вакансии по выбранным вами компаниям успешно загружены/nВыберите вариант, "
            "какую информацию вы бы хотели посмотреть (введите соответствующую цифру):"
        )
        print("_________________________________________________________________________")
        print("1. Список всех запрошенных компаний и количество вакансий у каждой компании (0 -вакансии отсутствуют)")
        print(
            "2. Список всех вакансий с дополнительной информацией (наименование компании, название вакансии, "
            "вилка зарплаты, ссылка на вакансию)"
        )
        print(
            "3. Средняя зарплата по всем вакансиям "
            "(выводит среднюю зарплату независимо от компании рабтодателя по каждой вакансии)"
        )
        print("4. Список всех вакансий, у которых зарплата выше средней по всем вакансиям")
        print("5. Список всех вакансий, в названии которых содержатся введенный вами текст, например 'python'")

        user_choice = input("==> ").strip()
        if user_choice == "5":
            user_input = input("Введите текст для поиска (по умолчанию 'Python'): ").strip()
            keyword = user_input or "Python"
            print(f"\n🔍 Производится поиск вакансий по ключевому слову '{keyword}':")

            # Получаем список вакансий в переменную
            vacancies = db_manager.get_vacancies_with_keyword(keyword)

            # Проверяем, пустой ли список
            if not vacancies:
                print(f"По ключевому слову '{keyword}' вакансий не найдено.")
            else:
                # Если вакансии есть, запускаем цикл для вывода
                for vac in vacancies:
                    title, comp_name, min_sal, max_sal, url = vac
                    print(f"Вакансия: {title} | Компания: {comp_name} | ЗП: {min_sal}-{max_sal} | Ссылка: {url}")

        elif user_choice == "1":
            # 1. Тест: Количество вакансий по компаниям
            print("\n📊 Статистика вакансий по компаниям:")
            for company, count in db_manager.get_companies_and_vacancies_count():
                print(f" - {company}: {count} вакансий")

        elif user_choice == "2":
            # 2. Тест: всех вакансий с указанием названия компании, названия вакансии и зарплаты и ссылки на вакансию
            for vac in db_manager.get_all_vacancies():
                comp_name, title, min_sal, max_sal, url = vac
                print(f"Компания: {comp_name} | Вакансия: {title} | ЗП: {min_sal}-{max_sal} руб.| Ссылка: {url}")

        elif user_choice == "3":
            # 3. Тест: Средняя зарплата по уникальным вакансиям
            for vac in db_manager.get_avg_salary():
                title, avg_salary = vac
                print(f"Вакансия: {title} | Средня ЗП: {avg_salary} руб.")

        elif user_choice == "4":
            # 4. Тест: Вакансии с зарплатой выше средней по уникальным зп
            print("\n📈 Вакансии с зарплатой выше средней:")
            for vac in db_manager.get_vacancies_with_higher_salary():
                comp_name, title, min_sal, max_sal, vac_avg, title_avg, url = vac
                print(
                    f"Компания: {comp_name} | Вакансия: {title} | Зарплата: {min_sal}-{max_sal} руб. "
                    f"(Средняя зп для вакансии: {int(vac_avg)} руб.) | "
                    f"Средняя по всем предложениям: {int(title_avg)} руб. | Ссылка: {url}"
                )

        else:
            print("\nЗапрос не выбран")

    except Exception as ex:
        print(f"\n[Критическая ошибка] во время работы конвейера: {ex}")
