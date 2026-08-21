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
    def show(title: str, message: str) -> None:
        env = os.environ.copy()
        env.setdefault('DISPLAY', _DEFAULT_DISPLAY)
        env.setdefault('DBUS_SESSION_BUS_ADDRESS', _DEFAULT_DBUS_ADDRESS)

        if 'XAUTHORITY' not in env:
            xauthority = _discover_xauthority()
            if xauthority:
                env['XAUTHORITY'] = xauthority
            else:
                logger.warning('Could not discover XAUTHORITY; notification may fail to display: %s', title)

        try:
            process = subprocess.Popen(
                ['zenity', '--info', '--title', title, '--text', message],
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
