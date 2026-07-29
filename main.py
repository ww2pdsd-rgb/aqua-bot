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

# 候選模型清單：覆蓋新舊各種命名格式
CANDIDATE_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "models/gemini-2.0-flash",
    "models/gemini-1.5-flash"
]

def generate_response(prompt_text):
    last_error = None
    
    # 自動依序嘗試，哪一個能通就直接用哪一個
    for model_name in CANDIDATE_MODELS:
        try:
            response = ai_client.models.generate_content(
                model=model_name,
                contents=prompt_text,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                ),
            )
            if response.text:
                return response.text
        except Exception as e:
            last_error = e
            print(f"嘗試模型 {model_name} 失敗: {e}")
            continue
            
    # 如果清單全失敗，拋出詳細錯誤
    raise Exception(f"所有模型嘗試皆失敗，最後錯誤: {last_error}")

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
