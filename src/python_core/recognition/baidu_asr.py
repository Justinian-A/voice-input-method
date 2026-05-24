"""
百度语音识别 API 封装
文档: https://ai.baidu.com/tech/speech
"""

import json
import requests
import base64


class BaiduASR:
    """百度语音识别客户端"""

    API_URL = "https://vop.baidu.com/pro_api"
    TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"

    def __init__(self, api_key: str = "", secret_key: str = ""):
        self.api_key = api_key
        self.secret_key = secret_key
        self._token = ""
        self._token_expire = 0

    def _get_token(self) -> str:
        """获取 Access Token，复用直到过期"""
        import time
        now = time.time()
        if self._token and now < self._token_expire - 300:
            return self._token

        resp = requests.post(
            self.TOKEN_URL,
            params={
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.secret_key,
            },
            timeout=10,
        )
        data = resp.json()
        if "access_token" not in data:
            raise RuntimeError(f"百度Token获取失败: {data}")

        self._token = data["access_token"]
        self._token_expire = now + data.get("expires_in", 86400)
        return self._token

    def recognize(self, audio_data: bytes, language: str = "zh") -> dict:
        """
        识别短语音（≤60秒）
        dev_pid: 1537=普通话, 1737=英语, 1637=粤语, 1837=四川话
        """
        lang_map = {
            "zh": 1537, "zh-CN": 1537,
            "en": 1737, "en-US": 1737,
            "yue": 1637, "sichuan": 1837,
        }
        dev_pid = lang_map.get(language, 1537)

        token = self._get_token()
        params = {
            "dev_pid": dev_pid,
            "format": "pcm",
            "rate": 16000,
            "channel": 1,
            "token": token,
            "cuid": "yusheng_input",
            "speech": base64.b64encode(audio_data).decode(),
            "len": len(audio_data),
        }

        resp = requests.post(self.API_URL, json=params, timeout=15)
        result = resp.json()

        if result.get("err_no") == 0:
            return {
                "text": result.get("result", [""])[0],
                "confidence": 1.0,
                "is_final": True,
                "error": None,
            }
        return {
            "text": "",
            "confidence": 0.0,
            "is_final": True,
            "error": f"err_no={result.get('err_no')}: {result.get('err_msg', 'unknown')}",
        }

    def check_available(self) -> bool:
        """检测在线服务是否可用"""
        try:
            self._get_token()
            return True
        except Exception:
            return False
