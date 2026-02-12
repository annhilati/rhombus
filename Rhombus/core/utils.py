from typing import TypeAlias
import hashlib, uuid, json

JSONDict: TypeAlias = dict[str, dict | list | tuple | str | int | float | bool | None]

def uuid_hash(data: JSONDict) -> str:
    """Creates a UUID string (without `-`) based of a JSON dictionary."""
    encoded_str = json.dumps(
        data, 
        sort_keys=True, 
        ensure_ascii=True, 
        separators=(',', ':')
    ).encode('utf-8')
    hash_digest = hashlib.sha256(encoded_str).digest()
    return str(uuid.UUID(bytes=hash_digest[:16])).replace("-", "")