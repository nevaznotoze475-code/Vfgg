# twork/tdrainer/utils.py
def escape_md(text: str) -> str:
    special_chars = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in special_chars else char for char in text)