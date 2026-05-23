"""配置加载工具"""

from pathlib import Path
from typing import Optional

import yaml


def load_config(config_path: Optional[str | Path] = None) -> dict:
    """加载配置文件

    Args:
        config_path: 配置文件路径，默认为 config/settings.yaml

    Returns:
        dict: 配置字典
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"

    config_path = Path(config_path)

    if not config_path.exists():
        return get_default_config()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            return config or get_default_config()
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return get_default_config()


def get_default_config() -> dict:
    """获取默认配置"""
    return {
        "asr": {
            "engine": "paraformer",
            "model_size": "large",
            "language": "zh",
            "sample_rate": 16000,
            "chunk_size": 0.5
        },
        "audio": {
            "sample_rate": 16000,
            "channels": 1,
            "dtype": "int16",
            "vad_threshold": 0.5,
            "noise_reduce": True
        },
        "nlp": {
            "enable_punctuation": True,
            "enable_correction": True,
            "enable_segmentation": True
        },
        "ui": {
            "theme": "dark",
            "font_size": 14,
            "show_waveform": True,
            "auto_copy": True
        },
        "hotwords": {
            "enabled": True,
            "file": "config/hotwords.txt"
        },
        "performance": {
            "max_concurrent": 2,
            "cache_size": 100,
            "timeout": 30
        }
    }


def save_config(config: dict, config_path: Optional[str | Path] = None):
    """保存配置文件

    Args:
        config: 配置字典
        config_path: 配置文件路径
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"

    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
