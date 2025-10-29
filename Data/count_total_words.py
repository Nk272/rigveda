import json
import re
import sys
from typing import Any, Dict


wordPattern = re.compile(r"\b[\w’'-]+\b", flags=re.UNICODE)


def CountWordsInText(text: str) -> int:
    return len(wordPattern.findall(text))


def CountTotalWords(jsonPath: str) -> int:
    with open(jsonPath, "r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    totalWords = 0
    books = data.get("books", {})
    for _, book in books.items():
        hymns = book.get("hymns", {})
        for _, hymn in hymns.items():
            text = hymn.get("text", "") or ""
            if text:
                totalWords += CountWordsInText(text)
    return totalWords


def Main() -> None:
    defaultPath = "/Users/nikunjgoyal/Codes/rigveda/Data/JSONMaps/rigveda_data.json"
    jsonPath = sys.argv[1] if len(sys.argv) > 1 else defaultPath
    print(CountTotalWords(jsonPath))


if __name__ == "__main__":
    Main()


