"""Real API + MongoDB + Redis, with an offline LLM and synthetic market data.

Requires PREVIEW_INTEGRATION=1 and isolated local databases (see preview guide).
"""

import os
import secrets
import uuid

import httpx
import pytest


@pytest.mark.asyncio
@pytest.mark.skipif(os.getenv("PREVIEW_INTEGRATION") != "1", reason="Requires isolated preview databases")
async def test_login_analysis_report_export_paper_trade(monkeypatch, tmp_path):
    from app.core.config import settings
    from app.core.database import init_database, close_database, get_mongo_db
    from app.main import app
    from app.models.user import UserCreate
    from app.services.user_service import user_service
    from app.services.simple_analysis_service import get_simple_analysis_service
    from tests.preview.offline import install_offline_boundaries

    assert settings.MONGODB_HOST in ("localhost", "127.0.0.1")
    assert settings.MONGO_DB.startswith("tradingagents_preview_")
    assert settings.REDIS_HOST in ("localhost", "127.0.0.1")
    monkeypatch.setenv("TRADINGAGENTS_RESULTS_DIR", str(tmp_path))
    await init_database()
    service = get_simple_analysis_service()
    install_offline_boundaries(monkeypatch, service)
    username = "preview_" + uuid.uuid4().hex[:12]
    password = secrets.token_urlsafe(24)
    user = await user_service.create_user(UserCreate(
        username=username, email=f"{username}@example.test", password=password,
    ))
    assert user is not None
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://preview.test") as client:
            assert (await client.get("/api/paper/account")).status_code == 401
            bad_login = await client.post("/api/auth/login", json={"username": username, "password": "wrong"})
            assert bad_login.status_code == 401
            login = await client.post("/api/auth/login", json={"username": username, "password": password})
            assert login.status_code == 200, login.text
            client.headers["Authorization"] = "Bearer " + login.json()["data"]["access_token"]

            submit = await client.post("/api/analysis/single", json={
                "symbol": "AAPL", "stock_code": "AAPL", "parameters": {
                    "market_type": "美股", "selected_analysts": ["market"], "research_depth": "快速",
                },
            })
            assert submit.status_code == 200, submit.text
            task_id = submit.json()["data"]["task_id"]
            status = await client.get(f"/api/analysis/tasks/{task_id}/status")
            assert status.status_code == 200, status.text
            assert status.json()["data"]["status"] == "completed", status.text
            persisted = await get_mongo_db().analysis_tasks.find_one({"task_id": task_id})
            assert persisted["status"] == "completed"

            detail = await client.get(f"/api/reports/{task_id}/detail")
            assert detail.status_code == 200, detail.text
            assert "繁體預覽驗收" in detail.text
            assert "final_trade_decision" in detail.text
            assert detail.json()["data"]["analysis_date"] == "2025-12-05"
            for format in ("markdown", "json"):
                exported = await client.get(f"/api/reports/{task_id}/download", params={"format": format})
                assert exported.status_code == 200, exported.text
                assert "attachment" in exported.headers["content-disposition"]
                assert "繁體預覽驗收" in exported.text
            assert list(tmp_path.rglob("*.md")), "Modular reports were not saved"

            account = await client.get("/api/paper/account")
            assert account.status_code == 200, account.text
            before = await get_mongo_db().paper_accounts.find_one({"user_id": str(user.id)})
            order = await client.post("/api/paper/order", json={
                "code": "AAPL", "side": "buy", "quantity": 2, "analysis_id": task_id,
            })
            assert order.status_code == 200, order.text
            assert order.json()["data"]["order"]["status"] == "filled"
            after = await get_mongo_db().paper_accounts.find_one({"user_id": str(user.id)})
            assert before["cash"]["USD"] - after["cash"]["USD"] == 200
            assert before["cash"]["CNY"] == after["cash"]["CNY"]
            positions = await client.get("/api/paper/positions")
            assert positions.status_code == 200, positions.text
            position = await get_mongo_db().paper_positions.find_one({"user_id": str(user.id), "code": "AAPL"})
            assert position["quantity"] == 2
            orders = await client.get("/api/paper/orders")
            assert orders.status_code == 200 and task_id in orders.text
            sale = await client.post("/api/paper/order", json={"code": "AAPL", "side": "sell", "quantity": 2})
            assert sale.status_code == 200, sale.text
            oversell = await client.post("/api/paper/order", json={"code": "AAPL", "side": "sell", "quantity": 1})
            assert oversell.status_code == 400
    finally:
        await close_database()
        user_service.close()
        user_service.client = None
