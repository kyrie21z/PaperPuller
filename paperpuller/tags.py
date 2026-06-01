from __future__ import annotations


KEYWORDS = {
    "OCR": ["ocr", "optical character recognition", "document understanding", "text spotting"],
    "STR": ["scene text", "text recognition", "text detection", "text recognizer"],
    "ViT": ["vision transformer", "vit", "transformer-based vision", "visual transformer"],
    "MAE": ["masked autoencoder", "mae", "masked image modeling", "self-supervised visual"],
    "Augmentation": ["augmentation", "synthetic data", "domain randomization", "data synthesis"],
}


def local_topic_tags(title: str, abstract: str) -> list[str]:
    haystack = f"{title}\n{abstract}".lower()
    tags = [
        tag
        for tag, keywords in KEYWORDS.items()
        if any(keyword in haystack for keyword in keywords)
    ]
    return tags or ["Other"]

