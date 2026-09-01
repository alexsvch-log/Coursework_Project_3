@echo off
chcp 65001 > nul
echo ====================================
echo Запуск форматирования и линтеров...
echo ====================================

echo [1/4] Сортировка импортов (isort)...
call poetry run isort .

echo [2/4] Форматирование кода (black)...
call poetry run black .

echo [3/4] Проверка стиля (flake8)...
call poetry run flake8 .

echo [4/4] Проверка типов (mypy)...
call poetry run mypy src

echo ====================================
echo Все проверки завершены!
echo ====================================
pause