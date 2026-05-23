"""自然语言处理器 - 语音识别后处理"""

import re
from typing import Optional


class NLPProcessor:
    """自然语言处理器，负责语音识别结果的后处理

    功能：
    - 自动标点
    - 智能断句
    - 文本纠错
    - 数字规范化
    """

    # 中文标点符号映射
    PUNCTUATION_MAP = {
        "，": ",",
        "。": ".",
        "！": "!",
        "？": "?",
        "；": ";",
        "：": ":",
        """: '"',
        """: '"',
        "'": "'",
        "'": "'",
        "（": "(",
        "）": ")",
    }

    # 常见语音识别错误纠正
    CORRECTION_RULES = {
        "的的": "的",
        "了了": "了",
        "是是": "是",
        "在在": "在",
        "有有": "有",
    }

    def __init__(self, config: dict):
        self.config = config
        self.enable_punctuation = config.get("enable_punctuation", True)
        self.enable_correction = config.get("enable_correction", True)
        self.enable_segmentation = config.get("enable_segmentation", True)

    def process(self, text: str) -> str:
        """处理识别文本"""
        if not text:
            return text

        # 1. 清理空白
        text = self._clean_whitespace(text)

        # 2. 智能纠错
        if self.enable_correction:
            text = self._correct_errors(text)

        # 3. 自动标点
        if self.enable_punctuation:
            text = self._add_punctuation(text)

        # 4. 智能断句
        if self.enable_segmentation:
            text = self._segment_sentences(text)

        return text

    def _clean_whitespace(self, text: str) -> str:
        """清理多余空白"""
        # 合并多个空格
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _correct_errors(self, text: str) -> str:
        """纠正常见识别错误"""
        for wrong, correct in self.CORRECTION_RULES.items():
            text = text.replace(wrong, correct)
        return text

    def _add_punctuation(self, text: str) -> str:
        """添加标点符号

        简单实现：基于规则添加标点
        实际应用中应使用专门的标点模型
        """
        # 如果已有标点，直接返回
        if any(p in text for p in "。！？，；："):
            return text

        # 简单规则：在常见连接词后添加逗号
        connectives = ["然后", "接着", "但是", "不过", "而且", "所以", "因此"]
        for conn in connectives:
            text = text.replace(conn, f"，{conn}")

        # 末尾添加句号
        if text and text[-1] not in "。！？":
            text += "。"

        return text

    def _segment_sentences(self, text: str) -> str:
        """智能断句"""
        # 按标点分割
        sentences = re.split(r"([。！？；])", text)

        # 重组句子，保持标点
        result = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            punct = sentences[i + 1] if i + 1 < len(sentences) else ""
            if sentence.strip():
                result.append(sentence.strip() + punct)

        return "".join(result)

    def normalize_numbers(self, text: str) -> str:
        """规范化数字表达"""
        # 将中文数字转换为阿拉伯数字
        chinese_nums = {
            "零": "0", "一": "1", "二": "2", "三": "3", "四": "4",
            "五": "5", "六": "6", "七": "7", "八": "8", "九": "9",
            "十": "10", "百": "100", "千": "1000", "万": "10000"
        }

        for cn, ar in chinese_nums.items():
            text = text.replace(cn, ar)

        return text
