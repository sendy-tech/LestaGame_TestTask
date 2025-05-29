#!/bin/sh

set -e

# Имя хоста БД и порт
host="$1"
port="${POSTGRES_PORT:-5432}"

# Удаляем первый аргумент (host), чтобы осталась только команда
shift

until pg_isready -h "$host" -p "$port"; do
  echo "Postgres is unavailable - sleeping"
  sleep 1
done

# Запускаем оставшуюся команду
exec "$@"
