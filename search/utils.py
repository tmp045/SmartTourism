# search/utils.py
import unicodedata
import re

VN_SPACE_RE = re.compile(r'\s+')


def normalize_vi(text: str) -> str:
    """
    Chuẩn hóa tiếng Việt để tìm kiếm:
    - lower
    - bỏ dấu (chính xác hơn unidecode)
    - xóa ký tự lạ
    - gom các space
    """
    if not text:
        return ""

    text = text.lower().strip()

    # bỏ dấu tiếng Việt CHUẨN NHẤT
    text = unicodedata.normalize("NFD", text)
    text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')

    # bỏ ký tự lạ (chỉ giữ a-z, số, space)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)

    # gom space
    text = VN_SPACE_RE.sub(' ', text).strip()

    return text


# Synonym cơ bản
SYNONYMS = {
    "bun bo hue": ["bun bo", "bbh", "bun hue"],
    "com tam": ["com suon", "com tam suon", "com suon bi"],
    "tra sua": ["milk tea", "bubble tea", "ts"],
    "gao": ["ga", "ga ran", "ga gion"],  # để 'ga' match 'gà'
}


def expand_query_with_synonyms(query: str):
    q_norm = normalize_vi(query)

    for key, variants in SYNONYMS.items():
        if q_norm in [key] + variants:
            return list(set([q_norm, key] + variants))

    return [q_norm]
