"""VoiceBridge 后端主入口 - FastAPI + WebSocket"""
import asyncio
import json
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from asr_client import TencentASRClient
from context_manager import ContextManager
from translator import translate

app = FastAPI(title="VoiceBridge")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "ok"}


# ---- Mock 数据 ----
MOCK_TEXTS = [
    "Today we're going to talk about caching strategies in distributed systems.",
    "The first approach is write-through cache, which updates both the cache and the database simultaneously.",
    "This ensures data consistency but adds latency to write operations.",
    "The second approach is write-back cache, where we only update the cache first.",
    "This improves write performance but risks data loss if the cache fails.",
]


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    print("[WS] Client connected")

    ctx = ContextManager(max_context=5)
    start_time = time.time()

    # 1. 连接 ASR（带超时保护，不阻塞 WebSocket 太久）
    asr = TencentASRClient(engine_model_type="16k_en")
    try:
        success, msg = await asyncio.wait_for(asr.connect(), timeout=5.0)
    except asyncio.TimeoutError:
        success, msg = False, "连接超时（5s）"
    mock_mode = not success
    if mock_mode:
        print(f"[ASR] FAILED: {msg} → 使用 Mock 模式")
    else:
        print(f"[ASR] Connected ✓")

    recv_task = None

    try:
        while True:
            data = await ws.receive()

            # ---- 文本控制消息 ----
            if "text" in data:
                msg = json.loads(data["text"])
                msg_type = msg.get("type", "")

                if msg_type == "config":
                    ctx.set_config(
                        topic=msg.get("topic", ""),
                        glossary=msg.get("glossary", {}),
                    )
                    print(f"[WS] Config: topic={ctx.topic}, glossary={ctx.glossary}")
                elif msg_type == "clear":
                    ctx = ContextManager(max_context=5)
                    await ws.send_json({"type": "clear"})
                elif msg_type == "pause" and recv_task:
                    recv_task.cancel()
                elif msg_type == "resume":
                    recv_task = asyncio.create_task(
                        _asr_loop(ws, asr, ctx, mock_mode, start_time)
                    )

            # ---- 二进制 PCM 音频数据 ----
            elif "bytes" in data and (asr.is_connected or mock_mode):
                if not mock_mode:
                    await asr.send_audio(data["bytes"])

                # 首次收到音频时启动 ASR 结果接收循环
                if recv_task is None or recv_task.done():
                    recv_task = asyncio.create_task(
                        _asr_loop(ws, asr, ctx, mock_mode, start_time)
                    )

    except WebSocketDisconnect:
        print("[WS] Client disconnected")
    finally:
        if recv_task and not recv_task.done():
            recv_task.cancel()
        await asr.close()


async def _asr_loop(ws: WebSocket, asr: TencentASRClient,
                    ctx: ContextManager, mock_mode: bool,
                    start_time: float):
    """循环接收 ASR 结果 → 翻译 → 发送字幕"""
    mock_idx = 0
    last_final = ""

    while True:
        if mock_mode:
            # ---- Mock 模式：每 4 秒一句 ----
            await asyncio.sleep(4)
            if mock_idx >= len(MOCK_TEXTS):
                break
            source_text = MOCK_TEXTS[mock_idx]
            mock_idx += 1
            elapsed = time.time() - start_time

            # interim
            await ws.send_json({
                "type": "subtitle",
                "segment": {
                    "id": "interim", "startTime": elapsed - 2,
                    "endTime": elapsed, "sourceText": source_text,
                    "translatedText": "...", "status": "interim", "version": 1,
                }
            })

            # 翻译
            translated = await translate(source_text, ctx.get_recent_for_prompt())
            seg = ctx.add_segment(source_text, translated, elapsed - 2, elapsed)

            # final
            await ws.send_json({
                "type": "subtitle",
                "segment": {
                    "id": seg.id, "startTime": seg.start_time,
                    "endTime": seg.end_time, "sourceText": source_text,
                    "translatedText": translated, "status": "final", "version": 1,
                }
            })
        else:
            # ---- 真实 ASR 模式 ----
            if not asr.is_connected:
                print("[ASR] Disconnected, stopping receive loop")
                break

            try:
                result = await asyncio.wait_for(asr.receive_result(), timeout=0.15)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[ASR] Receive error: {e}")
                break

            if result is None:
                await asyncio.sleep(0.05)
                continue

            code = result.get("code", -1)
            if code != 0:
                print(f"[ASR] Error code: {code}, msg: {result.get('message', '')}")
                continue

            res = result.get("result", {})
            slice_type = res.get("slice_type", 0)
            text = res.get("voice_text_str", "")
            if not text:
                continue

            elapsed = time.time() - start_time

            if slice_type == 1:
                # Interim — 只发原文，不翻译
                await ws.send_json({
                    "type": "subtitle",
                    "segment": {
                        "id": "interim", "startTime": elapsed - 1,
                        "endTime": elapsed, "sourceText": text,
                        "translatedText": "", "status": "interim", "version": 1,
                    }
                })

            elif slice_type == 2:
                # Final — 去重后翻译
                text = text.strip()
                if not text or text == last_final:
                    continue
                last_final = text

                translated = await translate(text, ctx.get_recent_for_prompt())
                seg = ctx.add_segment(text, translated, elapsed - 2, elapsed)

                await ws.send_json({
                    "type": "subtitle",
                    "segment": {
                        "id": seg.id, "startTime": seg.start_time,
                        "endTime": seg.end_time, "sourceText": text,
                        "translatedText": translated, "status": "final", "version": 1,
                    }
                })


if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT
    uvicorn.run(app, host=HOST, port=PORT)
