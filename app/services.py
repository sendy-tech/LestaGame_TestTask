import math
import re
import heapq
from typing import Optional
from collections import Counter
from http import HTTPStatus

from fastapi import UploadFile, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import FileUpload, WordStat
from app.models.user import User


def decode_content(content: bytes) -> str:
    for encoding in ["utf-8", "windows-1251", "cp1252"]:
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")  # fallback


async def get_text(file: UploadFile) -> str:
    """Читает содержимое файла как текст."""
    try:
        content = await file.read()
        text = decode_content(content)
    except Exception:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail="Не удалось прочитать файл")
    finally:
        await file.close()

    return text


def clean_words(text: str) -> list[str]:
    """Извлекает слова на любом алфавите (русский, английский и др.)."""
    return re.findall(r'\b[^\W\d_]{2,}\b', text.lower(), flags=re.UNICODE)


def term_frequency(text: str) -> Counter[str]:
    """Вычисляет Term Frequency (TF) для текста."""
    words = clean_words(text)

    if not words:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Файл не содержит допустимого текста"
        )

    word_counts = Counter(words)
    total_words = sum(word_counts.values())

    # Возвращаем нормализованную частоту
    return Counter({word: count / total_words for word, count in word_counts.items()})

async def inverse_document_frequency(db: AsyncSession, user: User, words: list[str]) -> dict[str, float]:
    """
    Вычисляет IDF для списка слов по документам конкретного пользователя.

    :param db: AsyncSession SQLAlchemy
    :param user: текущий пользователь (должен иметь атрибут id)
    :param words: список слов для подсчёта IDF
    :return: словарь {слово: idf}
    """
    # Получаем количество документов текущего пользователя
    total_docs_res = await db.execute(
        select(func.count(FileUpload.id)).where(FileUpload.user_id == user.id)
    )
    total_docs = total_docs_res.scalar_one()

    if total_docs == 0:
        return {word: 0.0 for word in words}

    # Считаем, в скольких документах пользователя встречается каждое слово
    result = await db.execute(
        select(
            WordStat.word,
            func.count(func.distinct(WordStat.file_id)).label("doc_count")
        ).where(
            WordStat.word.in_(words),
            WordStat.user_id == user.id
        ).group_by(WordStat.word)
    )

    word_doc_counts = {row.word: row.doc_count for row in result}

    # IDF по формуле log10(N / (1 + n_i)), где N — общее число документов пользователя
    idf_scores = {}
    for word in words:
        doc_count = word_doc_counts.get(word, 0)
        idf_scores[word] = math.log10(total_docs / (1 + doc_count))
    return idf_scores

class HuffmanNode:
    def __init__(self, char: Optional[str], freq: int):
        self.char = char
        self.freq = freq
        self.left: Optional[HuffmanNode] = None
        self.right: Optional[HuffmanNode] = None

    def __lt__(self, other):
        return self.freq < other.freq


def build_huffman_tree(text: str) -> HuffmanNode:
    frequency = {}
    for char in text:
        frequency[char] = frequency.get(char, 0) + 1

    heap = [HuffmanNode(char, freq) for char, freq in frequency.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        node1 = heapq.heappop(heap)
        node2 = heapq.heappop(heap)

        merged = HuffmanNode(None, node1.freq + node2.freq)
        merged.left = node1
        merged.right = node2
        heapq.heappush(heap, merged)

    return heap[0]  # корень дерева


def generate_codes(node: HuffmanNode, prefix: str = "", code_map: Optional[dict] = None) -> dict:
    if code_map is None:
        code_map = {}

    if node.char is not None:
        code_map[node.char] = prefix
    else:
        generate_codes(node.left, prefix + "0", code_map)
        generate_codes(node.right, prefix + "1", code_map)

    return code_map


def huffman_encode(text: str) -> tuple[str, dict]:
    root = build_huffman_tree(text)
    codes = generate_codes(root)
    encoded = ''.join(codes[char] for char in text)
    return encoded, codes