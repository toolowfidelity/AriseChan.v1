from arisechan.services.motion_commands import (
    MOTION_DESCRIPTIONS,
    MOTION_COUNT,
    MOTION_SEQUENCE_DESCRIPTIONS,
)


def reply_to(message):
    normalized = message.casefold()
    quoted = message.strip()
    if len(quoted) > 160:
        quoted = quoted[:157].rstrip() + "..."

    if any(word in normalized for word in ("привет", "здравствуй", "хай", "hello")):
        return (
            "Привет! Рада, что ты заглянул. Сейчас я работаю локально, поэтому "
            "могу поддержать простой разговор и помочь с нашим проектом, но "
            "пока не умею отвечать так же подробно, как подключённый ИИ. "
            "Расскажи, что хочешь сделать дальше?"
        )

    if any(word in normalized for word in ("arisechan", "компаньон", "оверлей", "проект")):
        return (
            "Поняла, ты про AriseChan — нашего настольного компаньона. Мы уже "
            "разделили персонажа, облачка и поле ввода на отдельные блоки. "
            "Можем дальше улучшать внешний вид, поведение блоков или общение. "
            "Что сейчас важнее?"
        )

    if any(word in normalized for word in ("ошибка", "не работает", "сломал", "баг")):
        return (
            "Давай спокойно разберёмся. Напиши, что ты ожидал увидеть, что "
            "произошло вместо этого и какие действия привели к проблеме. "
            "Если есть текст ошибки, пришли его — так будет проще найти причину. "
            "Сейчас я отвечаю без облачного ИИ, поэтому это базовая подсказка."
        )

    if any(word in normalized for word in ("спасибо", "благодар")):
        return (
            "Пожалуйста, мне приятно помогать тебе с AriseChan. Пока я отвечаю "
            "в простом локальном режиме, но даже так можем постепенно улучшать "
            "проект и разбирать следующие шаги."
        )

    if "?" in message:
        return (
            f"Я услышала твой вопрос: «{quoted}». Сейчас у меня нет подключения "
            "к OpenAI, поэтому я не могу дать полноценный анализ или проверить "
            "актуальные данные. Могу помочь разложить вопрос на шаги или "
            "продолжить работу над самим приложением."
        )

    return (
        f"Поняла тебя: «{quoted}». Сейчас я без подключения к облачному ИИ, "
        "поэтому отвечаю простыми заготовленными репликами. Могу продолжить "
        "обсуждать AriseChan, помочь сформулировать следующую задачу или "
        "подсказать, какие детали стоит уточнить."
    )


def reply_to_motion(motion_index, randomly_selected=False):
    if not 1 <= motion_index <= MOTION_COUNT:
        raise ValueError(f"Motion number must be between 1 and {MOTION_COUNT}.")

    description = MOTION_DESCRIPTIONS[motion_index]
    if randomly_selected:
        return (
            f"Хи-хи, случайно выбрала жест №{motion_index:02d}: "
            f"{description}. Смотри!"
        )
    return (
        f"Конечно! Показываю жест №{motion_index:02d}: "
        f"{description}."
    )


def reply_to_sequence(sequence_name):
    try:
        description = MOTION_SEQUENCE_DESCRIPTIONS[sequence_name]
    except KeyError as error:
        raise ValueError(f"Unknown animation sequence: {sequence_name}") from error
    return f"Сыграю составную анимацию: {description}."
