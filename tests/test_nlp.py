"""NLP 处理器测试"""

import pytest
from src.nlp.processor import NLPProcessor


@pytest.fixture
def processor():
    """创建 NLP 处理器实例"""
    config = {
        "enable_punctuation": True,
        "enable_correction": True,
        "enable_segmentation": True
    }
    return NLPProcessor(config)


class TestNLPProcessor:
    """NLP 处理器测试类"""

    def test_clean_whitespace(self, processor):
        """测试空白清理"""
        assert processor._clean_whitespace("  hello   world  ") == "hello world"
        assert processor._clean_whitespace("hello\nworld") == "hello world"
        assert processor._clean_whitespace("") == ""

    def test_correct_errors(self, processor):
        """测试纠错功能"""
        assert processor._correct_errors("的的") == "的"
        assert processor._correct_errors("了了") == "了"
        assert processor._correct_errors("正常的文本") == "正常的文本"

    def test_add_punctuation(self, processor):
        """测试自动标点"""
        # 已有标点的文本
        assert processor._add_punctuation("你好。") == "你好。"

        # 无标点的文本
        result = processor._add_punctuation("然后我去了学校")
        assert "，" in result or "。" in result

    def test_segment_sentences(self, processor):
        """测试断句功能"""
        text = "第一句话。第二句话！第三句话？"
        result = processor._segment_sentences(text)
        assert "第一句话。" in result
        assert "第二句话！" in result
        assert "第三句话？" in result

    def test_normalize_numbers(self, processor):
        """测试数字规范化"""
        assert "1" in processor.normalize_numbers("一")
        assert "2" in processor.normalize_numbers("二")
        assert "10" in processor.normalize_numbers("十")

    def test_process_pipeline(self, processor):
        """测试完整处理流程"""
        result = processor.process("你好世界")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_input(self, processor):
        """测试空输入"""
        assert processor.process("") == ""
        assert processor.process(None) is None
