import psycopg2


class BDSaver:
    """Класс для создания таблиц и сохранения данных о вакансиях в PostgreSQL."""

    def __init__(self, db_config: dict):
        """Инициализирует параметры подключения к базе данных."""
        self.db_config = db_config

    def create_tables(self) -> None:
        """Создает таблицы organizations и vacancies с необходимыми связями."""
        query_organizations = """
            CREATE TABLE IF NOT EXISTS organizations (
                id INT PRIMARY KEY,
                name VARCHAR(255) NOT NULL
            );
        """
        query_vacancies = """
            CREATE TABLE IF NOT EXISTS vacancies (
                id INT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                min_sal INT,
                max_sal INT,
                url TEXT,
                org_id INT,
                CONSTRAINT fk_organization
                    FOREIGN KEY(org_id)
                    REFERENCES organizations(id)
                    ON DELETE CASCADE
            );
        """

        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query_organizations)
                cursor.execute(query_vacancies)
        # print("Таблицы organizations и vacancies успешно проверены/созданы.")

    def save_organizations(self, companies: list) -> None:
        """Заполняет таблицу organizations из переданного списка словарей."""
        query = """
            INSERT INTO organizations (id, name)
            VALUES (%s, %s)
            ON CONFLICT (id) DO NOTHING;
        """

        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                for company in companies:
                    cursor.execute(query, (int(company["id"]), company["name"]))
        # print(f"Организации ({len(companies)} шт.) успешно обработаны.")

    def save_vacancies(self, vacancies_list: list) -> None:
        """Принимает список вакансий (массив словарей) и сохраняет их в базу данных."""
        query = """
            INSERT INTO vacancies (id, title, min_sal, max_sal, url, org_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
        """

        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                # Итерируемся напрямую по переданному списку
                for item in vacancies_list:
                    vac_id = int(item.get("id") or 0)
                    title = item.get("name")

                    employer_info = item.get("employer") or {}
                    org_id = int(employer_info.get("id") or 0)

                    salary_info = item.get("salary") or {}
                    min_sal = salary_info.get("from")
                    max_sal = salary_info.get("to")
                    url = item.get("alternate_url")

                    cursor.execute(query, (vac_id, title, min_sal, max_sal, url, org_id))
        # print(f"Вакансии ({len(vacancies_list)} шт.) успешно обработаны.")

    # def print_table_preview(self, table_name: str, limit: int = 5) -> None:
    #     """Выводит первые N строк из указанной таблицы в консоль. Потом удалить"""
    #     query = f"SELECT * FROM {table_name} LIMIT %s;"
    #
    #     with psycopg2.connect(**self.db_config) as conn:
    #         with conn.cursor() as cursor:
    #             try:
    #                 cursor.execute(query, (limit,))
    #                 columns = [desc[0] for desc in cursor.description]
    #                 rows = cursor.fetchall()
    #
    #                 print(f"\n📋 Предварительный просмотр таблицы '{table_name}' (макс. {limit} строк):")
    #                 print("-" * 50)
    #                 print(f"Столбцы: {columns}")
    #                 print("-" * 50)
    #
    #                 if not rows:
    #                     print("[Таблица пуста]")
    #                 for row in rows:
    #                     print(row)
    #                 print("-" * 50)
    #
    #             except Exception as e:
    #                 print(f"⚠️ Не удалось прочитать таблицу {table_name}: {e}")

    def clear_tables(self) -> None:
        """Полностью очищает таблицы перед новым импортом данных."""
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                # CASCADE автоматически очистит и связанные вакансии
                cursor.execute("TRUNCATE TABLE organizations RESTART IDENTITY CASCADE;")
                cursor.execute("TRUNCATE TABLE vacancies RESTART IDENTITY;")
        # print("🧹 Таблицы успешно очищены для перезаписи данных.")
