import subprocess
from datetime import datetime

from modules.ai.utils.ai_log import log_ai_call

CLAUDE_CLI_TIMEOUT_SECONDS = 3 * 60 * 60


def run_claude_skill(skill_command: str) -> None:
    log_ai_call(f'CLI REQUEST command={skill_command}')
    start = datetime.now()

    result = subprocess.run(
        ['claude', '-p', skill_command, '--permission-mode', 'bypassPermissions', '--output-format', 'json'],
        capture_output=True,
        text=True,
        timeout=CLAUDE_CLI_TIMEOUT_SECONDS,
        cwd='/tmp',
    )

    elapsed = (datetime.now() - start).total_seconds()
    log_ai_call(f'CLI RESPONSE elapsed={elapsed:.1f}s {result}')

    if result.returncode != 0:
        raise RuntimeError(f'claude CLI exited with code {result.returncode}: {result.stderr.strip()}')
