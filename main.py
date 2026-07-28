import os
import discord
import google.generativeai as genai

# 1. 初始化 Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=(
        "你是 hololive 旗下二期生的電玩女僕「湊あくあ（湊阿夸）」。"
        "你性格有點內向害羞、容易慌張，是個電玩高手但偶爾會吃癟發脾氣。"
        "請用可愛、充滿活力且略帶中二的少女口吻與用戶對話。"
        "常用「こんあくあー！」、「阿夸才沒有搞砸呢！」等台詞，適時使用感情動作描寫（例如：（慌張按鍵盤））。"
    )
)

# 2. 初始化 Discord Bot 權限
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 你的 Discord User ID（避免機器人回應別人的訊息或回應自己）
YOUR_USER_ID = int(os.getenv("YOUR_USER_ID", "0"))

@client.event
async def on_ready():
    print(f'⚓︎ 湊あくあ 已成功連線！登入身份：{client.user}')

@client.event
async def on_message(message):
    # 忽略機器人自己的訊息
    if message.author == client.user:
        return

    # 只回應你發出的訊息
    if message.author.id == YOUR_USER_ID:
        # 當前頻道顯示正在打字...
        async with message.channel.typing():
            try:
                # 送給 Gemini 生成回答
                response = model.generate_content(message.content)
                if response.text:
                    await message.channel.send(response.text)
            except Exception as e:
                print(f"Error: {e}")

# 啟動 Bot
client.run(os.getenv("DISCORD_BOT_TOKEN"))
