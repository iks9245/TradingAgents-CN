import { test } from 'node:test'
import assert from 'node:assert/strict'
import { parseTradingRecommendation } from '../src/utils/tradingRecommendation.ts'

test('Traditional, simplified and English recommendations can become paper orders', () => {
  for (const word of ['買入', '买入', 'BUY']) {
    assert.deepEqual(parseTradingRecommendation(word, '目標價位: $125.50'), { action: 'buy', targetPrice: 125.5 })
  }
  for (const word of ['賣出', '卖出', 'sell']) {
    assert.equal(parseTradingRecommendation(word).action, 'sell')
  }
})

test('final recommendation wins over earlier debate; ambiguous/hold text cannot trade', () => {
  assert.equal(parseTradingRecommendation('曾考慮買入\n最終交易建議: **賣出**').action, 'sell')
  for (const word of ['買入/賣出', '持有', 'HOLD', 'shareholder', 'buyer', '']) {
    assert.equal(parseTradingRecommendation(word), null)
  }
})
