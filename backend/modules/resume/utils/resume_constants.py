import os

from common.utils.env import get_env

CLAUDE_CLI_BINARY = os.path.expanduser('~/.local/bin/claude')
CLAUDE_CLI_TIMEOUT_SECONDS = 600 # 10 minutes
CLAUDE_LOG_PATH = get_env('CLAUDE_LOG_PATH')
