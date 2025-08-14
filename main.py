import os
import json
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from keep_alive import keep_alive

# .env fayldan tokenlarni yuklaymiz
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

bot = telebot.TeleBot(TOKEN)

# Foydalanuvchi ma'lumotlarini yuklash/saqlash
def load_user_data():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_data(data):
    with open("users.json", "w") as f:
        json.dump(data, f, indent=4)

user_data = load_user_data()

# Tilga mos prompt
def get_prompt_by_language(lang, prompt):
    if lang == "uz":
        return f"Savolga do‘stona, tushunarli, faktlarga asoslangan va emojili tarzda javob yozing.\n\nSavol: {prompt}\nJavob:"
    elif lang == "ru":
        return f"Ответь на вопрос дружелюбно, точно, с фактами и смайликами.\n\nВопрос: {prompt}\nОтвет:"
    else:
        return f"Answer in a friendly, factual way with emojis.\n\nQuestion: {prompt}\nAnswer:"

# Hugging Face API orqali javob olish
def ask_huggingface(prompt):
    API_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 80, "temperature": 0.7, "do_sample": True}
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        if response.status_code == 200:
            output = response.json()
            if isinstance(output, dict) and 'generated_text' in output:
                return output['generated_text'].split("Javob:")[-1].strip()
            elif isinstance(output, list) and 'generated_text' in output[0]:
                return output[0]['generated_text'].split("Javob:")[-1].strip()
            else:
                return "😕 Javobni tushunmadim."
        elif response.status_code == 503:
            return "⏳ Model yuklanmoqda, qayta urinib ko‘ring."
        else:
            return f"❌ API xatosi: {response.status_code}"
    except Exception as e:
        return f"⚠️ Xatolik: {str(e)}"

# /start
@bot.message_handler(commands=['start'])
def welcome(message):
    user_id = str(message.chat.id)
    if user_id not in user_data:
        user_data[user_id] = {"language": "uz"}
        save_user_data(user_data)

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🇺🇿 O‘zbekcha", callback_data="lang_uz"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    bot.send_message(message.chat.id, "Tilni tanlang / Choose your language 👇", reply_markup=markup)

# Til tanlash
@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def handle_language(call):
    user_id = str(call.message.chat.id)
    lang = call.data.split("_")[1]
    user_data[user_id]["language"] = lang
    save_user_data(user_data)

    texts = {
        "uz": "✅ Til o‘zbek tiliga o‘zgartirildi!",
        "ru": "✅ Язык изменен на русский!",
        "en": "✅ Language changed to English!"
    }
    bot.answer_callback_query(call.id, texts[lang])
    bot.send_message(call.message.chat.id, texts[lang])

# /help
@bot.message_handler(commands=['help'])
def help_command(message):
    lang = user_data.get(str(message.chat.id), {}).get("language", "uz")
    texts = {
        "uz": "✳️ Savol bering, qisqa va tushunarli javob olasiz. Tilni o‘zgartirish uchun /language ni bosing.",
        "ru": "✳️ Задайте вопрос. Чтобы сменить язык, нажмите /language.",
        "en": "✳️ Ask a question. To change the language, use /language."
    }
    bot.reply_to(message, texts[lang])

# /language
@bot.message_handler(commands=['language'])
def language_command(message):
    welcome(message)

# Har qanday matn
@bot.message_handler(func=lambda m: True)
def chat(message):
    bot.send_chat_action(message.chat.id, 'typing')
    user_id = str(message.chat.id)
    lang = user_data.get(user_id, {}).get("language", "uz")
    prompt = get_prompt_by_language(lang, message.text)
    javob = ask_huggingface(prompt)
    bot.reply_to(message, javob)

# Server ishga tushirish
if __name__ == "__main__":
    keep_alive()
    print("🤖 Bot ishga tushdi...")
    bot.infinity_polling()
