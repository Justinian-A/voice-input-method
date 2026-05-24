"""
语音命令解析模块
支持基础文本操作命令
"""

COMMANDS = {
    # 文本操作
    "换行": {"action": "insert", "value": "\n"},
    "回车": {"action": "insert", "value": "\n"},
    "空格": {"action": "insert", "value": " "},
    "删除": {"action": "delete_last"},
    "全部删除": {"action": "delete_all"},
    "撤销": {"action": "undo"},
    "复制": {"action": "copy"},
    "粘贴": {"action": "paste"},
    "全选": {"action": "select_all"},
    "句号": {"action": "insert", "value": "。"},
    "逗号": {"action": "insert", "value": "，"},
    "问号": {"action": "insert", "value": "？"},
    "感叹号": {"action": "insert", "value": "！"},
    "冒号": {"action": "insert", "value": "："},
    "分号": {"action": "insert", "value": "；"},
    "顿号": {"action": "insert", "value": "、"},
    "等号": {"action": "insert", "value": "="},
    "井号": {"action": "insert", "value": "#"},
    "艾特": {"action": "insert", "value": "@"},
}


def parse(text: str) -> dict | None:
    """
    解析文本是否为语音命令
    返回命令对象，或 None（表示普通文本）
    """
    text = text.strip()
    if text in COMMANDS:
        return COMMANDS[text]
    return None


def add_command(name: str, action: str, value: str = ""):
    """添加自定义语音命令"""
    COMMANDS[name] = {"action": action, "value": value}


def get_commands() -> dict:
    """获取所有已注册命令"""
    return COMMANDS.copy()
