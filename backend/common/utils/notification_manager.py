import subprocess


class NotificationManager:
    """Manages OS notifications using zenity."""

    @staticmethod
    def show(title: str, message: str) -> None:
        subprocess.Popen(
            ['zenity', '--info', '--title', title, '--text', message],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
