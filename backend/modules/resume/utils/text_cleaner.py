import html
import re

_SCRIPT_OR_STYLE_RE = re.compile(r'<(script|style)\b[^>]*>.*?</\1>', re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r'<[^>]+>')
_INLINE_CSS_RE = re.compile(r'\{[^{}]*\}')
_TRAILING_SPACES_RE = re.compile(r'[ \t]+')
_BLANK_LINES_RE = re.compile(r'\n\s*\n+')


def clean_job_description(text: str) -> str:
    if not text:
        return text

    cleaned = html.unescape(text)
    cleaned = _SCRIPT_OR_STYLE_RE.sub(' ', cleaned)
    cleaned = _TAG_RE.sub(' ', cleaned)
    cleaned = _INLINE_CSS_RE.sub(' ', cleaned)

    lines = [_TRAILING_SPACES_RE.sub(' ', line).strip() for line in cleaned.splitlines()]
    cleaned = '\n'.join(line for line in lines if line)
    cleaned = _BLANK_LINES_RE.sub('\n\n', cleaned)

    return cleaned.strip()
