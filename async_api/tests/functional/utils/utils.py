from hashlib import sha256
from urllib.parse import urlparse, urlunparse
from typing import Union
import orjson


def build_url(base_url: str, *url_parts):
    path = [str(url_part).strip(' /') for url_part in url_parts if url_part]
    path = '/'.join(path)
    url_parts = list(urlparse(base_url))
    url_parts[2] = path
    return urlunparse(url_parts)


def hash_key(index: str, key: Union[str, dict]) -> str:
    # Формирует хеш ключа запроса
    key: bytes = orjson.dumps(key)
    hash = sha256(key).hexdigest()
    return f'{index}:{hash}'
