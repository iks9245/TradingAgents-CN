from unittest.mock import MagicMock

from app.services.simple_analysis_service import (
    create_analysis_config, get_provider_and_url_by_model_sync,
)


def test_saved_model_limits_are_forwarded_without_credentials(monkeypatch):
    client = MagicMock()
    db = client.__getitem__.return_value
    configs = MagicMock()
    providers = MagicMock()
    db.system_configs = configs
    db.llm_providers = providers
    configs.find_one.return_value = {"llm_configs": [{
        "model_name": "preview-model", "provider": "openai",
        "api_base": "http://localhost/fixture", "api_key": "fixture-not-a-real-key",
        "max_tokens": 8192, "temperature": 0.0, "timeout": 180, "retry_times": 1,
    }]}
    providers.find_one.return_value = None
    monkeypatch.setattr("pymongo.MongoClient", lambda *a, **kw: client)
    info = get_provider_and_url_by_model_sync("preview-model")
    assert info["model_config"] == {
        "max_tokens": 8192, "temperature": 0.0, "timeout": 180, "retry_times": 1,
    }
    config = create_analysis_config(
        research_depth="快速", selected_analysts=["market"],
        quick_model="preview-model", deep_model="preview-model", llm_provider="openai",
        market_type="美股", quick_model_config=info["model_config"], deep_model_config=info["model_config"],
    )
    assert config["quick_model_config"]["max_tokens"] == 8192
    assert config["deep_model_config"]["temperature"] == 0.0
    assert "api_key" not in config["quick_model_config"]
