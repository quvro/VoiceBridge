"""腾讯云实时语音识别 WebSocket 客户端"""
import asyncio
import base64
import hashlib
import hmac
import json
import time
import uuid
from urllib.parse import urlencode

import websockets

from config import (
    TENCENT_APPID,
    TENCENT_SECRET_ID,
    TENCENT_SECRET_KEY,
    TENCENT_ASR_ENDPOINT,
)


def build_signature(params: dict) -> str:
    """构建腾讯云 ASR HMAC-SHA1 签名"""
    sorted_params = sorted(params.items(), key=lambda x: x[0])
    sign_str = f"{TENCENT_ASR_ENDPOINT.replace('wss://', '')}/{TENCENT_APPID}?"
    sign_str += "&".join(f"{k}={v}" for k, v in sorted_params)
    signature = base64.b64encode(
        hmac.new(TENCENT_SECRET_KEY.encode(), sign_str.encode(), hashlib.sha1).digest()
    ).decode()
    return signature


def build_url(engine_model_type: str = "16k_en", voice_format: int = 1) -> str:
    """构建腾讯云 ASR WebSocket 连接 URL"""
    now = int(time.time())
    voice_id = str(uuid.uuid4())
    params = {
        "engine_model_type": engine_model_type,
        "expired": now + 86400,
        "nonce": now * 1000,
        "secretid": TENCENT_SECRET_ID,
        "timestamp": now,
        "voice_format": voice_format,
        "voice_id": voice_id,
    }
    signature = build_signature(params)
    params["signature"] = signature
    # 需要 URL encode 特殊字符
    query_string = urlencode(params)
    return f"{TENCENT_ASR_ENDPOINT}/{TENCENT_APPID}?{query_string}", voice_id


class TencentASRClient:
    """腾讯云实时语音识别客户端"""

    def __init__(self, engine_model_type: str = "16k_en"):
        self.engine_model_type = engine_model_type
        self.voice_id: str = ""
        self._ws: websockets.WebSocketClientProtocol | None = None
        self._connected: bool = False

    async def connect(self) -> tuple[bool, str]:
        """连接腾讯云 ASR WebSocket"""
        url, self.voice_id = build_url(self.engine_model_type)
        try:
            self._ws = await websockets.connect(url, max_size=10**8)
            response = await self._ws.recv()
            result = json.loads(response)
            if result.get("code") == 0:
                self._connected = True
                return True, result.get("message", "success")
            return False, result.get("message", "unknown error")
        except Exception as e:
            return False, str(e)

    async def send_audio(self, pcm_data: bytes):
        """发送 PCM 音频数据"""
        if self._ws and self._connected:
            await self._ws.send(pcm_data)

    async def send_end(self):
        """发送音频结束标记"""
        if self._ws and self._connected:
            await self._ws.send(json.dumps({"type": "end"}))

    async def receive_result(self) -> dict | None:
        """接收识别结果（阻塞直到有结果或连接断开）"""
        if self._ws and self._connected:
            try:
                response = await self._ws.recv()
                return json.loads(response)
            except websockets.ConnectionClosed:
                self._connected = False
                return None
        return None

    async def close(self):
        """关闭连接"""
        self._connected = False
        if self._ws:
            await self._ws.close()
            self._ws = None

    @property
    def is_connected(self) -> bool:
        return self._connected
