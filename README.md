# PathPilot AI

### Agent-Powered Career Services Assistant

**Author:** Joud Senan  
**Course:** EECE 503P/798S ? Agentic Systems  
**Assignment:** C3 ? Introduction to Agents

PathPilot AI is a conversational assistant for a fictional career-development studio. Its concierge, **Nova**, answers business questions, collects customer leads, and records feedback through model-requested tools. The project demonstrates intent routing, short-term conversation memory, tool execution, and an optional reflection pass in a Gradio interface.

[View the GitHub repository](https://github.com/Joud158/pathpilot-ai)

## Business Overview

PathPilot helps students and early-career professionals prepare for job applications through targeted feedback and interview practice.

| Service | Price (USD) | Includes |
| --- | --- | --- |
| Resume Review | $39 | Written feedback within three business days |
| Mock Interview | $69 | A 45-minute remote session and a written action plan |
| Career Launch Bundle | $149 | One resume review, two mock interviews, and a personalized action plan |
| Discovery Call | Free | A 15-minute introductory call, subject to availability |

All business details, staff profiles, prices, and policies are fictional. The PDF and text summary in `me/` provide the official knowledge used by the assistant.

## Features

- **Business-grounded answers:** both the PDF and text summary are included in the system prompt.
- **Separate persona and instructions:** Nova's identity and tone are distinct from operational rules.
- **Three-way intent routing:** messages are classified as `GENERAL`, `LEAD`, or `FEEDBACK`, with a heuristic fallback when the classifier is unavailable.
- **Model-requested tools:** customer interest and feedback are written to local JSONL files after actual function calls.
- **Conversation memory:** recent chat history lets Nova resolve references such as ?that service.?
- **Lead validation:** name, valid email, and notes are required before a lead can be recorded.
- **Reflection:** a second model pass reviews the draft using business knowledge, conversation context, and tool results; draft and revised replies are logged.
- **Gradio interface:** the same agent powers the local app and Jupyter notebook.

## How It Works

1. The router classifies the incoming message.
2. The model receives the business knowledge, persona, instructions, route guidance, recent conversation, and tool schemas.
3. Requested tools are executed, and their results are returned to the model.
4. The optional reflection pass reviews the draft before the final reply is displayed.

Routing guides the model; it does not execute or fabricate tool calls.

### Tool Definitions

| Tool | Parameters | Purpose | Output |
| --- | --- | --- | --- |
| `record_customer_interest` | `email`, `name`, `message` | Record an explicitly requested follow-up with valid customer details | Success with `detail`, or error with `reason` |
| `record_feedback` | `question` | Record feedback or an unanswered business question | Success with `detail`, or error with `reason` |

Input JSON schemas are defined in `agent_core.py` and displayed in the notebook.

## Project Structure

```text
pathpilot-ai/
??? me/
?   ??? about_business.pdf
?   ??? business_summary.txt
??? tests/
?   ??? test_agent.py
??? agent_core.py
??? app.py
??? business_agent.ipynb
??? requirements.txt
??? .env.example
??? .gitignore
??? README.md
```

The local `.env`, generated `logs/`, virtual environment, and temporary test files are excluded from version control.

## Run Locally

Use Python 3.11 and a Gemini API key. Run these commands in PowerShell:

```powershell
git clone https://github.com/Joud158/pathpilot-ai.git
cd pathpilot-ai
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and supply your own key:

```dotenv
AI_PROVIDER=gemini
GEMINI_API_KEY=your_actual_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
ENABLE_REFLECTION=true
```

Create your key in [Google AI Studio](https://aistudio.google.com/apikey). Keep the actual key in `.env`; never commit it. Restart the app or notebook kernel after changing configuration.

Start the chatbot:

```powershell
.\.venv\Scripts\python.exe app.py
```

Open the local URL printed in the terminal, usually **http://127.0.0.1:7860**. Press **Ctrl+C** to stop the server.

### Notebook

Open `business_agent.ipynb` in VS Code or Jupyter with the project environment selected as the kernel. Install `ipykernel` in that environment if needed:

```powershell
.\.venv\Scripts\python.exe -m pip install ipykernel
```

Run the cells from the top to inspect the documents, persona, instructions, router, schemas, live interaction, and tests. Stop any existing terminal app before launching the notebook's Gradio interface.

### API Provider

Gemini is the default. The `openai` Python package connects to Google's [OpenAI-compatible Gemini endpoint](https://ai.google.dev/gemini-api/docs/openai); Gemini requests are sent to Google and require no OpenAI key.

An alternative OpenAI configuration is available through `AI_PROVIDER=openai`, `OPENAI_API_KEY`, and `OPENAI_MODEL`. Select a model available to your account.

## Testing and Demonstration

Run the offline tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
```

The test suite covers routing, document grounding, tool schemas, validation, conversation history, tool-result handling, malformed arguments, reflection logging, and provider configuration. **13 tests passed during the local audit.** These tests use scripted responses and do not make live API calls.

Use the following sequence for a live demonstration:

| Step | Message | Expected behavior |
| --- | --- | --- |
| General question | ?What services and prices do you offer?? | Answers using the business documents |
| Lead inquiry | ?I'm interested in a mock interview. Please have your team follow up.? | Requests missing name and email |
| Contact details | ?My name is Alex Lee and my email is alex@example.com. Please contact me about that service.? | Remembers the service and calls the lead tool |
| Unknown question | ?Do you offer refunds?? | Logs the question and explains that staff must confirm the policy |
| Feedback | ?I have feedback: please add weekend appointments.? | Calls the feedback tool |

Inspect the terminal for route labels and successful tool results. Generated files are:

| File | Contents |
| --- | --- |
| `logs/leads.jsonl` | Timestamp, name, email, and service notes |
| `logs/feedback.jsonl` | Timestamp and feedback or unanswered question |
| `logs/reflection.jsonl` | Timestamp, user message, original draft, and revised reply |

A revision may match its draft when no correction is needed. Use fictional contact details for demonstrations and inspect saved notebook outputs before publishing.

## Limitations

- The assistant records requests; it does not book appointments, send emails, charge customers, or guarantee employment.
- API outages and quota limits can interrupt replies. If reflection fails, the original draft is retained.
- Reflection is a model-based review, not a guarantee of correctness.
- JSONL records are stored locally. They are demonstration storage rather than a production customer-management system.

## Submission

- **Repository:** [Joud158/pathpilot-ai](https://github.com/Joud158/pathpilot-ai)
- **Demonstration video:** pending recording and link.
- **Reflection bonus:** implemented, with successful live draft/revised evidence; some calls were interrupted by provider outages.
- **Hugging Face hosting bonus:** not completed. Local Gradio demonstration is available.
