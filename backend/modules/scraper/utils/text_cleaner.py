import html
import re

# Matches any HTML tag, e.g. <b>, </div>, <br/>
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')
# Matches leading/trailing runs of whitespace or stray punctuation (_ , ' " -)
TRIM_CHARS_PATTERN = re.compile(r"^[\s_,'\"\-]+|[\s_,'\"\-]+$")
# Matches 2+ consecutive spaces/tabs (newlines are left intact for multi-line text)
MULTIPLE_SPACES_PATTERN = re.compile(r'[ \t]{2,}')


def clean_text(text: str | None) -> str | None:
    if text is None:
        return None

    cleaned = HTML_TAG_PATTERN.sub('', text)
    cleaned = html.unescape(cleaned)
    cleaned = MULTIPLE_SPACES_PATTERN.sub(' ', cleaned.strip())
    cleaned = TRIM_CHARS_PATTERN.sub('', cleaned).strip()
    return cleaned or None
