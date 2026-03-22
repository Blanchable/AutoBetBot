"""Primary entrypoint.

Default: launches control panel (Windows-first UX).
Set APP_HEADLESS=1 to run bot runtime directly without UI.
"""

import os

from app.config import Settings
from app.runtime import BotRuntime
from ui.control_panel import main as control_panel_main
from utils.logging_utils import configure_logging


def main() -> None:
    if os.getenv("APP_HEADLESS", "0") == "1":
        settings = Settings.from_env()
        configure_logging(settings.log_level)
        runtime = BotRuntime(settings)
        runtime.run()
        return

    control_panel_main()


if __name__ == "__main__":
    main()
