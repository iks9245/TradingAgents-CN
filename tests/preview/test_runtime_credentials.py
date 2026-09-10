from unittest.mock import Mock

from tradingagents.dataflows import interface


def test_graph_config_does_not_persist_runtime_keys(monkeypatch):
    save = Mock()
    monkeypatch.setattr(interface.config_manager, "save_settings", save)
    config = {
        "quick_api_key": "fixture-quick", "deep_api_key": "fixture-deep", "api_key": "fixture-key",
        "quick_think_llm": "preview-model", "quick_model_config": {"max_tokens": 8192},
    }
    interface.set_config(config)
    assert save.call_args.args[0] == {
        "quick_think_llm": "preview-model", "quick_model_config": {"max_tokens": 8192},
    }
    assert config["quick_api_key"] == "fixture-quick"
