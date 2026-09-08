import os
import shutil
import subprocess
import time
from datetime import datetime

from common.utils.env import get_env
from modules.ai.utils.ai_log import log_ai_call

CLAUDE_CLI_TIMEOUT_SECONDS = 3 * 60 * 60
CLAUDE_CLI_MODEL_ENV_KEY = 'CLAUDE_CLI_MODEL'

# The worker process (Django-Q) doesn't inherit the interactive shell's PATH, so `claude`
# isn't found by name there even though it resolves fine in a terminal. Fall back to the
# well-known install location used by the native installer if PATH lookup fails.
CLAUDE_CLI_FALLBACK_PATH = os.path.expanduser('~/.local/bin/claude')

# Vars that make the `claude` CLI authenticate against the pay-per-token Anthropic API
# instead of the interactive claude.ai (subscription) login used everywhere else. Stripped
# so this behaves like a normal `claude` run in a terminal rather than billing the API key.
API_KEY_ENV_VARS = (
    'ANTHROPIC_API_KEY',
    'ANTHROPIC_AUTH_TOKEN',
    'ANTHROPIC_BASE_URL',
    'CLAUDE_CODE_USE_BEDROCK',
    'CLAUDE_CODE_USE_VERTEX',
)


def _subprocess_env() -> dict:
    return {key: value for key, value in os.environ.items() if key not in API_KEY_ENV_VARS}


def _resolve_claude_binary() -> str:
    resolved = shutil.which('claude')
    if resolved:
        return resolved
    if os.path.isfile(CLAUDE_CLI_FALLBACK_PATH):
        return CLAUDE_CLI_FALLBACK_PATH
    raise FileNotFoundError(
        f"'claude' CLI not found on PATH and fallback path does not exist: {CLAUDE_CLI_FALLBACK_PATH}"
    )


def run_claude_skill(skill_command: str) -> None:
    log_ai_call(f'CLI REQUEST command={skill_command}')
    start = datetime.now()
    deadline = time.monotonic() + CLAUDE_CLI_TIMEOUT_SECONDS

    process = subprocess.Popen(
        [
            _resolve_claude_binary(),
            '-p',
            skill_command,
            '--permission-mode',
            'bypassPermissions',
            '--output-format',
            'stream-json',
            '--verbose',
            '--model',
            get_env(CLAUDE_CLI_MODEL_ENV_KEY),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd='/tmp',
        env=_subprocess_env(),
    )

    assert process.stdout is not None

    try:
        for line in process.stdout:
            log_ai_call(f'CLI STREAM {line.rstrip()}')

            if time.monotonic() > deadline:
                process.kill()
                raise subprocess.TimeoutExpired(process.args, CLAUDE_CLI_TIMEOUT_SECONDS)

        returncode = process.wait(timeout=max(0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        elapsed = (datetime.now() - start).total_seconds()
        log_ai_call(f'CLI TIMEOUT elapsed={elapsed:.1f}s command={skill_command}')
        raise

    elapsed = (datetime.now() - start).total_seconds()
    log_ai_call(f'CLI RESPONSE elapsed={elapsed:.1f}s returncode={returncode}')

    if returncode != 0:
        raise RuntimeError(f'claude CLI exited with code {returncode}')
