"""VoiceBridge 后端主入口 - FastAPI + WebSocket"""
import asyncio
import json
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from asr_client import TencentASRClient
from context_manager import ContextManager
from translator import translate, correct_recent

app = FastAPI(title="VoiceBridge")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    print("[WS] Client connected")

    ctx = ContextManager(max_context=5)
    asr = TencentASRClient(engine_model_type="16k_en")

    # Mock 模式标记，当 ASR 不可用时使用模拟数据
    mock_mode = False
    mock_counter = 0
    mock_texts = [
        "Today we're going to talk about caching strategies in distributed systems.",
        "The first approach is write-through cache, which updates both the cache and the database simultaneously.",
        "This ensures data consistency but adds latency to write operations.",
        "The second approach is write-back cache, where we only update the cache first.",
        "This improves write performance but risks data loss if the cache fails.",
    ]

    async def connect_asr():
        nonlocal mock_mode
        if not asr:
            return
        success, msg = await asr.connect()
        if not success:
            print(f"[ASR] Connection failed: {msg}, switching to mock mode")
            mock_mode = True
        else:
            print(f"[ASR] Connected: {msg}")

    asr_task = asyncio.create_task(connect_asr())
    recv_task = None

    start_time = time.time()

    try:
        while True:
            data = await ws.receive()

            if "text" in data:
                msg = json.loads(data["text"])
                msg_type = msg.get("type", "")

                if msg_type == "config":
                    ctx.set_config(
                        topic=msg.get("topic", ""),
                        glossary=msg.get("glossary", {}),
                    )
                    print(f"[WS] Config updated: topic={ctx.topic}, glossary={ctx.glossary}")

                elif msg_type == "pause":
                    # 暂停 ASR
                    if recv_task and not recv_task.done():
                        recv_task.cancel()
                    print("[WS] Paused")

                elif msg_type == "resume":
                    # 恢复 ASR
                    if asr.is_connected or mock_mode:
                        recv_task = asyncio.create_task(receive_results(ws, asr, ctx, mock_mode))

                elif msg_type == "clear":
                    ctx = ContextManager(max_context=5)
                    await ws.send_json({"type": "clear"})
                    print("[WS] Cleared")

            elif "bytes" in data:
                pcm = data["bytes"]
                if asr.is_connected:
                    await asr.send_audio(pcm)

                # 启动 ASR 结果接收（首次收到音频时）
                if recv_task is None or recv_task.done():
                    await asyncio.sleep(0.5)  # 等 ASR 连接就绪
                    recv_task = asyncio.create_task(
                        receive_results(ws, asr, ctx, mock_mode, start_time)
                    )

    except WebSocketDisconnect:
        print("[WS] Client disconnected")
    finally:
        if recv_task and not recv_task.done():
            recv_task.cancel()
        if asr_task and not asr_task.done():
            asr_task.cancel()
        await asr.close()


async def receive_results(ws: WebSocket, asr: TencentASRClient,
                          ctx: ContextManager, mock_mode: bool,
                          start_time: float):
    """接收 ASR 结果并触发翻译"""
    last_final = ""
    mock_idx = 0

    # Mock 模式文本列表
    mock_texts = [
        "Today we're going to talk about caching strategies in distributed systems.",
        "The first approach is write-through cache, which updates both the cache and the database simultaneously.",
        "This ensures data consistency but adds latency to write operations.",
        "The second approach is write-back cache, where we only update the cache first.",
        "This improves write performance but risks data loss if the cache fails.",
    ]

    while True:
        if mock_mode:
            await asyncio.sleep(3)  # 模拟每3秒一个新句子
            if mock_idx >= len(mock_texts):
                break
            text = mock_texts[mock_idx]
            mock_idx += 1
            elapsed = time.time() - start_time

            seg = ctx.add_segment(
                source_text=text,
                translated_text="",
                start_time=elapsed - 3,
                end_time=elapsed,
            )

            # 发送 interim
            await ws.send_json({
                "type": "subtitle",
                "segment": {
                    "id": seg.id,
                    "startTime": seg.start_time,
                    "endTime": seg.end_time,
                    "sourceText": text,
                    "translatedText": "...",
                    "status": "interim",
                    "version": 1,
                }
            })

            # 翻译
            context = ctx.get_recent_for_prompt()
            translated = await translate(text, context)
            seg.translated_text = translated

            # 发送 final
            await ws.send_json({
                "type": "subtitle",
                "segment": {
                    "id": seg.id,
                    "startTime": seg.start_time,
                    "endTime": seg.end_time,
                    "sourceText": text,
                    "translatedText": translated,
                    "status": "final",
                    "version": 1,
                }
            })
        else:
            result = await asr.receive_result()
            if result is None:
                await asyncio.sleep(0.05)
                continue

            code = result.get("code", -1)
            if code != 0:
                continue

            res = result.get("result", {})
            slice_type = res.get("slice_type", 0)
            text = res.get("voice_text_str", "")

            if not text:
                continue

            elapsed = time.time() - start_time

            if slice_type == 1:  # Interim
                await ws.send_json({
                    "type": "subtitle",
                    "segment": {
                        "id": "interim",
                        "startTime": elapsed - 1,
                        "endTime": elapsed,
                        "sourceText": text,
                        "translatedText": "...",
                        "status": "interim",
                        "version": 1,
                    }
                })

            elif slice_type == 2:  # Final
                if text == last_final:
                    continue
                last_final = text

                seg = ctx.add_segment(
                    source_text=text,
                    translated_text="",
                    start_time=elapsed - 2,
                    end_time=elapsed,
                )

                context = ctx.get_recent_for_prompt()
                translated = await translate(text, context)
                seg.translated_text = translated

                await ws.send_json({
                    "type": "subtitle",
                    "segment": {
                        "id": seg.id,
                        "startTime": seg.start_time,
                        "endTime": seg.end_time,
                        "sourceText": text,
                        "translatedText": translated,
                        "status": "final",
                        "version": 1,
                    }
                })


if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT
    uvicorn.run(app, host=HOST, port=PORT)
