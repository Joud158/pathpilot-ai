# Assignment requirement audit

Audited against `C3 - Introduction to Agents.pdf` on October 14, 2026. The handout has no point breakdown, so a defensible numeric grade cannot be calculated. Code completion alone does not establish 100/100.

| Requirement | Implementation / evidence | Status |
| --- | --- | --- |
| Fictional identity, mission, services, team, value proposition | `me/about_business.pdf`, `me/business_summary.txt` | Complete |
| Separate labeled persona and instructions | `agent_core.py`, notebook section 3 | Complete |
| Three-intent router with appropriate handling | `route_intent`, route-specific instructions, notebook section 4 | Implemented; offline tested |
| Two tools with name, input schema, expected output | `TOOLS`, tool functions, notebook section 5 | Implemented; offline tested |
| Summary AND PDF used in system prompt | `SUMMARY`, extracted `PDF_CONTENT`, `SYSTEM_PROMPT` | Complete |
| API conversation, short-term history, tool-result messages | `respond` | Implemented; offline tested |
| Gradio ChatInterface | `app.py`, executable notebook launch cell | Implemented; local startup checked |
| API key in local `.env`, excluded from upload | `.env.example`, `.gitignore`, explicit project-local dotenv loading | User must configure real key |
| Runs successfully with actual model | Live notebook example and multi-turn demo | Pending real API-key run |
| GitHub repository submission | Upload project contents including notebook and `me/` | Pending |
| Video showcasing functionality | Recording script in README | Pending |
| Bonus reflection with draft/revised logs | `reflect`, notebook log inspection | Implemented; offline tested; real-model evidence pending |
| Bonus Hugging Face Space | Deployable `app.py` | Pending deployment |

## Finish before submitting

1. From the project folder, install `requirements.txt`, copy `.env.example` to `.env`, and set your own valid API key. Do not upload `.env`.
2. Run `python -m pytest -q tests`, then run the notebook's live examples and Gradio launch. Confirm actual lead, feedback, and reflection records. Offline tests simulate model responses and do not prove live model reliability.
3. Create a GitHub repository and upload this project's files, including hidden `.gitignore` and `.env.example`. Exclude personal logs, caches, and secrets.
4. Record the README demo script. Show all three routes, contact collection across turns, actual tool execution and log files, and reflection draft/revised replies. Add the video and repository URLs to the README.
5. For the hosting bonus, deploy to a Gradio Hugging Face Space, set `OPENAI_API_KEY` as a secret, test the hosted chatbot, and add the Space URL to the README.

Gemini support is configured as the default, with OpenAI available as an alternative. All 13 offline tests pass. No live API credentials, GitHub repository, demo video, or Space were available during the audit. Do not present scripted offline test outputs as real model evidence.
