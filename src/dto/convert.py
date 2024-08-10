from src.database import Question
from src.dto.question import QuestionDTO


def question_to_dto(question: Question) -> QuestionDTO:
    return QuestionDTO(
        id=question.id,
        level_id=question.level_id,
        text=question.text,
        hint=question.hint,
        correct_answer=question.correct_answer,
        image_file=question.image_file
    )