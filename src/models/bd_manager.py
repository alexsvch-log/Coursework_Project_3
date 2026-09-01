from typing import List, Tuple, cast

import psycopg2


class BDManager:
    """Класс для выполнения аналитических выборок из базы данных PostgreSQL."""

    def __init__(self, db_config: dict):
        """Инициализирует параметры подключения к БД."""
        self.db_config = db_config

    def get_companies_and_vacancies_count(self) -> List[Tuple[str, int]]:
        """Получает список всех компаний и количество вакансий у каждой компании.
        Использует LEFT JOIN, чтобы показать даже те компании, у которых сейчас 0 вакансий.
        """
        query = """
            SELECT o.name, COUNT(v.id) AS vacancies_count
            FROM organizations o
            LEFT JOIN vacancies v ON o.id = v.org_id
            GROUP BY o.name
            ORDER BY vacancies_count DESC;
        """
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return cast(List[Tuple[str, int]], cursor.fetchall())

    def get_all_vacancies(self) -> List[Tuple[str, str, int, int, str]]:
        """Получает список всех вакансий с указанием названия компании,
        названия вакансии, зарплаты (от и до) и ссылки на вакансию.
        """
        query = """
            SELECT o.name, v.title, v.min_sal, v.max_sal, v.url
            FROM vacancies v
            JOIN organizations o ON v.org_id = o.id
            ORDER BY o.name;
            LIMIT 10; -- <--- База данных сразу вернет только 10 строк, сэкономив память и время
        """
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return cast(List[Tuple[str, str, int, int, str]], cursor.fetchall())

    def get_avg_salary(self) -> List[Tuple[str, float]]:
        """Считает среднюю зарплату для каждого уникального наименования вакансии:
        1. Сначала вычисляет среднюю ЗП для каждой строки из её вилки.
        2. Затем группирует по уникальным названиям и считает среднее для каждой уникальной вакансии.
        """
        query = """
            SELECT
                raw_vacancies.title,
                ROUND(AVG(raw_vacancies.vacancy_avg)::numeric, 2) AS title_avg
            FROM (
                -- Шаг 1: Считаем среднее из вилки для абсолютно каждой вакансии
                SELECT
                    title,
                    ((COALESCE(min_sal, max_sal) + COALESCE(max_sal, min_sal)) / 2.0) AS vacancy_avg
                FROM vacancies
                WHERE min_sal IS NOT NULL OR max_sal IS NOT NULL
            ) AS raw_vacancies
            -- Шаг 2: Группируем по уникальному названию
            GROUP BY raw_vacancies.title
            ORDER BY title_avg DESC; -- Сортировка от больших зарплат к меньшим
        """
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                # fetchall() вернет список всех уникальных вакансий и их средних ЗП
                return cast(List[Tuple[str, float]], cursor.fetchall())

    def get_vacancies_with_higher_salary(self) -> List[Tuple[str, str, int, int, float, float, str]]:
        """Получает список вакансий, у которых средняя ЗП выше, чем
        средняя ЗП для этой же уникальной вакансии (по её названию).
        """
        query = """
            SELECT
                o.name,
                v.title,
                v.min_sal,
                v.max_sal,
                -- 1. Средняя ЗП текущей конкретной вакансии (середина вилки)
                ((COALESCE(v.min_sal, v.max_sal) + COALESCE(v.max_sal, v.min_sal)) / 2.0) AS vac_avg,
                -- 2. Средняя ЗП для ВСЕХ вакансий с таким же названием (берем из подзапроса)
                ut.title_avg,
                v.url
            FROM vacancies v
            JOIN organizations o ON v.org_id = o.id
            -- Подключаем подзапрос, который считает среднее по уникальным title
            JOIN (
                SELECT
                    title,
                    AVG((COALESCE(min_sal, max_sal) + COALESCE(max_sal, min_sal)) / 2.0) AS title_avg
                FROM vacancies
                WHERE min_sal IS NOT NULL OR max_sal IS NOT NULL
                GROUP BY title
            ) AS ut ON v.title = ut.title
            -- Условие: средняя вакансии выше, чем средняя для её уникального названия
            WHERE ((COALESCE(v.min_sal, v.max_sal) + COALESCE(v.max_sal, v.min_sal)) / 2.0) > ut.title_avg
            ORDER BY v.title ASC, vac_avg DESC;
        """
        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return cast(List[Tuple[str, str, int, int, float, float, str]], cursor.fetchall())

    def get_vacancies_with_keyword(self, keyword: str) -> List[Tuple[str, str, int, int, str]]:
        """Получает список всех вакансий, в названии которых содержатся коючевое слово.
        Поиск регистронезависимый (благодаря ILIKE в PostgreSQL).
        """
        query = """
            SELECT v.title, o.name, v.min_sal, v.max_sal, v.url
            FROM vacancies v
            JOIN organizations o ON v.org_id = o.id
            WHERE v.title ILIKE %s
            ORDER BY v.title;
        """
        # Оборачиваем ключевое слово в знаки процента % для поиска подстроки
        search_param = f"%{keyword}%"

        with psycopg2.connect(**self.db_config) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (search_param,))
                return cast(List[Tuple[str, str, int, int, str]], cursor.fetchall())
