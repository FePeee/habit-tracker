import re
import logging

from openai import AsyncOpenAI, APIStatusError

from config import OPENROUTER_API_KEY, OPENROUTER_HTTP_REFERER, OPENROUTER_APP_TITLE

logger = logging.getLogger(__name__)

TELEGRAM_FORMAT_INSTRUCTION = (
    "\n\nIMPORTANT formatting rules: "
    "Output will be shown in Telegram as plain text (no Markdown rendering). "
    "Do NOT use markdown tables (no | pipes), HTML tags like <br>, horizontal rules (---), "
    "or markdown headings (#, ##, ###, etc.). "
    "Use short sections with blank lines, emojis, bullet lines starting with - or numbered lists. "
    "Do not use **bold** or __italic__ syntax; write normal words and use emojis for emphasis. "
    "Keep it concise and readable on mobile."
)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY or "missing-key",
            default_headers={
                "HTTP-Referer": OPENROUTER_HTTP_REFERER,
                "X-OpenRouter-Title": OPENROUTER_APP_TITLE,
            },
        )
    return _client


def sanitize_for_telegram(text: str) -> str:
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*---+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"__([^_]+)__", r"\1", text)
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            cells = [c for c in cells if c and not re.match(r"^[-:]+$", c)]
            if cells:
                cleaned.append(" - ".join(cells))
        else:
            cleaned.append(line)
    out = "\n".join(cleaned)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


async def call_ai(prompt: str, *, max_tokens: int = 500, for_telegram: bool = True) -> str:
    if not OPENROUTER_API_KEY:
        return "AI is not configured. Please set OPENROUTER_API_KEY (https://openrouter.ai/keys)."

    full_prompt = prompt + TELEGRAM_FORMAT_INSTRUCTION if for_telegram else prompt

    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=max_tokens,
            timeout=90,
        )
        if not response.choices:
            logger.warning("OpenRouter returned no choices")
            return "AI couldn't generate a response. Please try again later."
        content = response.choices[0].message.content
        if not content or not content.strip():
            logger.warning("OpenRouter returned empty content")
            return "AI couldn't generate a response. Please try again later."
        if for_telegram:
            content = sanitize_for_telegram(content)
        if not content.strip():
            logger.warning("Sanitized AI response became empty")
            return "AI response could not be parsed. Please try again."
        return content
    except APIStatusError as e:
        if e.status_code == 401:
            return (
                "OpenRouter rejected the API key (401). Set a valid OPENROUTER_API_KEY "
                "and restart the backend."
            )
        logger.warning("OpenRouter API error: %s", e)
        return f"AI service error ({e.status_code}): {e}"
    except Exception as e:
        logger.exception("call_ai failed")
        return f"AI service error: {e}"
