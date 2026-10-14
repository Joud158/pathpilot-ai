# PathPilot AI — Agent-Powered Business Assistant

**EECE 503P/798S — C3 Introduction to Agents assignment**. Fictional business; all names, pricing, and policies are for demonstration only.

## Features
- Official business profile in `me/about_business.pdf` and `me/business_summary.txt`; both are read into the agent's system prompt.
- Separate `PERSONA` and `INSTRUCTIONS` in `agent_core.py` and displayed in notebook.
- Three-way intent router (GENERAL / LEAD / FEEDBACK), LLM classification with heuristic fallback.
- Two real model-requested function-calling tools with JSON schemas and persistent JSONL logs.
- Short-term conversation memory from Gradio history.
- Unknown-question logging, opt-in lead collection, validation, and safe failure behavior.
- Bonus reflection pass with draft/revised logs; Hugging Face Spaces-ready app.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Windows PowerShell: Copy-Item .env.example .env
# Edit .env and enter your real GEMINI_API_KEY; never commit .env
python -m pytest -q tests
python app.py
```
Open the local Gradio URL printed in your terminal. For the notebook, launch Jupyter from the project root and open `business_agent.ipynb`.

## Hugging Face Spaces (bonus)
1. Create a **Gradio** Space with Python SDK.
2. Upload the repository contents, including `app.py`, `agent_core.py`, `requirements.txt`, and `me/`.
3. In Space **Settings → Variables and secrets**, add `GEMINI_API_KEY` as a **secret**. Set `AI_PROVIDER=gemini` and optionally `GEMINI_MODEL` and `ENABLE_REFLECTION` as variables.
4. The Space runs `app.py`. Test all three routes and reflection. Note that local JSONL files on Spaces may be ephemeral across restarts; use a persistent storage service for production.
5. Add the Space URL and demonstration video URL to this README before submission.

## Demo script (record your own video)
1. Show `me/about_business.pdf`, `me/business_summary.txt`, persona/instructions, and tool schemas.
2. Ask **What services and prices do you offer?** (GENERAL).
3. Ask **I'm interested in a mock interview**; confirm the assistant asks for name/email (LEAD).
4. Provide a fictional name/email and explicit request to follow up; inspect `logs/leads.jsonl`.
5. Ask **Do you offer refunds?** (unanswered business question); inspect `logs/feedback.jsonl`.
6. Send **I have feedback: please add weekend appointments**; inspect feedback log.
7. Show `logs/reflection.jsonl` containing draft and revised replies.
8. Show the deployed Hugging Face Space and link to your GitHub repository.

## Notes
- This demo stores submitted names and emails in local JSONL. Do not use real personal data in public demonstrations.
- A tool call is executed only if the model requests it. Router classification alone never fabricates a tool call.
- Reflection is a quality check, not a formal guarantee; inspect output and logs in live demos.
- The `.env` file is excluded by `.gitignore`; `.env.example` is safe to commit.
- No live API calls are made by the included offline unit tests.


## Gemini setup

Gemini is now the default provider (`gemini-3.1-flash-lite`). Create your own key at https://aistudio.google.com/apikey and put it in `.env` as `GEMINI_API_KEY`. Keep the project on the Free Tier if you want free usage, subject to Google quota limits. Restart the app after changing `.env`.

The `openai` Python package remains in requirements because Google officially supports using it with the Gemini endpoint: https://ai.google.dev/gemini-api/docs/openai. Requests with `AI_PROVIDER=gemini` go to Google, not OpenAI. No OpenAI key or credits are needed. To switch back, set `AI_PROVIDER=openai` and configure `OPENAI_API_KEY` and `OPENAI_MODEL`.
