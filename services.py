import math
import random
import re
from collections import Counter
from http import HTTPStatus

from fastapi import UploadFile, HTTPException


async def get_text(file: UploadFile) -> str:
    try:
        content = await file.read()
        text = content.decode()
    except UnicodeDecodeError:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST)
    finally:
        await file.close()

    return text


async def term_frequency(text: str) -> Counter:
    split_text = re.findall(r'\b[^\d\W]+\b', text)
    if len(split_text) < 1:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST)
    word_tf = Counter(split_text)
    total = word_tf.total()

    for word in word_tf:
        word_tf[word] /= total

    return word_tf


async def inverse_document_frequency(words: Counter) -> list[tuple[str, int]]:
    dict_idf = {}
    total_docs = 100_000_000
    for word in words:
        docs_with_word = random.randint(0, 3000) + 1
        idf = math.log10(total_docs/docs_with_word)
        dict_idf[word] = idf

    sorted_idf = sorted(
        dict_idf.items(), key=lambda item: item[1], reverse=True
    )
    return sorted_idf[:50]
