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
├── app  <span style="color:green"># Основная директория приложения.</span><br />
│   ├── static <span style="color:green"># Статические файлы</span><br />
│   │   └── styles.css <span style="color:green"># Таблица стилей</span><br />
│   ├── templates <span style="color:green"># Папка с HTML-шаблонами</span><br />
│   │   ├── index.html <span style="color:green"># Начальная форма для загрузки файла</span><br />
│   │   └── output.html <span style="color:green"># Результаты анализа текста.</span><br />
│   ├── database.py <span style="color:green"># Настройка подключения к базе данных.</span><br />
│   ├── init_db.py <span style="color:green"> # Инициализация базы данных</span><br />
│   ├── main.py <span style="color:green"># Основное приложение FastAPI</span><br />
│   ├── models.py<span style="color:green"> # Содержит ORM-модели</span><br />
│   ├── requirements.txt <span style="color:green"># Зависимости Python</span><br />
│   ├── services.py <span style="color:green"># Логика обработки текста</span><br />
│   └── wait-for-postgres.sh<span style="color:green"> # Скрипт ожидания запуска PostgreSQL</span><br />
├── .env <span style="color:green"># Переменные окружения</span><br />
├── .gitignore<span style="color:green"># Указание Git игнорируемых файлов</span><br />
├── compose.yaml <span style="color:green"># Docker Compose для запуска</span><br />
├── Dockerfile <span style="color:green"># Инструкция сборки образа приложения</span><br />
└── README.md <span style="color:green"># Документация проекта</span><br />

### Project run

- Run the application:  
```bash
docker-compose up --build
```
Приложение будет доступно по адресу: http://localhost:8000

### 📊 Метрики
Доступны по эндпоинту /metrics. Пример:

```json
{
  "total_uploads": 3,
  "unique_words": 178
}
```
### 🔁 Версия приложения
Версия: 0.0.1<br />
Эндпоинт: /version

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
