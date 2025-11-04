# Admin Panel

Админ-панель предоставляет единый веб-интерфейс для мониторинга и обслуживания
сервисов экосистемы. Приложение включает в себя фронтенд (React + Vite)
и бэкенд (FastAPI), которые можно запускать как локально, так и в Docker.

## Структура каталогов

```
services/admin-panel/
├── README.md               # краткая инструкция по запуску
├── backend/                # FastAPI-приложение и статический билд фронтенда
│   ├── config.py           # загрузка настроек из переменных окружения
│   ├── core/               # бизнес-логика и вспомогательные утилиты
│   ├── routes/             # обработчики HTTP-маршрутов
│   ├── prompts/            # исходные файлы промптов
│   └── static/             # собранный фронтенд для продакшена
└── frontend/               # исходный код клиентского приложения
    ├── src/                # компоненты React и API-клиенты
    └── vite.config.ts      # конфигурация сборки
```

## Запуск

### Локально

1. Соберите фронтенд:
   ```bash
   cd services/admin-panel/frontend
   npm install
   npm run build
   ```
2. Запустите FastAPI-приложение:
   ```bash
   cd ../backend
   python run_local.py
   ```
3. Откройте http://localhost:8001/ в браузере.

### В Docker

```bash
docker compose up -d --build admin-panel
```

## Бэкенд (FastAPI)

Бэкенд реализован на FastAPI и предоставляет REST API, агрегирующее данные из
других сервисов. Точка входа находится в `backend/main.py`, где создаётся
экземпляр приложения, подключаются CORS middleware и регистрируются маршруты
для различных функциональных модулей.(services/admin-panel/backend/main.py)

### Конфигурация

Модуль `config.py` загружает настройки из переменных окружения (URL сервисов,
порт, режим отладки) с помощью `pydantic-settings`. Значения по умолчанию
подходят для запуска в Docker-сети или локально. (services/admin-panel/backend/config.py)

### Вспомогательные модули

- `core/services.py` описывает поддерживаемые сервисы, функции проверки
  /health-эндпоинтов и сборку сводного статуса. В `SERVICE_REGISTRY` перечислены
  Contract Extractor, Globas API и Legal AI; дополнительные алиасы (например,
  `m-base`) доступны для прокси-запросов.(services/admin-panel/backend/core/services.py)
- `core/prompts.py` инкапсулирует работу с файловыми промптами: чтение,
  перечисление и сериализацию структур, чтобы фронтенд мог редактировать
  содержимое через API. (services/admin-panel/backend/core/prompts.py)

### Маршруты

| Префикс           | Обработчик                              | Назначение |
|-------------------|-----------------------------------------|------------|
| `/api/health`     | `routes/health.py`                      | Возвращает состояние самой панели и агрегированные статусы сервисов.(services/admin-panel/backend/routes/health.py) |
| `/api/services`   | `routes/services.py`                    | Делегирует запросы к Contract Extractor (конфигурация, схема, модели) и возвращает статусы сервисов. (services/admin-panel/backend/routes/services.py) |
| `/api/prompts`    | `routes/prompts.py`                     | Позволяет перечислять и обновлять файлы промптов Contract Extractor и Legal AI. (services/admin-panel/backend/routes/prompts.py) |
| `/api/config`     | `routes/config.py`                      | Запрашивает конфигурации сервисов и возвращает результат в унифицированном виде, даже если сервис недоступен. (services/admin-panel/backend/routes/config.py) |
| `/api/proxy`      | `routes/proxy.py`                       | Универсальный прокси для ручного тестирования запросов из интерфейса, поддерживает JSON и multipart-форматы. (services/admin-panel/backend/routes/proxy.py) |

Фронтенд-сборка из каталога `backend/static` автоматически раздаётся FastAPI,
если каталог присутствует. В режиме разработки при отсутствии сборки сервер
возвращает подсказку о необходимости выполнить `npm run build`. (services/admin-panel/backend/main.py)

## Фронтенд (React + Vite)

Клиентское приложение инициализируется в `frontend/src/main.tsx`, где React
приложение монтируется в DOM и оборачивается в `BrowserRouter` для возможной
будущей навигации. (services/admin-panel/frontend/src/main.tsx)

