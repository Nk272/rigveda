import json
import os
import random
import sys
import time
from collections import deque
from typing import Any, Deque, Dict, List, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

MAX_REQUESTS_PER_MINUTE = 30
MAX_TOKENS_PER_MINUTE = 8000
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
PER_CALL_DELAY_SECONDS = 60
inputPath = "/Users/nikunjgoyal/Codes/rigveda/Data/JSONMaps/rigveda_data.json"
outputPath = "/Users/nikunjgoyal/Codes/rigveda/Data/JSONMaps/rigveda_summaries.json"

def LoadJson(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def SaveJson(path: str, data: Dict[str, Any]) -> None:
    tmpPath = f"{path}.tmp"
    with open(tmpPath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmpPath, path)


def BuildMessages(hymnText: str) -> List[Dict[str, str]]:
    system = (
        "You are a concise literary summarizer. "
        "Summarize the given Rigveda hymn in exactly one sentence, tone should be interesting and engaging, not boring and dry."
        "plain modern English, no proper nouns beyond those present, no markdown."
    )
    user = (
        "Summarize in one sentence:\n\n" + hymnText.strip()
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def Log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def PostChatCompletion(apiKey: str, messages: List[Dict[str, str]]) -> Tuple[str, Dict[str, Any]]:
    body = {
        "model": "openai/gpt-oss-120b",
        "messages": messages,
        "temperature": 0.2,
        "max_completion_tokens": 64,
        "reasoning_effort": "low",
    }
    payload = json.dumps(body).encode("utf-8")
    req = Request(
        GROQ_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {apiKey}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(req, timeout=90) as resp:
        respBody = resp.read().decode("utf-8")
        data = json.loads(respBody)
        content = data["choices"][0]["message"]["content"].strip()
        return content, data


def SendWithRetries(fn, maxAttempts: int = 8, baseDelaySeconds: float = 1.5) -> Any:
    attempt = 0
    while True:
        try:
            return fn()
        except HTTPError as e:
            print(e.headers)
            attempt += 1
            if attempt >= maxAttempts:
                Log(f"request: failed after {attempt} attempts, status={getattr(e, 'code', None)}")
                raise
            status = getattr(e, "code", None)
            retryAfter = e.headers.get("Retry-After") if hasattr(e, "headers") and e.headers else None
            if status in (429, 500, 502, 503, 504):
                if retryAfter:
                    try:
                        delay = float(retryAfter)
                    except ValueError:
                        delay = baseDelaySeconds * attempt
                else:
                    delay = baseDelaySeconds * attempt
                delay += random.uniform(0, 0.5)
                Log(f"request: transient error status={status}, attempt={attempt}, sleeping={delay:.2f}s")
                time.sleep(delay)
                continue
            Log(f"request: non-retryable HTTP error status={status}, attempt={attempt}")
            raise
        except URLError:
            Log(f"request: URLError, attempt={attempt}")
            raise


def SummarizeHymn(apiKey: str, hymnText: str) -> Tuple[str, Dict[str, Any]]:
    messages = BuildMessages(hymnText)
    content, data = SendWithRetries(lambda: PostChatCompletion(apiKey, messages))
    return content, data


def IterateHymns(data: Dict[str, Any]):
    books = data.get("books", {})
    for bookKey in sorted(books.keys(), key=lambda x: int(x)):
        hymns = books[bookKey].get("hymns", {})
        for hymnId in sorted(hymns.keys(), key=lambda x: int(x)):
            hymn = hymns[hymnId]
            text = hymn.get("text", "") or ""
            yield hymnId, text

class RateLimiter:
    def __init__(self, maxRequestsPerMinute: int = 30, maxTokensPerMinute: int = 8000) -> None:
        self.maxRequestsPerMinute = maxRequestsPerMinute
        self.maxTokensPerMinute = maxTokensPerMinute
        self.requestTimes: Deque[float] = deque()
        self.tokenEvents: Deque[Tuple[float, int]] = deque()

    def _prune(self, now: float) -> None:
        cutoff = now - 60.0
        while self.requestTimes and self.requestTimes[0] < cutoff:
            self.requestTimes.popleft()
        while self.tokenEvents and self.tokenEvents[0][0] < cutoff:
            self.tokenEvents.popleft()

    def _currentTokenSum(self) -> int:
        return sum(t for _, t in self.tokenEvents)

    def WaitForCapacity(self, neededTokens: int) -> None:
        while True:
            now = time.time()
            self._prune(now)
            reqs = len(self.requestTimes)
            tokens = self._currentTokenSum()
            if reqs < self.maxRequestsPerMinute and (tokens + neededTokens) <= self.maxTokensPerMinute:
                return

            sleepUntil = None

            if reqs >= self.maxRequestsPerMinute and self.requestTimes:
                t = self.requestTimes[0] + 60.0
                sleepUntil = t if sleepUntil is None else min(sleepUntil, t)

            if (tokens + neededTokens) > self.maxTokensPerMinute and self.tokenEvents:
                running = tokens
                target = self.maxTokensPerMinute - neededTokens
                expireTime = None
                for ts, tok in self.tokenEvents:
                    running -= tok
                    expireTime = ts + 60.0
                    if running <= target:
                        break
                if expireTime is not None:
                    sleepUntil = expireTime if sleepUntil is None else min(sleepUntil, expireTime)

            if sleepUntil is None:
                sleepUntil = now + 1.0
            delay = max(0.0, sleepUntil - now) + random.uniform(0, 0.1)
            Log(
                f"rate-limit: waiting {delay:.2f}s (reqs={reqs}/30, tokens={tokens}/8000, need={neededTokens})"
            )
            time.sleep(delay)

    def Record(self, usedTokens: int) -> None:
        now = time.time()
        self.requestTimes.append(now)
        self.tokenEvents.append((now, max(0, usedTokens)))


def Main() -> None:
    apiKey = os.environ.get("GROQ_API_KEY")
    if not apiKey:
        print("GROQ_API_KEY is required in environment", file=sys.stderr)
        sys.exit(1)

    perCallDelaySeconds = PER_CALL_DELAY_SECONDS

    data = LoadJson(inputPath)
    summaries: Dict[str, str] = {}
    if os.path.exists(outputPath):
        try:
            existing = LoadJson(outputPath)
            if isinstance(existing, dict):
                for k, v in existing.items():
                    if isinstance(v, str):
                        summaries[k] = v
        except Exception:
            pass

    total = 0
    processed = 0
    skipped = 0
    processedTarget = 1028
    for _ in IterateHymns(data):
        total += 1

    limiter = RateLimiter(maxRequestsPerMinute=30, maxTokensPerMinute=8000)

    for hymnId, text in IterateHymns(data):
        if hymnId in summaries and summaries[hymnId]:
            skipped += 1
            processed += 1
            Log(f"skip: already summarized hymnId={hymnId}")
            continue

        Log(f"prepare: hymnId={hymnId} processed={processed}/{processedTarget}")
        Log(f"send: hymnId={hymnId}")
        summary, raw = SummarizeHymn(apiKey, text)
        summaries[hymnId] = summary
        usedTokens = 0
        try:
            usage = raw.get("usage")
            if isinstance(usage, dict):
                totalTokens = usage.get("total_tokens")
                if isinstance(totalTokens, int) and totalTokens > 0:
                    usedTokens = totalTokens
        except Exception:
            pass
        limiter.Record(usedTokens)
        processed += 1
        Log(f"done: hymnId={hymnId} usedTokens={usedTokens} summaryChars={len(summary)}")
        Log(f"post-request: sleeping {perCallDelaySeconds}s")
        time.sleep(perCallDelaySeconds)
        SaveJson(outputPath, summaries)    
    print(json.dumps({"total": total, "processed": processed, "skipped": skipped}, ensure_ascii=False))


if __name__ == "__main__":
    Main()


