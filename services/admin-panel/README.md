# Веб-обертка для администрирования сервисов 

frontend = React + TypeScript + Vite
backend = FastAPI

## Запуск локально

1. Из директории ../admin-panel/frontend

```bash
npm run build
```
2. Из директории ../admin-panel/backend

```bash
python run_local.py
```

3. Проверка: http://localhost:8001/

## Запуск Docker

- Отдельно admin-panel

```bash
docker compose up -d --build admin-panel
```

- Все сервисы сразу

```bash
docker compose up -d --build 
```

Проверка: http://localhost:8001/

## Страницы

- Сервисы: показывает статусы подключения к сервисам
- Промты: показывает промты доступные в директории ../admin-panel/backend/prompts, можно отредактировать их содержимое (пока работает не совсем правильно)
- Конфигурация: показывает информацию о сервисах (только при подключении)
- Тестирование запросов: форма для проверки запросов (работают только GET-запросы)

Адреса сервисов на вкладке "Тестирование":

contract_extractor_url: "http://contract-extractor:8080"
globas_api_url: "http://globas-api:8000"
legal_ai_url: "http://legal-ai:8000"
m-base: "http://localhost:8000/",
base : "http://localhost:8001/"

В поле "endpoint" можно вводить как с "/", так и без

## Недоработки

- POST запросы не проходят
- Промты сейчас доступны только из admin-panel/backend/prompts, а должны импортироваться непосредственно из сервисов.
Для этого нужно писать соответсвующую логику в самих сервисах.
- Редактирование промтов не проходит в текущей версии запуска через докер, возможно стоит создать общий volume для всех сервисов
