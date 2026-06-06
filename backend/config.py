"""VoiceBridge 后端配置"""
import os
from dotenv import load_dotenv

load_dotenv()

# 腾讯云 ASR 配置
TENCENT_APPID = os.getenv("TENCENT_APPID", "")
TENCENT_SECRET_ID = os.getenv("TENCENT_SECRET_ID", "")
TENCENT_SECRET_KEY = os.getenv("TENCENT_SECRET_KEY", "")
TENCENT_ASR_ENDPOINT = "wss://asr.cloud.tencent.com/asr/v2"

# DeepSeek 翻译配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-v4-flash"

# 服务配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
