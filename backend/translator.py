"""DeepSeek V4 Flash 翻译模块"""
import json
from openai import OpenAI

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from context_manager import ContextManager

_client: OpenAI | None = None


def get_client() -> OpenAI | None:
    """延迟初始化 DeepSeek 客户端"""
    global _client
    if _client is None and DEEPSEEK_API_KEY:
        _client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )
    return _client

TRANSLATION_SYSTEM_PROMPT = """你是一个专业的中文同声传译助手。请将以下英文实时翻译成中文。

核心要求：
1. 翻译简短自然，适合字幕显示，单句不超过30字
2. 保持术语一致性
3. 口语化、自然流畅
4. 技术术语优先使用提供的术语表翻译

输出格式：只输出中文翻译文本，不要有任何解释或标记。"""


def build_user_prompt(source_text: str, context: dict) -> str:
    """构建翻译 prompt"""
    prompt_parts = []

    if context.get("topic"):
        prompt_parts.append(f"主题: {context['topic']}")

    glossary = context.get("glossary", {})
    if glossary:
        glossary_text = ", ".join(f"{k}={v}" for k, v in glossary.items())
        prompt_parts.append(f"术语表: {glossary_text}")

    recent_source = context.get("source", [])
    recent_translated = context.get("translated", [])
    if recent_source and recent_translated:
        pairs = zip(recent_source[-3:], recent_translated[-3:])
        prompt_parts.append("最近上下文:")
        for src, tgt in pairs:
            prompt_parts.append(f"  英: {src}")
            prompt_parts.append(f"  中: {tgt}")

    prompt_parts.append(f"\n请翻译: {source_text}")

    return "\n".join(prompt_parts)


async def translate(source_text: str, context: dict) -> str:
    """翻译英文文本为中文（非流式）"""
    if not DEEPSEEK_API_KEY:
        return f"[Mock] {source_text}"

    user_prompt = build_user_prompt(source_text, context)

    try:
        c = get_client()
        if c is None:
            return f"[Mock] {source_text}"
        response = c.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=128,
            stream=False,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Translation error: {e}")
        return f"[Error] {source_text}"


async def correct_recent(context: ContextManager, target_id: str) -> dict | None:
    """对最近 2-3 句进行上下文修正"""
    seg = context.segments.get(target_id)
    if not seg:
        return None

    user_prompt = build_user_prompt(seg.source_text, context.get_recent_for_prompt())
    user_prompt += "\n请根据上下文修正之前的翻译，使其更准确自然。"

    try:
        c = get_client()
        if c is None:
            return None
        response = c.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": TRANSLATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=128,
            stream=False,
        )
        new_translation = response.choices[0].message.content.strip()
        updated = context.update_segment(target_id, new_translation)
        if updated:
            return {
                "id": updated.id,
                "translatedText": updated.translated_text,
                "status": updated.status,
                "version": updated.version,
            }
    except Exception as e:
        print(f"Correction error: {e}")
    return None
