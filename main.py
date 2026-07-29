import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
import google.generativeai as genai

# ================= 1. Web Server 防判斷逾時 =================
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

# ================= 2. 初始化 Gemini API =================
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

system_prompt = (
    "你是 hololive 旗下二期生的電玩女僕「湊あくあ（湊阿夸）」。"
    "你性格有點內向害羞、容易慌張，是個電玩高手但偶爾會吃癟發脾氣。"
    "請用可愛、充滿活力且略帶中二的少女口吻與用戶對話。"
    "常用「こんあくあー！」、「阿夸才沒有搞砸呢！」等台詞，適時使用感情動作描寫（例如：（慌張按鍵盤））。"
)

# 測試最新與標準相容的模型名稱
MODEL_CANDIDATES = [
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro-latest"
]

def generate_with_fallback(prompt_text):
    last_error = None
    for model_name in MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt
            )
            response = model.generate_content(prompt_text)
            if response and response.text:
                return response.text
        except Exception as e:
            last_error = e
            print(f"嘗試模型 {model_name} 失敗: {e}")
            continue
    raise Exception(f"API 金鑰無效或權限不符。最後錯誤：{last_error}")

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
                    lambda: generate_with_fallback(message.content)
                )
                await message.channel.send(reply_text)
            except Exception as e:
                print(f"錯誤詳情: {e}")
                await message.channel.send(f"阿夸電腦當機啦！（錯誤：{e}）")

client.run(os.getenv("DISCORD_BOT_TOKEN"))
