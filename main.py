import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from google import genai
from google.genai import types

# ================= 1. Web Server 防 Render 逾時 =================
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Aqua Bot is Running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# ================= 2. 初始化 Gemini Client =================
api_key = os.getenv("GEMINI_API_KEY")
ai_client = genai.Client(api_key=api_key)

system_prompt = (
    "你是 hololive 旗下二期生的電玩女僕「湊あくあ（湊阿夸）」。"
    "你性格有點內向害羞、容易慌張，是個電玩高手但偶爾會吃癟發脾氣。"
    "請用可愛、充滿活力且略帶中二的少女口吻與用戶對話。"
    "常用「こんあくあー！」、「阿夸才沒有搞砸呢！」等台詞，適時使用感情動作描寫（例如：（慌張按鍵盤））。"
)

# 動態取得當前 API Key 真正擁有的可用模型清單
def find_working_model():
    try:
        models = list(ai_client.models.list())
        model_names = [m.name for m in models]
        print(f"⚓︎ 你的 API Key 當前支援的所有模型：{model_names}")
        
        # 尋找名稱含有 flash 或 generateContent 的模型
        for m in models:
            name = m.name
            if "flash" in name or "gemini" in name:
                print(f"⚓︎ 自動鎖定首選模型：{name}")
                return name
        
        if model_names:
            return model_names[0]
    except Exception as e:
        print(f"無法獲取模型清單: {e}")
    
    return "models/gemini-2.0-flash"

ACTIVE_MODEL = find_working_model()

def generate_response(prompt_text):
    global ACTIVE_MODEL
    try:
        response = ai_client.models.generate_content(
            model=ACTIVE_MODEL,
            contents=prompt_text,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        return response.text
    except Exception as e:
        print(f"原模型 {ACTIVE_MODEL} 呼叫失敗 ({e})，重新動態尋找可用模型...")
        # 若失敗則現場重新撈一次可用模型備援
        ACTIVE_MODEL = find_working_model()
        response = ai_client.models.generate_content(
            model=ACTIVE_MODEL,
            contents=prompt_text,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        return response.text

# ================= 3. 初始化 Discord Bot =================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

YOUR_USER_ID = int(os.getenv("YOUR_USER_ID", "0"))

@client.event
async def on_ready():
    print(f'⚓︎ 湊あくあ 已成功連線！登入身份：{client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.author.id == YOUR_USER_ID:
        async with message.channel.typing():
            try:
                loop = asyncio.get_running_loop()
                reply_text = await loop.run_in_executor(
                    None, 
                    lambda: generate_response(message.content)
                )
                
                if reply_text:
                    await message.channel.send(reply_text)
                else:
                    await message.channel.send("こんあくあー！阿夸剛才愣了一下，再跟我說一次好嗎？")
            except Exception as e:
                print(f"錯誤詳情: {e}")
                await message.channel.send(f"阿夸電腦當機啦！（錯誤：{e}）")

client.run(os.getenv("DISCORD_BOT_TOKEN"))
