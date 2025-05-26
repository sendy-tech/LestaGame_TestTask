FROM python:latest

# Устанавливаем рабочую директорию внутри контейнера
#WORKDIR /app


# Копируем файлы зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем содержимое текущей директории в контейнер
COPY . .

EXPOSE 8080
# Настраиваем запуск нашего приложения
CMD ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"]


#FROM python:latest as build
#
## Копируем файлы зависимостей
#COPY requirements.txt .
#
## Устанавливаем зависимости
#RUN pip install --no-cache-dir -r requirements.txt
#
## Копируем содержимое текущей директории в контейнер
#COPY . .
#
#WORKDIR /src
#
#FROM alpine:3.21 as production
#COPY --from=build /bin /bin/main
#EXPOSE 8080
#
## Настраиваем запуск нашего приложения
#CMD ["uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8080"]