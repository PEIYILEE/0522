import asyncio
import serial
from aiohttp import web
from typing import Optional
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

# === 環境變數 ===
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === Serial 連線 ===
ser = serial.Serial('COM4', 9600)

# === WebSocket 用戶清單 ===
ws_clients = set()

# === HTML 首頁 ===
async def index(request):
    return web.FileResponse('./index.html')

# === GPT 呼叫函式 ===
async def ask_openai(category: str, sub: str) -> str:
    prompt = (
        f"我今天想吃「{category}」的「{sub}」，請你提供兩段回覆："
        f"\n1. 健康建議：簡單說明如何吃得更健康。"
        f"\n2. 卡路里：估算這道料理平均會有多少大卡。"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ 發生錯誤：{e}"

# === WebSocket handler ===
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    ws_clients.add(ws)
    print('🔗 WebSocket 已連線')

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    category = data.get('category')
                    sub = data.get('sub')
                    if category and sub:
                        print(f'🎯 接收到用戶選擇: {category} > {sub}')
                        reply = await ask_openai(category, sub)
                        await ws.send_str(reply)
                except Exception as e:
                    print(f"⚠️ JSON 錯誤：{e}")
    finally:
        ws_clients.remove(ws)
        print('❌ WebSocket 離線')

    return ws

# === Serial 指令翻譯 ===
def translate(raw: str) -> Optional[str]:
    raw = raw.strip()
    if   raw.startswith('↑') or 'Forward'  in raw: return 'UP'
    elif raw.startswith('↓') or 'Backward' in raw: return 'DOWN'
    elif raw.startswith('←') or 'Left'     in raw: return 'LEFT'
    elif raw.startswith('→') or 'Right'    in raw: return 'RIGHT'
    elif '✔' in raw or 'Select'  in raw or 'CONFIRM' in raw: return 'CONFIRM'
    elif '✖' in raw or 'Cancel'  in raw or 'REJECT'  in raw: return 'REJECT'
    else: return None

# === 背景 Task：讀取 Serial 資料，送給前端 ===
async def read_from_serial():
    while True:
        if ser.in_waiting:
            raw = ser.readline().decode('utf-8', errors='ignore')
            cmd = translate(raw)
            if cmd:
                print(f'🠞 轉換: {raw.strip()}  ➜  {cmd}')
                for ws in ws_clients.copy():
                    if not ws.closed:
                        await ws.send_str(cmd)
        await asyncio.sleep(0.03)

# === 啟動應用 ===
async def main():
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_get('/ws', websocket_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8000)
    await site.start()

    print('🌐 HTTP:       http://localhost:8000')
    print('🌀 WebSocket:  ws://localhost:8000/ws')

    await read_from_serial()

# === 執行主程式 ===
if __name__ == '__main__':
    asyncio.run(main())
