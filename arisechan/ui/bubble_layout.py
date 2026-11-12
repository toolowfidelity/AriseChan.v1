from arisechan.ui.blocks import CHARACTER_HEIGHT, CHARACTER_WIDTH


BUBBLE_WIDTH = 292
BUBBLE_TEXT_WIDTH = BUBBLE_WIDTH - 75
BUBBLE_GAP = 12
CHARACTER_MOUTH_X_RATIO = 0.4
CHARACTER_MOUTH_Y_RATIO = 0.17
BUBBLE_TAIL_EXTENSION = 72


def wrap_text(text, font, width):
    lines = []
    for paragraph in text.splitlines() or [""]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = ""
        for word in words:
            parts = split_long_word(word, font, width)
            for part_index, part in enumerate(parts):
                candidate = f"{current} {part}" if current else part
                if (
                    current
                    and part_index == 0
                    and font.measure(candidate) <= width
                ):
                    current = candidate
                else:
                    if current:
                        lines.append(current)
                    current = part
        lines.append(current)
    return lines


def split_long_word(word, font, width):
    if font.measure(word) <= width:
        return [word]

    parts = []
    current = ""
    for character in word:
        candidate = current + character
        if current and font.measure(candidate) > width:
            parts.append(current)
            current = character
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts


def bubble_height(lines, font):
    line_height = font.metrics("linespace")
    return max(80, len(lines) * line_height + 48)


def find_bubble_position(
    width,
    height,
    character_block,
    screen_width,
    screen_height,
    taskbar_top=None,
):
    if character_block and character_block.exists():
        char_x, char_y = character_block.position()
        mouth_x = char_x + round(CHARACTER_WIDTH * CHARACTER_MOUTH_X_RATIO)
        preferred_x = mouth_x - width + 1
        mouth_y = char_y + round(CHARACTER_HEIGHT * CHARACTER_MOUTH_Y_RATIO)
        preferred_y = mouth_y - height // 2
    else:
        preferred_x = (screen_width - width) // 2
        preferred_y = (screen_height - height) // 2

    x = max(8, min(preferred_x, screen_width - width - 8))
    work_area_bottom = (
        screen_height
        if taskbar_top is None
        else min(screen_height, taskbar_top)
    )
    max_y = max(8, work_area_bottom - height - 8)
    y = max(8, min(preferred_y, max_y))
    return x, y
