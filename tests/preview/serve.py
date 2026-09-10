"""Local-only acceptance server. Run explicitly; never used in production or CI.

PREVIEW_OPENCLAW_CONFIG opts into the user's configured MiMo service. Without
it, the agent graph runs with the offline external boundaries in offline.py.
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path


def build_app():
    # Set environment before importing the production settings singleton.
    os.environ.setdefault("MONGODB_HOST", "127.0.0.1")
    os.environ.setdefault("MONGODB_PORT", "27028")
    os.environ.setdefault("MONGODB_DATABASE", "tradingagents_preview_browser")
    os.environ.setdefault("REDIS_HOST", "127.0.0.1")
    os.environ.setdefault("REDIS_PORT", "6388")
    os.environ.setdefault("REDIS_ENABLED", "true")
    os.environ.setdefault("JWT_SECRET", "preview-local-only-not-for-production")
    os.environ.setdefault("TRADINGAGENTS_RESULTS_DIR", str(Path("output/playwright/reports").resolve()))
    assert os.environ["MONGODB_HOST"] in ("127.0.0.1", "localhost")
    assert os.environ["REDIS_HOST"] in ("127.0.0.1", "localhost")
    assert os.environ["MONGODB_DATABASE"].startswith("tradingagents_preview_")
    # Legacy core storage uses different names from the web API settings.
    os.environ["MONGODB_CONNECTION_STRING"] = f"mongodb://{os.environ['MONGODB_HOST']}:{os.environ['MONGODB_PORT']}"
    os.environ["MONGODB_DATABASE_NAME"] = os.environ["MONGODB_DATABASE"]

    live_config = os.environ.get("PREVIEW_OPENCLAW_CONFIG")
    base_url = "http://127.0.0.1/offline-fixture"
    if live_config:
        provider = json.loads(Path(live_config).read_text())["models"]["providers"]["xiaomi-coding"]
        base_url = provider["baseUrl"]
        key = provider["apiKey"]
        if not isinstance(key, str) or not key or key.startswith("${"):
            raise ValueError("OpenClaw MiMo credential must be resolved before running live acceptance")
        os.environ["OPENAI_API_KEY"] = key
        # Redact the exact credential even if a legacy log prints configuration.
        original_factory = logging.getLogRecordFactory()
        def redacted_record(*args, **kwargs):
            record = original_factory(*args, **kwargs)
            if key in record.getMessage():
                record.msg = record.getMessage().replace(key, "[REDACTED]")
                record.args = ()
            return record
        logging.setLogRecordFactory(redacted_record)

    from app.main import app
    from app.core.database import init_database, close_database, get_mongo_db
    from app.models.config import SystemConfig, LLMConfig, LLMProvider, DataSourceConfig
    from app.models.user import UserCreate
    from app.services.user_service import user_service
    from app.services.simple_analysis_service import get_simple_analysis_service

    @asynccontextmanager
    async def lifespan(_app):
        await init_database()
        db = get_mongo_db()
        model = LLMConfig(
            provider="openai", model_name="mimo-v2.5", model_display_name="MiMo v2.5",
            api_base=base_url, max_tokens=8192, timeout=180, retry_times=1,
            capability_level=4, features=["tool_calling"],
        )
        config = SystemConfig(
            config_name="preview", config_type="system",
            llm_configs=[model], default_llm="mimo-v2.5",
            data_source_configs=[DataSourceConfig(name="yfinance", type="yahoo_finance", market_categories=["us"])],
            default_data_source="yfinance",
            system_settings={"quick_analysis_model": "mimo-v2.5", "deep_analysis_model": "mimo-v2.5"},
        ).model_dump(by_alias=True)
        config.pop("_id", None)
        await db.system_configs.update_one({"config_name": config["config_name"]}, {"$set": config}, upsert=True)
        provider_doc = LLMProvider(name="openai", display_name="MiMo (OpenAI compatible)", default_base_url=base_url).model_dump(by_alias=True)
        provider_doc.pop("_id", None)
        await db.llm_providers.update_one({"name": "openai"}, {"$set": provider_doc}, upsert=True)
        username = "preview-user"
        if not await user_service.get_user_by_username(username):
            await user_service.create_user(UserCreate(username=username, email="preview@example.test", password="Preview-Local-Only-2026"))
        user_service.users_collection.update_one({"username": username}, {"$set": {
            "preferences.default_market": "美股", "preferences.default_depth": "1",
            "preferences.default_analysts": ["市场分析师"],
        }})
        patch = None
        if not live_config:
            from pytest import MonkeyPatch
            from tests.preview.offline import install_offline_boundaries
            patch = MonkeyPatch()
            install_offline_boundaries(patch, get_simple_analysis_service())
        print(f"Preview ready: {'LIVE MiMo + live market data' if live_config else 'OFFLINE fixtures'}", flush=True)
        try:
            yield
        finally:
            if patch:
                patch.undo()
            await close_database()
            user_service.close()
            user_service.client = None

    # Deliberately omit production scheduled synchronization jobs in this harness.
    app.router.lifespan_context = lifespan
    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(build_app(), host="127.0.0.1", port=8018)
