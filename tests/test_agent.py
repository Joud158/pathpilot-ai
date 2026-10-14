import json
import agent_core as a
from types import SimpleNamespace
import pytest


class FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []

    def model_dump(self, **kwargs):
        result = {"role": "assistant", "content": self.content}
        if self.tool_calls:
            result["tool_calls"] = [
                {"id": c.id, "type": "function", "function": vars(c.function)}
                for c in self.tool_calls
            ]
        return result


class FakeClient:
    """Scripted model replies exercise the actual respond/tool loop without API costs."""
    def __init__(self, *messages):
        self.messages = iter(messages)
        self.requests = []
        self.chat = SimpleNamespace(completions=self)

    def create(self, **kwargs):
        self.requests.append({**kwargs, "messages": list(kwargs["messages"])})
        return SimpleNamespace(choices=[SimpleNamespace(message=next(self.messages))])


def tool_message(name, arguments):
    return FakeMessage(tool_calls=[SimpleNamespace(
        id="call_demo", function=SimpleNamespace(name=name, arguments=arguments)
    )])

def test_router_heuristics():
    assert a.route_intent("What are your prices?") == "GENERAL"
    assert a.route_intent("I am interested in a mock interview") == "LEAD"
    assert a.route_intent("I have feedback about the service") == "FEEDBACK"

def test_lead_and_feedback(tmp_path, monkeypatch):
    monkeypatch.setattr(a, "LOG_DIR", tmp_path)
    assert a.record_customer_interest("bad", "A", "mock interview")["status"] == "error"
    assert a.record_customer_interest("a@example.com", "A", "mock interview")["status"] == "success"
    assert json.loads((tmp_path / "leads.jsonl").read_text().splitlines()[0])["name"] == "A"
    assert a.record_feedback("Do you offer refunds?")["status"] == "success"
    assert "refunds" in (tmp_path / "feedback.jsonl").read_text()

def test_schema():
    assert len(a.TOOLS) == 2
    assert {t["function"]["name"] for t in a.TOOLS} == set(a.TOOL_HANDLERS)
    assert "PERSONA:" in a.SYSTEM_PROMPT and "INSTRUCTIONS:" in a.SYSTEM_PROMPT


def test_pdf_is_in_prompt():
    assert "PathPilot AI" in a.PDF_CONTENT
    assert a.PDF_CONTENT in a.SYSTEM_PROMPT
    assert a.SUMMARY in a.SYSTEM_PROMPT


@pytest.mark.parametrize("name,arguments,filename,intent", [
    ("record_customer_interest", {"email": "alex@example.com", "name": "Alex", "message": "mock interview"}, "leads.jsonl", "LEAD"),
    ("record_feedback", {"question": "Do you offer refunds?"}, "feedback.jsonl", "FEEDBACK"),
])
def test_model_requested_tools_and_history(tmp_path, monkeypatch, name, arguments, filename, intent):
    monkeypatch.setattr(a, "LOG_DIR", tmp_path)
    monkeypatch.setenv("ENABLE_REFLECTION", "false")
    client = FakeClient(FakeMessage(intent), tool_message(name, json.dumps(arguments)), FakeMessage("Successfully logged."))
    history = [{"role": "user", "content": "I want a mock interview."}, {"role": "assistant", "content": "Please provide your name and email."}]
    assert a.respond("Please follow up: Alex, alex@example.com", history, client) == "Successfully logged."
    assert json.loads((tmp_path / filename).read_text())[next(iter(arguments))] == next(iter(arguments.values()))
    assert history[0] in client.requests[1]["messages"]
    assert client.requests[1]["tools"] == a.TOOLS
    outcome = client.requests[2]["messages"][-1]
    assert outcome["role"] == "tool" and outcome["tool_call_id"] == "call_demo"
    assert json.loads(outcome["content"])["status"] == "success"


def test_malformed_tool_arguments_return_error(tmp_path, monkeypatch):
    monkeypatch.setattr(a, "LOG_DIR", tmp_path)
    monkeypatch.setenv("ENABLE_REFLECTION", "false")
    client = FakeClient(FakeMessage("LEAD"), tool_message("record_customer_interest", "not json"), FakeMessage("Please provide valid contact details."))
    assert "valid contact" in a.respond("Please contact me", client=client)
    assert json.loads(client.requests[-1]["messages"][-1]["content"])["status"] == "error"
    assert not (tmp_path / "leads.jsonl").exists()


def test_reflection_records_revision(tmp_path, monkeypatch):
    monkeypatch.setattr(a, "LOG_DIR", tmp_path)
    monkeypatch.setenv("ENABLE_REFLECTION", "true")
    client = FakeClient(FakeMessage("GENERAL"), FakeMessage("The bundle costs $199."), FakeMessage("The bundle costs $149."))
    assert a.respond("How much is the bundle?", client=client) == "The bundle costs $149."
    log = json.loads((tmp_path / "reflection.jsonl").read_text())
    assert "$199" in log["draft"] and "$149" in log["revised"]


def test_router_fallback_on_outage():
    client = FakeClient()  # exhausted replies simulate a failed router call
    assert a.route_intent("alex@example.com", client) == "LEAD"
    assert a.route_intent("How long is the discovery call?") == "GENERAL"


def test_non_string_lead_fields():
    assert a.record_customer_interest(None, "Alex", "Interview")["status"] == "error"


def test_gemini_client_configuration(monkeypatch):
    monkeypatch.setattr(a, "PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-not-a-real-key")
    client = a.create_client()
    assert str(client.base_url) == "https://generativelanguage.googleapis.com/v1beta/openai/"
    assert a.generation_options(12)["max_tokens"] >= 2048
    client.close()


def test_missing_gemini_key(monkeypatch):
    monkeypatch.setattr(a, "PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert "configure GEMINI_API_KEY" in a.respond("What services do you offer?")


def test_openai_provider_configuration(monkeypatch):
    monkeypatch.setattr(a, "PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-not-a-real-key")
    client = a.create_client()
    assert str(client.base_url) == "https://api.openai.com/v1/"
    assert a.generation_options(12) == {"max_tokens": 12}
    client.close()
