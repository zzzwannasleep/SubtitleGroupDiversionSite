from __future__ import annotations

from sqlalchemy import BigInteger, Integer
from sqlalchemy.sql.type_api import TypeEngine


def bigint_type() -> TypeEngine[int]:
    return BigInteger().with_variant(Integer, "sqlite")
