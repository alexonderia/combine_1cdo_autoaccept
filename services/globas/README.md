# Synthetic Globas API (Docker Compose)

Стек для локального прототипа «синтетического Globas»: PostgreSQL + FastAPI + гибкая генерация данных.

## Запуск
```bash
docker compose up -d --build
```

Проверка:
- API: http://localhost:8000/health
- Документация: http://localhost:8000/docs

## Инициализация базы (создать с нуля)
```bash
curl -X POST http://localhost:8000/admin/init \
  -H "Content-Type: application/json" \
  -d '{"config_path": "/app/config/config.example.yml"}'
```
Ответ вернёт количество записей по таблицам.

## Добавить N записей
```bash
curl -X POST http://localhost:8000/admin/add \
  -H "Content-Type: application/json" \
  -d '{
        "n": 50,
        "distribution": {"red": 15, "yellow": 20, "green": 15},
        "config_path": "/app/config/config.example.yml"
      }'
```

## Посмотреть последние 10 компаний
```bash
curl "http://localhost:8000/admin/tail"
```
Можно изменить количество записей, указав `?limit=20` (максимум 100).

## Выгрузка контрагентов в CSV
- Последние 100 компаний в файл:
```bash
curl "http://localhost:8000/admin/export-companies?limit=100" -o companies_100.csv
```
- Все компании (может быть большой файл):
```bash
curl "http://localhost:8000/admin/export-companies" -o companies_all.csv
```

## Получить данные по имени или ИНН
- По имени (substring, регистр не важен):
```bash
curl "http://localhost:8000/search?name=Альфа"
```
- По ИНН (точное совпадение):
```bash
curl "http://localhost:8000/by-inn/1234567890"
```

## Как формируется JSON чек-листа (`/check` и `include_checklist`)
Формирование ответа делает функция [`build_checklist_document`](api/app/main.py).  Она возвращает объект с реквизитами компании, списком пунктов памятки и метаданными проверки.  Каждый пункт содержит код, текст вопроса (берётся из файла локализации), нормализованный ответ и дополнительные данные (например, числовые показатели, детализацию по налоговым обязательствам и т.д.).

Если по какому-либо пункту нет данных в таблице `due_diligence`, в JSON явно указывается «Нет данных», а статус помечается как `unknown`.

### Эндпоинт `/check`
- Получить чек-лист по названию:
  ```bash
  curl "http://localhost:8000/check?name=Альфа"
  ```
- Получить по ИНН:
  ```bash
  curl "http://localhost:8000/check?inn=1234567890"
  ```

Возвращаемая структура (`checklist_document`) включает:

```json
{
  "company": {
    "id": "uuid",
    "name": "ООО \"Пример\"",
    "inn": "1234567890",
    "ogrn": "1234567890123",
    "status": "ACTIVE",
    "okved_main": "62.01",
    "reg_date": "2020-05-10",
    "address": "г. Москва, ул. Примерная, д. 1",
    "risk_scores": {
      "grade": "green",
      "solvency": 82,
      "reliability": 76,
      "compliance_flag": "none"
    }
  },
  "items": [
    {
      "code": "tax_debt_and_obligations",
      "question": "Нет ли у контрагента долгов по налогам, исполнительных листов ФССП, кредитным линиям и лизингу",
      "answer": {
        "code": "bool_no",
        "text": "Нет",
        "status": "ok",
        "raw_value": false
      },
      "details": [
        {
          "code": "tax_debt",
          "label": "Налоговые задолженности",
          "answer": {"code": "exists_no", "text": "Нет", "status": "ok", "raw_value": false}
        }
      ]
    }
  ],
  "metadata": {
    "title": "Чек-лист к памятке о порядке проведения должной осмотрительности",
    "checked_at": "2024-05-04",
    "checked_by": null,
    "digital_signature": null,
    "locale": "ru-RU",
    "field_labels": {
      "checked_at": "Дата проверки",
      "checked_by": "Кто проверял",
      "digital_signature": "Подпись (ПЭП)"
    }
  }
}
```

* `answer.status` показывает итоговую оценку пункта (`ok` — признаков риска нет, `issue` — обнаружены факторы риска, `unknown` — данных нет).
* Дополнительные числа, списки документов и расшифровки передаются в полях `data` и `details`.

## Детальная карточка (ID компании)
```bash
curl "http://localhost:8000/company/<uuid>"
```

## Конфигурация
Редактируйте `config/config.example.yml`:
- `classes.distribution` — состав по классам (red/yellow/green)
- `dictionaries.*` — пути к словарям (можно подменить на свои, по умолчанию `/app/config/ruRU/dictionaries/*`)
- `risk.*`, `grade_rules` — логика скоринга
- `ownership.*`, `sanctions.*`, `financials.*`, `courts.*` — генерация доменов
- `due_diligence.*` — параметры синтетических проверок по чек-листу

При желании создайте свой файл `config.yml` и укажите его в `config_path`.

### Настройка текстов для чек-листа
- Скопируйте `config/ruRU/checklist_texts.example.yml` в `config/ruRU/checklist_texts.yml` и при необходимости скорректируйте формулировки вопросов и ответов.
- Файл автоматически подхватывается при запуске контейнера (путь `/app/config/ruRU/checklist_texts.yml`).
- Если файл лежит в другом месте, задайте переменную окружения `CHECKLIST_TEXTS_PATH` с абсолютным путём.
- В блоке `answers` можно изменить базовые варианты «Да/Нет», «Имеется/Не имеется», текст для отсутствующих данных и т.п.
- В блоке `questions` находятся формулировки пунктов памятки.
- В блоке `exposure_labels` задаются человеко-читаемые названия для детализированной расшифровки блока `tax_debt_and_obligations`.
- В блоке `metadata` можно переименовать заголовок чек-листа и подписи к сервисным полям («Дата проверки», «Кто проверял», «Подпись (ПЭП)»).
