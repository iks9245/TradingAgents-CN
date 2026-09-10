from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.services.foreign_stock_service import ForeignStockService


@pytest.mark.asyncio
@pytest.mark.parametrize("market", ["US", "HK"])
async def test_default_priority_does_not_filter_out_yahoo(market):
    service = ForeignStockService.__new__(ForeignStockService)
    service.db = None
    assert (await service._get_source_priority(market))[0] == "yahoo_finance"


@pytest.mark.asyncio
async def test_legacy_yfinance_grouping_is_normalized_and_deduplicated():
    cursor = Mock()
    cursor.sort.return_value = cursor
    cursor.to_list = AsyncMock(return_value=[
        {"data_source_name": "yfinance"}, {"data_source_name": "yahoo_finance"},
        {"data_source_name": "finnhub"},
    ])
    service = ForeignStockService.__new__(ForeignStockService)
    service.db = SimpleNamespace(datasource_groupings=SimpleNamespace(find=Mock(return_value=cursor)))
    assert await service._get_source_priority("US") == ["yahoo_finance", "finnhub"]
