from dataclasses import dataclass

@dataclass
class Channel:
    username: str
    is_shop: bool
    confidence: float
