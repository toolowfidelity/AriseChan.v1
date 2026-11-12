import re
from dataclasses import dataclass
from typing import Literal


MOTION_COUNT = 26
MOTION_SEQUENCES = {
    "greeting": (23, 7),
    "happy": (21, 12),
    "shy": (10, 17),
    "curious": (5, 2),
}
MOTION_SEQUENCE_DESCRIPTIONS = {
    "greeting": "радостный жест, затем движение головы и рук",
    "happy": "улыбка и два выразительных жеста",
    "shy": "смущённый жест и застенчивое выражение",
    "curious": "удивлённый взгляд и поворот головы",
}
MOTION_DESCRIPTIONS = {
    1: "наклоны головы",
    2: "повороты и наклоны головы",
    3: "поворот корпуса и жест руками",
    4: "жест руками и изменение мимики",
    5: "удивлённый взгляд",
    6: "повороты головы и движения рук",
    7: "повороты головы и движения рук",
    8: "наклон корпуса и мягкий взгляд",
    9: "покачивание и наклоны головы",
    10: "смущённая улыбка и жест руками",
    11: "наклон головы и поза рук",
    12: "улыбка и жест руками",
    13: "поворот корпуса и движение руки",
    14: "выразительная мимика и жест руками",
    15: "повороты и наклоны головы",
    16: "грустное выражение со слезами",
    17: "смущённое выражение",
    18: "повороты головы и жест руками",
    19: "покачивание корпуса",
    20: "серьёзное выражение и движение руки",
    21: "улыбка и жест руками",
    22: "смущённая улыбка и жест руками",
    23: "радостное выражение и жест руками",
    24: "выразительная мимика и поза",
    25: "смена мимики и наклоны головы",
    26: "смена мимики и движения рук",
}

_NUMBERED_MOTION = re.compile(
    r"(?:^|[^\w])(?:/motion|motion|движени\w*|анимаци\w*)"
    r"\s*(?:(?:№|#|номер)\s*)?(\d+)(?!\d)",
    re.IGNORECASE,
)
_MOTION_LIST = re.compile(
    r"(?:список\s+движени\w*|покажи\s+движени\w*|"
    r"какие\s+движени\w*|движени\w*\s+список|"
    r"^движения$|motion\s+list)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class MotionCommand:
    action: Literal["play", "sequence", "random", "idle", "list"]
    number: int | None = None
    sequence: str | None = None


def parse_motion_command(text: str) -> MotionCommand | None:
    normalized = text.casefold().strip()
    match = _NUMBERED_MOTION.search(normalized)
    if match:
        return MotionCommand("play", int(match.group(1)))

    sequence_phrases = {
        "greeting": ("поздоровайся", "поприветствуй", "помаши"),
        "happy": ("покажи радость", "порадуйся"),
        "shy": ("смутись", "застенчивое движение"),
        "curious": ("удиви меня", "удивись"),
    }
    for sequence, phrases in sequence_phrases.items():
        if any(phrase in normalized for phrase in phrases):
            return MotionCommand("sequence", sequence=sequence)

    if _MOTION_LIST.search(normalized):
        return MotionCommand("list")

    if normalized in {"стоп", "stop", "idle", "ожидание"} or any(
        phrase in normalized
        for phrase in (
            "останови движение",
            "останови анимацию",
            "прекрати движение",
            "вернись в ожидание",
        )
    ):
        return MotionCommand("idle")

    if normalized in {"движение", "анимация", "двигайся", "пошевелись"} or any(
        phrase in normalized
        for phrase in (
            "случайное движение",
            "рандомное движение",
            "любое движение",
            "сделай движение",
            "покажи движение",
            "random motion",
        )
    ):
        return MotionCommand("random")

    return None


def format_motion_list() -> str:
    motions = ", ".join(
        f"{number:02d} — {MOTION_DESCRIPTIONS[number]} "
        f"(haru_g_m{number:02d})"
        for number in range(1, MOTION_COUNT + 1)
    )
    return (
        "У Haru есть зацикленное ожидание и 26 пронумерованных движений. "
        "Названия в файлах отсутствуют; описания ниже — по анимируемым "
        "параметрам модели:\n"
        f"{motions}\n\n"
        "Составные анимации: «поздоровайся», «покажи радость», "
        "«смутись», «удиви меня».\n"
        "Напиши «движение 7», «случайное движение» или «останови движение»."
    )
