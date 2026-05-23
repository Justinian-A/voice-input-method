"""语音输入法主入口"""

import sys
from pathlib import Path

from src.core.engine import VoiceInputEngine
from src.ui.console import ConsoleUI
from src.utils.config import load_config


def main():
    """启动语音输入法"""
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    config = load_config(config_path)

    engine = VoiceInputEngine(config)
    ui = ConsoleUI(engine)

    try:
        ui.start()
    except KeyboardInterrupt:
        print("\n已退出语音输入法")
        sys.exit(0)


if __name__ == "__main__":
    main()
