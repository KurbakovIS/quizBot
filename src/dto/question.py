from dataclasses import dataclass
from typing import Optional
import uuid


@dataclass
class QuestionDTO:
    id: uuid.UUID
    level_id: uuid.UUID
    text: str
    hint: Optional[str]
    correct_answer: str
    image_file: Optional[str]
