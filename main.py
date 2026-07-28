import os
import asyncio
import discord
import google.generativeai as genai

# 1. 初始化 Gemini API
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

system_prompt = (
    "你是 hololive 旗下二期生的電玩女僕「湊あくあ（湊阿夸）」。"
    "你性格有點內向害羞、容易慌張，是個電玩高手但偶爾會吃癟發脾氣。"
    "請用可愛、充滿活力且略帶中二的少女口吻與用戶對話。"
    "常用「こんあくあー！」、「阿夸才沒有搞砸呢！」等台詞，適時使用感情動作描寫（例如：（慌張按鍵盤））。"
)

# 使用 gemini-1.5-flash
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=system_prompt
)

# 2. 初始化 Discord Bot
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

    # 判斷是否為你的 ID
    if message.author.id == YOUR_USER_ID:
        async with message.channel.typing():
            try:
                # 使用 asyncio.to_thread 避免 Blocking 事件迴圈
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: model.generate_content(message.content)
                )

                if response and response.text:
                    await message.channel.send(response.text)
                else:
                    await message.channel.send("こんあくあー！阿夸剛才思考過久，再跟我說一次好嗎？")
            except Exception as e:
                print(f"錯誤詳情: {e}")
                await message.channel.send(f"阿夸電腦當機啦！（錯誤：{e}）")

client.run(os.getenv("DISCORD_BOT_TOKEN"))
