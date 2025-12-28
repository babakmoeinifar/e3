import re

def extract_products(messages):
    products = []

    for msg in messages:
        text = msg.get("text", "")
        price = re.findall(r"\d{1,3}(?:,\d{3})*", text)

        if price:
            products.append({
                "title": text[:50],
                "price": price[0],
                "raw_text": text
            })

    return products
