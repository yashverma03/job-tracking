import glob
import logging
import os
import subprocess

logger = logging.getLogger(__name__)

_DEFAULT_DISPLAY = ':1'
_DEFAULT_DBUS_ADDRESS = f'unix:path=/run/user/{os.getuid()}/bus'


def _discover_xauthority() -> str | None:
    run_dir = f'/run/user/{os.getuid()}'
    candidates = [os.path.join(run_dir, '.Xauthority')]
    candidates.extend(glob.glob(os.path.join(run_dir, '.mutter-Xwaylandauth.*')))
    return next((path for path in candidates if os.path.isfile(path)), None)


class NotificationManager:
    """Manages OS notifications using zenity."""

    @staticmethod
    def show(title: str, message: str, width: int | None = None, height: int | None = None) -> None:
        command = ['zenity', '--info', '--title', title, '--text', message]
        NotificationManager._run(command, title, width=width, height=height)

    @staticmethod
    def show_table(
        title: str,
        columns: list[str],
        rows: list[list[str]],
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        """Displays a read-only table dialog (zenity's `--list`) - one row per entry in
        `rows`, each a list of cell values matching `columns` in order."""
        command = ['zenity', '--list', '--title', title]
        for column in columns:
            command += ['--column', column]
        for row in rows:
            command += [str(cell) for cell in row]

        NotificationManager._run(command, title, width=width, height=height)

    @staticmethod
    def _run(command: list[str], title: str, width: int | None = None, height: int | None = None) -> None:
        env = os.environ.copy()
        env.setdefault('DISPLAY', _DEFAULT_DISPLAY)
        env.setdefault('DBUS_SESSION_BUS_ADDRESS', _DEFAULT_DBUS_ADDRESS)

        if 'XAUTHORITY' not in env:
            xauthority = _discover_xauthority()
            if xauthority:
                env['XAUTHORITY'] = xauthority
            else:
                logger.warning('Could not discover XAUTHORITY; notification may fail to display: %s', title)

        if width is not None:
            command += ['--width', str(width)]
        if height is not None:
            command += ['--height', str(height)]

        try:
            process = subprocess.Popen(
                command,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except OSError:
            logger.exception('Failed to show notification: %s', title)
            return

        # zenity fails fast (e.g. no display/auth) but blocks on the dialog while
        # waiting for the user to dismiss it, so only poll briefly for an early exit.
        try:
            _, stderr = process.communicate(timeout=0.5)
        except subprocess.TimeoutExpired:
            return

        if process.returncode not in (0, 1):
            logger.error(
                'zenity exited with code %s for notification %r: %s',
                process.returncode,
                title,
                stderr.decode(errors='replace').strip(),
            )
