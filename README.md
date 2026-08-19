# Tender Status Tracker

Простой backend-сервис для трекинга статусов тендеров.

## Быстрый старт

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Запустите приложение:

```bash
uvicorn app.main:app --reload
```

3. Откройте OpenAPI:
- `http://127.0.0.1:8000/docs`

## Переменные окружения

По умолчанию используется `sqlite:///./tender.db`.

Для PostgreSQL:

```bash
set DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/dbname
```

и перезапустите приложение.

## Ключевые сущности

- `Tender` — тендер с текущим статусом
- `TenderStatusHistory` — журнал изменений статуса

## Статусы и переходы

- `DRAFT` — Черновик
- `ACTIVE` — Активен
- `WON` — Выигран
- `LOST` — Проигран

Разрешенные переходы:

- `DRAFT -> ACTIVE`
- `ACTIVE -> WON`
- `ACTIVE -> LOST`

С `WON` и `LOST` новые переходы запрещены (терминальные статусы).

## Эндпоинты

| Метод | Путь | Описание |
| --- | --- | --- |
| `POST` | `/tenders` | Создать тендер (статус по умолчанию `DRAFT`) |
| `GET` | `/tenders` | Список тендеров, фильтр по `status`, постраничный вывод `skip`/`limit` |
| `GET` | `/tenders/{id}` | Получить тендер |
| `PATCH` | `/tenders/{id}` | Обновить `title`, `description`, `customer` |
| `PATCH` | `/tenders/{id}/status` | Обновить статус с валидацией перехода и записью истории |
| `GET` | `/tenders/{id}/history` | История изменений статуса по тендеру |

## Тесты

```bash
python -m pytest tests/ -v
```

## Лицензия

Проект распространяется по лицензии MIT.
