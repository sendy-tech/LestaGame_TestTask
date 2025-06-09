
# 🐍 Генерация Python-клиента по OpenAPI для FastAPI-приложения

Данный проект использует [FastAPI](https://fastapi.tiangolo.com/), который автоматически публикует спецификацию API по адресу `/openapi.json`. Вы можете использовать эту спецификацию для генерации клиента на любом языке, включая Python, с помощью [OpenAPI Generator](https://openapi-generator.tech/).

---

## 📦 Установка OpenAPI Generator

### 🔹 Вариант 1: через Homebrew (macOS / Linux)

```bash
brew install openapi-generator
```

### 🔹 Вариант 2: через pip (Python Windows)

```powershell
pip install openapi-python-client
```

## ⚙️ Генерация клиента на Python

### Шаг 1: Запустите FastAPI-приложение

Убедитесь, что ваше приложение работает и доступно локально по адресу:

```
http://localhost:8000
```

### Шаг 2: Скачайте OpenAPI-спецификацию и сгенерируйте Python-клиент

```bash
openapi-python-client generate --url http://localhost:8000/openapi.json
```

---

## 📁 Структура `generated_client`

После генерации вы получите каталог с примерной структурой:

```
document-processing-api-client/
├── document-processing-api-client/
│   ├── api/
│   ├── models/
│   ├── __inin__.py
│   ├── client.py
│   ├── errors.py
│   ├── py.typed
│   ├── types.py
│   └── configuration.py
├── pyproject.toml
└── README.md
```

## 🌐 Поддерживаемые языки

OpenAPI Generator поддерживает множество языков:  
**Python, TypeScript, Go, Java, Kotlin, Swift, PHP** и другие.

Полный список генераторов:  
👉 https://openapi-generator.tech/docs/generators
