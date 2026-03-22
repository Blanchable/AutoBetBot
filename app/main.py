from app.config import Settings
from app.runtime import BotRuntime
from utils.logging_utils import configure_logging


def main() -> None:
    settings = Settings.from_env()
    configure_logging(settings.log_level)
    runtime = BotRuntime(settings)
    runtime.run()


if __name__ == "__main__":
    main()
