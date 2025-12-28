from dotenv import load_dotenv
load_dotenv()

from app.crawler.search import discover_channels
from app.crawler.messages import fetch_messages
from app.crawler.discovery import is_shop_channel
from app.extractor.product import extract_products
import sys


def main():
    channels = discover_channels()

    all_products = []

    for ch in channels:
        messages = fetch_messages(ch)

        verdict = is_shop_channel(messages)
        if verdict["فروشگاهی_است"]:
            products = extract_products(messages)
            all_products.extend(products)

    print(all_products)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        # Provide a clearer runtime message (e.g., missing env vars) and exit
        print("Runtime error:", e)
        print("Ensure required environment variables are set: EITAAYAR_TOKEN and GROQ_API_KEY")
        sys.exit(1)
