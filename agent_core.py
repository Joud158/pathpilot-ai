"""PathPilot AI: fictional business agent with routing, native tools and reflection."""
import os, re, json, logging
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
SUMMARY = (ROOT / "me" / "business_summary.txt").read_text(encoding="utf-8")
PDF_CONTENT = "\n".join(page.extract_text() or "" for page in PdfReader(ROOT / "me" / "about_business.pdf").pages).strip()
if not PDF_CONTENT:
    raise ValueError("The business PDF must contain extractable text.")
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("pathpilot")
PROVIDER = os.getenv("AI_PROVIDER", "gemini").strip().lower()
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite") if PROVIDER == "gemini" else os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def create_client():
    """Use Google's documented OpenAI-compatible Gemini endpoint, or OpenAI."""
    if PROVIDER not in {"gemini", "openai"}:
        raise ValueError("AI_PROVIDER must be gemini or openai")
    key_name = "GEMINI_API_KEY" if PROVIDER == "gemini" else "OPENAI_API_KEY"
    key = os.getenv(key_name, "").strip()
    if not key or key == "replace_with_your_key":
        raise ValueError(f"Please configure {key_name} in your local .env or Spaces secrets, then restart the app.")
    if PROVIDER == "gemini":
        return OpenAI(api_key=key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/", timeout=60, max_retries=1)
    return OpenAI(api_key=key, timeout=60, max_retries=1)


def generation_options(max_tokens=None):
    # Thinking tokens share the completion budget. Give Gemini enough room for
    # reasoning and visible text, including the short router classification.
    options = {"reasoning_effort": "low"} if PROVIDER == "gemini" else {}
    if max_tokens is not None:
        options["max_tokens"] = max(2048, max_tokens) if PROVIDER == "gemini" else max_tokens
    return options

# PERSONA: who the agent is (identity and communication style).
PERSONA = "You are Nova, PathPilot AI's warm, concise, professional career-services concierge. Speak naturally and clearly."

# INSTRUCTIONS: operational rules, separate from persona.
INSTRUCTIONS = """You represent only the fictional PathPilot AI company.
Use the supplied official business profile as your ONLY factual source about the business.
Never invent prices, availability, policies, credentials, services, or guarantees.
When the profile does not answer a business question, call record_feedback with the exact unanswered question, then clearly explain that a human must confirm it.
When a customer expresses interest in follow-up, ask for missing name and email, and service/notes. Never invent missing fields. Call record_customer_interest only when the customer explicitly wants follow-up and provides a valid email and name.
Never say a lead or feedback was recorded unless the corresponding tool returned success.
Do not collect passwords, payment details, government IDs, or other sensitive information.
Do not claim to book, charge, email, or contact staff automatically. The assistant can only log records.
For general career advice, you may give broad educational guidance but clearly distinguish it from official business facts.
If user asks for a human, invite them to share name and email for follow-up. Keep responses concise and helpful."""
SYSTEM_PROMPT = f"PERSONA:\n{PERSONA}\n\nINSTRUCTIONS:\n{INSTRUCTIONS}\n\nOFFICIAL BUSINESS SUMMARY:\n{SUMMARY}\n\nOFFICIAL BUSINESS PDF CONTENT:\n{PDF_CONTENT}"

def append_jsonl(filename, payload):
    path = LOG_DIR / filename
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), **payload}, ensure_ascii=False) + "\n")
    LOGGER.info("Record appended to %s", path.name)

def record_customer_interest(email: str, name: str, message: str) -> dict:
    """Persist an opted-in customer lead. Schema: email/name/message strings -> status dict."""
    if not all(isinstance(value, str) for value in (email, name, message)):
        return {"status": "error", "reason": "Email, name and message must be strings"}
    email, name, message = email.strip(), name.strip(), message.strip()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or not name or not message:
        return {"status": "error", "reason": "A valid email, name and message are required"}
    append_jsonl("leads.jsonl", {"email": email, "name": name, "message": message})
    return {"status": "success", "detail": "Customer interest logged for staff review; no email has been sent"}

def record_feedback(question: str) -> dict:
    """Persist an unanswered question or feedback. Schema: question string -> status dict."""
    if not isinstance(question, str) or not question.strip():
        return {"status": "error", "reason": "Question must not be empty"}
    append_jsonl("feedback.jsonl", {"question": question.strip()})
    return {"status": "success", "detail": "Feedback or unanswered question logged for staff review"}

# MCP-style documentation: name, description, input JSON schema and returned status.
TOOLS = [
 {"type":"function","function":{"name":"record_customer_interest","description":"Log a customer who explicitly requested staff follow-up and supplied their own name, email, and notes. Returns success/error; does not send email.","parameters":{"type":"object","properties":{"email":{"type":"string","description":"Customer email"},"name":{"type":"string","description":"Customer full name"},"message":{"type":"string","description":"Service interest or customer notes"}},"required":["email","name","message"],"additionalProperties":False}}},
 {"type":"function","function":{"name":"record_feedback","description":"Log customer feedback or a question not answered by the official business profile. Returns success/error.","parameters":{"type":"object","properties":{"question":{"type":"string","description":"Exact unanswered question or customer feedback"}},"required":["question"],"additionalProperties":False}}}
]
TOOL_HANDLERS = {"record_customer_interest": record_customer_interest, "record_feedback": record_feedback}

