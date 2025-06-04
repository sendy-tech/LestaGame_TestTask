import math
import random
import re
from collections import Counter
from http import HTTPStatus
from typing import Any

from fastapi import UploadFile, HTTPException

# Читает содержимое файла и возвращает текст как строку.
# Если файл не удаётся прочитать, вызывает HTTP 400.
async def get_text(file: UploadFile) -> str:
    try:
        content = await file.read()
        # Декодируем содержимое, игнорируя ошибки кодировки
        text = content.decode("utf-8", errors="ignore")
    except Exception:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Не удалось прочитать файл"
        )
    finally:
        await file.close()

    return text

# Расчёт Term Frequency (TF)
async def term_frequency(text: str) -> Counter:
    # Извлекаем только слова без цифр и знаков препинания
    words = re.findall(r'\b[^\d\W]+\b', text)

    if not words:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Файл не содержит допустимого текста"
        )

    word_counts = Counter(words)
    total_words = word_counts.total()

    # Нормализуем частоты
    for word in word_counts:
        word_counts[word] /= total_words

    return word_counts

# Вычисляет Inverse Document Frequency (IDF) (обратную частоту документа) для каждого слова.
# Использует случайные данные для количества документов, содержащих слово.
# Возвращает список из 50 слов с наибольшим IDF.
async def inverse_document_frequency(words: Counter) -> list[tuple[Any, float]]:
    idf_scores = {}
    total_docs = 100_000_000  # Допустимая база документов

    for word in words:
        docs_with_word = random.randint(1, 3000)
        idf = math.log10(total_docs / docs_with_word)
        idf_scores[word] = idf

    # Сортируем по убыванию IDF и берём топ-50
    top_words = sorted(idf_scores.items(), key=lambda item: item[1], reverse=True)
    return top_words[:50]