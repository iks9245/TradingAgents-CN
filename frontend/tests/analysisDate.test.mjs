import { test } from 'node:test'
import assert from 'node:assert/strict'
import { formatLocalDate } from '../src/utils/datetime.ts'

test('date picker preserves the selected calendar day in UTC+8 and UTC-8', () => {
  const original = process.env.TZ
  try {
    for (const timezone of ['Asia/Taipei', 'America/Los_Angeles', 'UTC']) {
      process.env.TZ = timezone
      assert.equal(formatLocalDate(new Date(2025, 11, 5)), '2025-12-05')
      assert.equal(formatLocalDate(new Date(2026, 0, 1)), '2026-01-01')
    }
    assert.throws(() => formatLocalDate(new Date('invalid')))
  } finally {
    if (original === undefined) delete process.env.TZ
    else process.env.TZ = original
  }
})