def route_intent(message: str, client=None) -> str:
    """Small LLM classifier; deterministic heuristic fallback for outages/tests."""
    text = message.lower()
    if client is not None:
        try:
            response = client.chat.completions.create(model=MODEL, temperature=0, **generation_options(12),
                messages=[{"role":"system","content":"Classify the latest user message into exactly one label: GENERAL, LEAD, FEEDBACK. LEAD includes interest, booking inquiry, or giving contact details. FEEDBACK includes complaints, suggestions, and unknown/unanswered questions. Otherwise GENERAL. Output only the label."},{"role":"user","content":message}])
            label = (response.choices[0].message.content or "").strip().upper()
            if label in {"GENERAL", "LEAD", "FEEDBACK"}: return label
        except Exception as exc:
            LOGGER.warning("Router fallback: %s", exc)
    if any(x in text for x in ["complaint", "feedback", "suggest", "unanswered", "not listed", "refund", "cancel", "discount", "payment method"]): return "FEEDBACK"
    if any(x in text for x in ["interested", "sign up", "contact me", "reach out", "book", "my email", "my name", "get started"]) or re.search(r"[^\s@]+@[^\s@]+\.[^\s@]+", text): return "LEAD"
    return "GENERAL"

def reflect(draft: str, user_message: str, client, context=None) -> str:
    """Bonus: second pass checks and revises answer, with visible logs."""
    if os.getenv("ENABLE_REFLECTION", "true").lower() != "true": return draft
    try:
        check = client.chat.completions.create(model=MODEL, temperature=0, **generation_options(450),
            messages=[{"role":"system","content":"You are a quality reviewer. Return ONLY the corrected customer-facing answer. Preserve factual accuracy and actual tool outcomes from the conversation. If a tool succeeded, retain that confirmation and do not ask the customer to provide fields or consent already supplied. Use conversation history to resolve references such as 'that service'. Never invent tool success. Check unsupported business claims, privacy, and clear wording. Use the official profile and operational instructions."},{"role":"user","content":f"INSTRUCTIONS:\n{INSTRUCTIONS}\nPROFILE:\n{SUMMARY}\nPDF:\n{PDF_CONTENT}\nCONVERSATION AND TOOL RESULTS:\n{json.dumps(context or [], ensure_ascii=False)}\nUSER:\n{user_message}\nDRAFT:\n{draft}"}])
        revised = (check.choices[0].message.content or "").strip() or draft
        append_jsonl("reflection.jsonl", {"user_message": user_message, "draft": draft, "revised": revised})
        LOGGER.info("REFLECTION DRAFT: %s", draft)
        LOGGER.info("REFLECTION REVISED: %s", revised)
        return revised
    except Exception as exc:
        LOGGER.warning("Reflection unavailable, retaining original: %s", exc)
        return draft

def respond(message: str, history=None, client=None) -> str:
    if not message or not message.strip(): return "Please enter a question."
    if client is None:
        try:
            client = create_client()
        except ValueError as exc:
            return str(exc)
    intent = route_intent(message, client)
    LOGGER.info("ROUTER: %s", intent)
    prior = []
    for turn in (history or [])[-12:]:
        if isinstance(turn, dict) and turn.get("role") in ("user", "assistant") and isinstance(turn.get("content"), str):
            prior.append({"role": turn["role"], "content": turn["content"]})
        elif isinstance(turn, (list, tuple)) and len(turn) == 2:
            prior.extend([{"role":"user","content":str(turn[0])},{"role":"assistant","content":str(turn[1])}])
    route_rule = {"GENERAL":"Answer from business knowledge; log unknown business questions.","LEAD":"Collect name/email/notes before calling lead tool; never invent missing details.","FEEDBACK":"Log explicit feedback or unknown business questions using feedback tool."}[intent]
    messages = [{"role":"system","content":SYSTEM_PROMPT + f"\n\nROUTER INTENT: {intent}. ROUTE HANDLING: {route_rule}"}, *prior, {"role":"user","content":message}]
    try:
        for _ in range(5):
            response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS, tool_choice="auto", temperature=0.2, **generation_options())
            choice = response.choices[0].message
            messages.append(choice.model_dump(exclude_none=True))
            if not choice.tool_calls:
                return reflect(choice.content or "I'm unable to answer that right now.", message, client, context=messages[1:])
            for call in choice.tool_calls:
                try:
                    arguments = json.loads(call.function.arguments)
                    if not isinstance(arguments, dict): raise ValueError("Expected JSON object")
                    handler = TOOL_HANDLERS.get(call.function.name)
                    result = handler(**arguments) if handler else {"status":"error","reason":"Unknown tool"}
                except Exception as exc:
                    result = {"status":"error","reason":str(exc)}
                LOGGER.info("TOOL %s -> %s", call.function.name, result)
                messages.append({"role":"tool","tool_call_id":call.id,"content":json.dumps(result)})
        return "I couldn't finish processing that request. Please try again."
    except Exception as exc:
        LOGGER.exception("Assistant request failed")
        status = getattr(exc, "status_code", None)
        if status == 503:
            return "The AI service is busy due to high demand. Please wait a moment and try again."
        if status == 429:
            return "The AI service request limit has been reached. Please check your quota in your provider dashboard and try again later."
        if status in (401, 403):
            return "The AI service rejected access. Please check your API key and project permissions, then restart the app."
        if status == 404:
            return "The configured AI model is unavailable. Please check the model name in .env, then restart the app."
        return "The assistant is temporarily unavailable. Please try again shortly."
