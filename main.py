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

def get_best_model():
    """優先嘗試標準官方 2.0 正式版，若失敗則動態查詢帳號可用清單"""
    candidate_list = ['models/gemini-2.0-flash', 'gemini-2.0-flash']
    
    # 先測試預設清單
    for model_id in candidate_list:
        try:
            ai_client.models.get(model=model_id)
            print(f"⚓︎ 成功確認模型可用：{model_id}")
            return model_id
        except Exception:
            continue

    # 若預設失敗，從 API 自動列出當前金鑰可用的第一個模型
    try:
        models = list(ai_client.models.list())
        for m in models:
            m_name = getattr(m, 'name', str(m))
            if 'flash' in m_name or 'gemini' in m_name:
                print(f"⚓︎ 動態選用帳號可用模型：{m_name}")
                return m_name
    except Exception as e:
        print(f"列出模型失敗: {e}")
        
    return 'gemini-2.0-flash'

# 啟動時先鎖定最佳可用模型
ACTIVE_MODEL = get_best_model()

def generate_response(prompt_text):
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
