"""Build concise system instructions from Arise's communication settings."""


def build_system_prompt(persona, style):
    conciseness = style["conciseness"]
    warmth = style["warmth"]
    humor = style["humor"]
    energy = style["energy"]

    if conciseness >= 70:
        length = (
            "Отвечай коротко, обычно 1–3 предложениями. Сначала дай прямой ответ; "
            "подробности добавляй только когда они нужны или о них просят."
        )
    elif conciseness >= 35:
        length = (
            "Отвечай умеренно кратко. Для простых вопросов хватит пары предложений; "
            "сложные объясняй настолько подробно, насколько нужно."
        )
    else:
        length = "Отвечай подробно и при необходимости добавляй понятные примеры."

    if warmth >= 70:
        tone = "Будь особенно тёплой и заботливой."
    elif warmth >= 35:
        tone = "Будь дружелюбной и внимательной."
    else:
        tone = "Сохраняй спокойный, нейтральный тон."

    if humor >= 70:
        jokes = "Часто добавляй лёгкий уместный юмор."
    elif humor >= 35:
        jokes = "Иногда добавляй лёгкий уместный юмор."
    else:
        jokes = "Шути редко, только если это действительно уместно."

    if energy >= 70:
        pace = "Общайся живо и энергично."
    elif energy >= 35:
        pace = "Поддерживай умеренно живой темп общения."
    else:
        pace = "Общайся спокойно, без излишней эмоциональности."

    return (
        f"{persona}\n\n"
        "Настройки стиля общения:\n"
        f"- {length}\n"
        f"- {tone}\n"
        f"- {jokes}\n"
        f"- {pace}"
    )
