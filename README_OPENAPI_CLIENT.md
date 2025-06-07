# 🐍 Генерация Python-клиента по OpenAPI для FastAPI-приложения

Данный проект использует [FastAPI](https://fastapi.tiangolo.com/) и автоматически публикует спецификацию API по адресу `/openapi.json`. Вы можете использовать эту спецификацию для генерации клиента на любом языке, включая Python, с помощью [OpenAPI Generator](https://openapi-generator.tech/).

## 📦 Установка OpenAPI Generator

Установить CLI можно одним из следующих способов:

### 🔹 Вариант 1: через Homebrew (macOS / Linux)

```bash
brew install openapi-generator
```

### 🔹 Вариант 2: скачать `.jar` и создать alias

```bash
wget https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/7.6.0/openapi-generator-cli-7.6.0.jar -O openapi-generator-cli.jar

alias openapi-generator='java -jar openapi-generator-cli.jar'
```

## ⚙️ Генерация клиента на Python

### Шаг 1: Запустите FastAPI приложение

Убедитесь, что ваше приложение работает и доступно локально по адресу:

```
http://localhost:8000
```

### Шаг 2: Скачайте OpenAPI спецификацию

```bash
curl http://localhost:8000/openapi.json -o openapi.json
```

### Шаг 3: Сгенерируйте Python-клиент

```bash
openapi-generator generate \
  -i openapi.json \
  -g python \
  -o ./generated_client
```

- `-i openapi.json` – путь к спецификации
- `-g python` – язык клиента
- `-o ./generated_client` – директория вывода

## 📁 Структура `generated_client`

После генерации вы получите каталог со следующим содержимым:

```
generated_client/
├── docs/
├── generated_client/
│   ├── api/
│   ├── models/
│   └── configuration.py
├── setup.py
└── README.md
```

## ✅ Использование клиента в проекте

```python
from generated_client import ApiClient, Configuration
from generated_client.api.default_api import DefaultApi

config = Configuration(host="http://localhost:8000")
with ApiClient(config) as client:
    api = DefaultApi(client)
    response = api.read_root()
    print(response)
```

## 📌 Примечания

- Убедитесь, что API доступен по тому же адресу, что указан в `host`.
- Вы можете настроить клиента под авторизацию, cookie и заголовки.

---

> **Поддерживаемые языки**: Python, TypeScript, Go, Java, Kotlin, Swift и другие. См. полный список генераторов:  
> https://openapi-generator.tech/docs/generators