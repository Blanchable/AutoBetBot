"""Primary entrypoint.

Windows-first default is to launch the control panel UI so operational tabs are always visible.
"""

from ui.control_panel import main as control_panel_main


def main() -> None:
    control_panel_main()


if __name__ == "__main__":
    main()
