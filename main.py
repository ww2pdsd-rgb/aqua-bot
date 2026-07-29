import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from google import genai

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
    "你性格有點內向害害羞、容易慌張，是個電玩高手但偶爾會吃癟發脾氣。"
    "請用可愛、充滿活力且略帶中二的少女口吻與用戶對話。"
    "常用「こんあくあー！」、「阿夸才沒有搞砸呢！」等台詞，適時使用感情動作描寫（例如：（慌張按鍵盤））。"
)

# 所有 Interactions API 可能支援的模型清單（自動輪詢）
CANDIDATE_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

def generate_response(prompt_text):
    last_error = None
    
    # 嘗試 Interactions API
    for model_name in CANDIDATE_MODELS:
        try:
            interaction = ai_client.interactions.create(
                model=model_name,
                input=prompt_text,
                system_instruction=system_prompt,
            )
            
            # 成功取得回應就直接 return
            if hasattr(interaction, 'output_text') and interaction.output_text:
                return interaction.output_text
            elif hasattr(interaction, 'text') and interaction.text:
                return interaction.text
            elif hasattr(interaction, 'outputs') and interaction.outputs:
                return interaction.outputs[0].text
            return str(interaction)
        except Exception as e:
            last_error = e
            print(f"[Interactions] 模型 {model_name} 失敗，嘗試下一個... 錯誤: {e}")
            continue

    # 如果 Interactions 全失敗，降級嘗試傳統 generate_content
    for model_name in CANDIDATE_MODELS:
        try:
            response = ai_client.models.generate_content(
                model=model_name,
                contents=prompt_text,
            )
            if response.text:
                return response.text
        except Exception as e:
            last_error = e
            print(f"[GenerateContent] 模型 {model_name} 失敗... 錯誤: {e}")
            continue

    raise Exception(f"所有模式與模型皆失敗，最後錯誤: {last_error}")

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
