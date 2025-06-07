# Тестовое задание для Lesta Game Start


### 📄Описание
Веб-приложение для анализа текстов. Пользователь может загрузить текстовый файл через форму на веб-странице. После обработки отображается таблица из 50 слов с наибольшим значением IDF, в которой указано:
- Слово
- TF (частота встречаемости в тексте)
- IDF (обратная частота документа)

### ⚙️ Стек технологий
- FastAPI 0.115.0
- Jinja2 3.1.6
- Python-multipart 0.0.20
- Psycopg2-binary 2.9.10
- Python-dotenv 1.0.1
- Uvicorn 0.32.1
- SQLAlchemy 2.0.30
- asyncpg 0.29.0
- PostgreSQL 15

### 📁 Структура проекта
project/<br />
├── app/  <span style="color:green"># Основная директория приложения.</span><br />
│   ├── auth/
│   │   ├── auth_services.py<span style="color:green"># Функции регистрации и получения токена</span><br />
│   │   └── dependencies.py<span style="color:green"># Функции проверки пользователя</span><br />
│   ├── crud/
│   │   ├── collection_crud.py<span style="color:green"># CRUD по коллекциям</span><br />
│   │   ├── document_crud.py<span style="color:green"># CRUD по документам</span><br />
│   │   └── user_crud.py<span style="color:green"># CRUD по пользователям</span><br />
│   ├── models/
│   │   ├── user.py<span style="color:green"># Модель пользователя</span><br />
│   │   ├── collection.py<span style="color:green"># Модель коллекций</span><br />
│   │   └── document.py<span style="color:green"># Модель пользователя</span><br />
│   ├── routes/
│   │   ├── api_routes.py<span style="color:green"># Роуты для API</span><br />
│   │   └── html_routes.py<span style="color:green"># Роуты для web</span><br />
│   ├── static/ <span style="color:green"># Статические файлы</span><br />
│   │   ├── 404img.png<span style="color:green"># Изображение для страницы 404</span><br />
│   │   ├── logo.gif<span style="color:green"># gif анимация в шапке сайта</span><br />
│   │   └── styles.css <span style="color:green"># Таблица стилей</span><br />
│   ├── templates/ <span style="color:green"># Папка с HTML-шаблонами</span><br />
│   │   ├── 404.html <span style="color:green"># Страница ошибки 404 файла</span><br />
│   │   ├── account.html <span style="color:green"># Страница настроек аккаунта</span><br />
│   │   ├── base.html <span style="color:green"># Страница-основа для всех страниц файла</span><br />
│   │   ├── index.html <span style="color:green"># Начальная форма для загрузки файла</span><br />
│   │   ├── login.html <span style="color:green"># Страница для входа в аккаунт</span><br />
│   │   ├── myfiles.html <span style="color:green"># Страница со всеми файлами пользователя</span><br />
│   │   ├── output.html <span style="color:green"># Результаты анализа текста</span><br />
│   │   └── register.html <span style="color:green"># Страница регистрации</span><br />
│   ├── database.py <span style="color:green"># Настройка подключения к базе данных</span><br />
│   ├── main.py <span style="color:green"># Основное приложение FastAPI</span><br />
│   ├── sсhemas.py <span style="color:green"># Pydantic-схемы</span><br />
│   └── services.py <span style="color:green"># Логика обработки текста</span><br />
├── .env <span style="color:green"># Переменные окружения</span><br />
├── .gitignore<span style="color:green"># Указание Git игнорируемых файлов</span><br />
├── compose.yaml <span style="color:green"># Docker Compose для запуска</span><br />
├── Dockerfile <span style="color:green"># Инструкция сборки образа приложения</span><br />
├── init_db.py <span style="color:green"> # Инициализация базы данных</span><br />
├── README.md <span style="color:green"># Документация проекта</span><br />
├── README_OPENAPI_CLIENT.md <span style="color:green"># Документация для запуска OpenAPI клиента</span><br />
├── requirements.txt <span style="color:green"># Зависимости Python</span><br />
└── wait-for-postgres.sh<span style="color:green"> # Скрипт ожидания запуска PostgreSQL</span><br />

### Project run

- Run the application:  
```bash
docker-compose up --build
```
Приложение будет доступно по адресу: http://localhost:8000

## 📊 Метрики
Доступны по эндпоинту api/metrics. Пример:

```json
{
  "total_uploads": 3,
  "unique_words": 178,
  "documents":8,
  "collections":2
}
```
### 🔁 Версия приложения
Версия: 0.0.2<br />
Эндпоинт: /version

## 📑 Swagger / OpenAPI

Swagger-документация доступна по адресу: [http://localhost:8000/docs](http://localhost:8000/docs)

## 📌 Эндпоинты API

### 🔐 Пользователи

- `POST /api/login` — авторизация по логину и паролю
- `POST /api/register` — регистрация нового пользователя
- `GET /api/logout` — завершение сессии (удаление cookie)
- `PATCH /api/user/{user_id}` — смена пароля
- `DELETE /api/user/{user_id}` — удаление пользователя

### 📄 Документы

- `GET /api/documents` — список загруженных документов
- `GET /api/documents/{document_id}` — содержимое документа
- `GET /api/documents/{document_id}/statistics` — TF/IDF статистика по документу
- `DELETE /api/documents/{document_id}` — удалить документ

### 📚 Коллекции

- `GET /api/collections` — список коллекций с документами
- `GET /api/collections/{collection_id}` — список документов в коллекции
- `GET /api/collections/{collection_id}/statistics` — TF/IDF статистика по коллекции
- `POST /api/collection/{collection_id}/{document_id}` — добавить документ в коллекцию
- `DELETE /api/collection/{collection_id}/{document_id}` — удалить документ из коллекции

### 📝 CHANGELOG
#### Версия 0.0.1
#### ✅ Базовая реализация:

- Загрузка и обработка текстовых файлов

- Расчёт TF и псевдо-IDF

- Отображение 50 слов с наибольшим IDF

- Запуск как Python приложения

#### 🆕 Изменения по сравнению с изначальной версией:

- Добавлен эндпоинт /status, показывающий работоспособность приложения

- Добавлен эндпоинт /version, отображающий версию приложения

- 📊 Добавлен эндпоинт /metrics показывает количество загрузок и число уникальных слов

- Добавлена поддержка .env для конфигурации

- 🐳 Добавлены переменные окружения в compose.yaml

- Возможность переопределения портов и параметров подключения к БД

- Обновлён README.md с документацией

- 🐳 Сборка и запуск в Docker-контейнерах

### Версия 0.0.2

- Добавлен Swagger-интерфейс (`/docs`)
- Проектирование и реализация моделей:
  - Пользователь, Документ, Коллекция, Статистика
- Реализованы все необходимые API-эндпоинты
- Добавлена авторизация, регистрация, смена пароля, удаление пользователя
- Документы можно добавлять в несколько коллекций
- Реализована генерация Python-клиента из OpenAPI
