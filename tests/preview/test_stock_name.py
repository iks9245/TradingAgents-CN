from unittest.mock import Mock

import pytest


@pytest.mark.parametrize('symbol', ['AAPL', '0700.HK', '00700'])
def test_foreign_task_creation_does_not_call_china_data_sources(monkeypatch, symbol):
    import app.services.simple_analysis_service as module
    helper = Mock(side_effect=AssertionError('Foreign symbol sent to Chinese provider'))
    monkeypatch.setattr(module, '_get_stock_info_safe', helper)
    service = module.SimpleAnalysisService.__new__(module.SimpleAnalysisService)
    service._stock_name_cache = {}
    assert service._resolve_stock_name(symbol) == symbol
    helper.assert_not_called()


def test_china_stock_names_still_use_provider_and_cache(monkeypatch):
    import app.services.simple_analysis_service as module
    helper = Mock(return_value={'name': '測試公司'})
    monkeypatch.setattr(module, '_get_stock_info_safe', helper)
    service = module.SimpleAnalysisService.__new__(module.SimpleAnalysisService)
    service._stock_name_cache = {}
    assert service._resolve_stock_name('600000') == '測試公司'
    assert service._resolve_stock_name('600000') == '測試公司'
    helper.assert_called_once_with('600000')
