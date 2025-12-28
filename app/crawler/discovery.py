from app.ai.groq_client import ask_groq
from app.ai.prompts import CHANNEL_VALIDATOR

def is_shop_channel(messages):
    prompt = CHANNEL_VALIDATOR.format(messages=messages[:10])
    return ask_groq(prompt)
