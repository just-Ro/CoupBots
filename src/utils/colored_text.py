COLORED_TEXT = True

def red(text: str) -> str:
    return f"\033[91m{text}\033[0m" if COLORED_TEXT else text

def green(text: str) -> str:
    return f"\033[92m{text}\033[0m" if COLORED_TEXT else text

def yellow(text: str) -> str:
    return f"\033[93m{text}\033[0m" if COLORED_TEXT else text

def blue(text: str) -> str:
    return f"\033[94m{text}\033[0m" if COLORED_TEXT else text