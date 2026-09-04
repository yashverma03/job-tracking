from datetime import datetime

from modules.ai.constants.ai_constants import CLAUDE_LOG_PATH


def log_ai_call(message: str) -> None:
    timestamp = datetime.now().isoformat(sep=' ', timespec='seconds')
    with open(CLAUDE_LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(f'[{timestamp}] {message}\n')
