import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, cast

import requests

# http://78.17.12.30:8000/api/vacancies?employer_id=1,6,10&text=Python&per_page=20


class BaseAPIAdapter(ABC):
    """Абстрактный базовый класс для всех API адаптеров."""

    @abstractmethod
    def fetch_data(self, *args: Any, **kwargs: Any) -> Any:
        pass


class HeadHunter(BaseAPIAdapter):
    """Сетевой адаптер для получения данных с сайта, имитирующего HeadHunter (с автоматическим fallback-режимом
    - в случае недоступности сайта подключаются резервные jSON файлы с информацией)."""

    def __init__(self) -> None:
        self.url: str = "http://78.17.12.30:8000/api/vacancies"
        self.headers: Dict[str, str] = {"User-Agent": "VacancyAdapterApp/1.0"}

    def fetch_data(
        self,
        employer_ids: List[int],
        filename: str,  # <--- Добавляем обязательный аргумент для имени файла
        page: int = 0,
        per_page: int = 20,
        force_local: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """Пытается получить данные с сайта по списку ID работодателей.
        При сбое возвращает информацию из локального jSON файла.
        """
        # Формируем полный путь к выбранному файлу внутри папки data
        file_path = os.path.join("data", filename)

        # ЕСЛИ ФЛАГ TRUE — СРАЗУ ИДЕМ К ФАЙЛУ
        if force_local:
            return self._load_local_file(file_path)

        # Иначе выполняем стандартный сетевой запрос
        employer_str = ",".join(map(str, employer_ids))

        params: Dict[str, Any] = {"employer_id": employer_str, "per_page": per_page, "page": page}

        try:
            response = requests.get(url=self.url, params=params, headers=self.headers, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data and isinstance(data, dict) and "items" in data:
                items = data.get("items")
                if isinstance(items, list):
                    return items

            print(f"⚠️ Сервер вернул некорректную структуру данных на странице {page}.")
            return self._load_local_file(file_path)  # <--- Передаем путь

        except requests.RequestException as e:
            print(f"⚠️ Сетевой запрос к API не удался. Причина: {e}")
            return self._load_local_file(file_path)  # <--- Передаем путь

        except Exception as e:
            print(f"⚠️ Ошибка при обработке сетевого ответа: {e}")
            return self._load_local_file(file_path)  # <--- Передаем путь

    def _load_local_file(self, data_file_path: str) -> List[Dict[str, Any]]:
        """Загружает резервный список вакансий из указанного локального JSON-файла."""
        print(data_file_path)
        if os.path.exists(data_file_path):
            try:
                with open(data_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        print(f"📦 [Fallback] Успешно загружен резервный файл: {data_file_path}")
                        return cast(List[Dict[str, Any]], data)
                    elif isinstance(data, dict) and "items" in data:
                        items = data.get("items")
                        if isinstance(items, list):
                            # print(f"📦 [Fallback] Успешно загружен резервный массив из ответа: {data_file_path}")
                            return cast(List[Dict[str, Any]], items)
            except Exception as e:
                print(f"⚠️ Предупреждение: Не удалось прочитать резервный файл {data_file_path}: {e}")
        else:
            print(f"⚠️ Предупреждение: Локальный резервный файл не найден по пути: {data_file_path}")

        return []
