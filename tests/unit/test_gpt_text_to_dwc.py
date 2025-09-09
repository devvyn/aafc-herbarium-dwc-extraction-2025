from types import SimpleNamespace
import importlib


gpt_text_to_dwc = importlib.import_module("engines.gpt.text_to_dwc")


def test_replaces_field_placeholder(monkeypatch):
    captured = {}
    resp = SimpleNamespace(output_text="{}")

    def fake_create(**kwargs):
        captured["messages"] = kwargs.get("input")
        return resp

    fake_client = SimpleNamespace(responses=SimpleNamespace(create=fake_create))
    monkeypatch.setattr(gpt_text_to_dwc, "OpenAI", lambda: fake_client)
    monkeypatch.setattr(
        gpt_text_to_dwc,
        "load_messages",
        lambda task, prompt_dir=None: [{"role": "user", "content": "Ensure %FIELD%"}],
    )

    gpt_text_to_dwc.text_to_dwc("data", model="gpt-4", fields=["catalogNumber", "eventDate"])

    assert captured["messages"][0]["content"].startswith("Ensure catalogNumber, eventDate")
