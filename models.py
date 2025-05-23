from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class FAQ:
    similarity: int
    question: str
    date: str
    customer: str
    status: str
    stg: str
    image: Optional[str | List[str]]
    answer: str
    answer_image: Optional[str | List[str]]
    engineer: str
    closedate: str


@dataclass
class EQ:
    id: str
    eqStatus: str
    closedate: str
    customer: str
    customerPN: str
    factoryPN: str
    selected: bool
    engineer: str
    stgpn: str
    basematerial: str
    soldermask: str
    plugging: str
    filepath: str


@dataclass
class TranslationResult:
    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str