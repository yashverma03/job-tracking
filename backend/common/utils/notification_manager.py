import logging
import os
import subprocess

logger = logging.getLogger(__name__)

_DEFAULT_DISPLAY = ':1'
_DEFAULT_DBUS_ADDRESS = f'unix:path=/run/user/{os.getuid()}/bus'


class NotificationManager:
    """Manages OS notifications using zenity."""

    @staticmethod
    def show(title: str, message: str) -> None:
        env = os.environ.copy()
        env.setdefault('DISPLAY', _DEFAULT_DISPLAY)
        env.setdefault('DBUS_SESSION_BUS_ADDRESS', _DEFAULT_DBUS_ADDRESS)

        try:
            subprocess.Popen(
                ['zenity', '--info', '--title', title, '--text', message],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            logger.exception('Failed to show notification: %s', title)