Основной компонент `App.tsx` управляет выбором вкладок, загрузкой данных через
кастомный хук и отображением соответствующих панелей: статусы сервисов,
редактор промптов, конфигурации и тестер прокси-запросов. (services/admin-panel/frontend/src/App.tsx)

### Хуки и типы

- `useLazyResource` — обёртка над асинхронными загрузчиками, которая запускает
  загрузку при активации вкладки и предоставляет методы обновления, состояние
  загрузки и ошибки. (services/admin-panel/frontend/src/core/hooks/useLazyResource.ts)
- `core/types.ts` и `types/tabs.ts` — централизованные TypeScript-интерфейсы
  для обмена данными между компонентами и API-клиентами. (services/admin-panel/frontend/src/core/types.ts) (services/admin-panel/frontend/src/types/tabs.ts)

### API-клиент

Модуль `core/api/client.ts` определяет вспомогательные функции `requestJson` и
`postJson`, которые бросают `HttpError` при неуспешном ответе, а `core/api/routes.ts`
содержит карту используемых backend-эндпоинтов. (services/admin-panel/frontend/src/core/api/client.ts) (services/admin-panel/frontend/src/core/api/routes.ts)
Поверх них построены специализированные клиенты для каждой функциональной 
вкладки (`features/*/api.ts`). (services/admin-panel/frontend/src/features/services/api.ts) (services/admin-panel/frontend/src/features/prompts/api.ts) (services/admin-panel/frontend/src/features/config/api.ts) (services/admin-panel/frontend/src/features/proxy/api.ts)

### Компоненты

- **AppHeader** — верхняя панель навигации с переключением вкладок. (services/admin-panel/frontend/src/components/layout/AppHeader.tsx)
- **ServiceStatusPanel** — карточки со статусами и деталями подключённых
  сервисов, включая версию и дополнительные поля. (services/admin-panel/frontend/src/features/services/components/ServiceStatusPanel.tsx)
- **PromptList** + **Modal** — список файлов промптов с возможностью открыть
  модальное окно для редактирования содержимого и отправки на сервер. (services/admin-panel/frontend/src/features/prompts/components/PromptList.tsx) (services/admin-panel/frontend/src/components/ui/Modal.tsx)
- **ConfigPanel** — отображает конфигурационные пары ключ/значение по сервисам
  и позволяет повторно загрузить данные. (services/admin-panel/frontend/src/features/config/components/ConfigPanel.tsx)
- **ProxyTester** — форма для ручного тестирования HTTP-запросов через
  серверный прокси с поддержкой JSON и загрузки файлов. (services/admin-panel/frontend/src/features/proxy/components/ProxyTester.tsx)

Глобальные стили и оформление компонентов описаны в `styles/globals.css`, что
обеспечивает единый внешний вид карточек, кнопок, модалей и форм ввода. (services/admin-panel/frontend/src/styles/globals.css)

## Работа с промптами

Файлы промптов находятся в `backend/prompts`. Для Contract Extractor поддерживается
фиксированный набор файлов (system, user templates, summary и т. д.), а также
дополнительные Markdown-руководства в подпапке `fields`. Для Legal AI список
ограничен набором шаблонов `analyze`, `business` и `overview`. API выдаёт
содержимое этих файлов и позволяет обновлять их через POST `/api/prompts/update`.

## Прокси-запросы

Эндпоинт `/api/proxy` позволяет из интерфейса отправлять запросы к любому из
зарегистрированных сервисов. Бэкенд проверяет тип контента, поддерживает JSON и
multipart, а также возвращает статус-код, заголовки и тело ответа, что удобно
для отладки интеграций. (services/admin-panel/backend/routes/proxy.py)

## Известные ограничения

- Прокси обрабатывает GET и POST запросы; другие методы вернут ошибку 405.
- При запуске в Docker редактирование промптов требует общей volume-настройки,
  иначе изменения не будут сохраняться в постоянное хранилище (см. README).
- Поддержка POST-запросов в UI ограничена: тело можно задать JSON-строкой или
  прикрепить один файл.

## Дополнительные материалы

- [README admin-panel](../services/admin-panel/README.md) — краткая инструкция.
- `docs/architecture.md` — общая архитектура платформы.