/** Parse display text without coupling paper orders to simplified Chinese. */
export function parseTradingRecommendation(recommendation: string, traderPlan = '') {
  const text = recommendation.replace(/買/g, '买').replace(/賣/g, '卖')
  const finalLines = [...text.matchAll(/(?:最[终終]交易建[议議]|最[终終]建[议議]|最[终終][决決]策)\s*[*：:\s]*(.+)/gi)]
  const actionText = finalLines.length ? finalLines[finalLines.length - 1][1] : text
  const matches = [...actionText.matchAll(/买入|卖出|持有|\bBUY\b|\bSELL\b|\bHOLD\b/gi)]
  const actions = new Set(matches.map(match => {
    const value = match[0].toLowerCase()
    return value === '买入' || value === 'buy' ? 'buy' : value === '卖出' || value === 'sell' ? 'sell' : 'hold'
  }))
  if (actions.size !== 1 || actions.has('hold')) return null
  const action = [...actions][0] as 'buy' | 'sell'
  const priceMatch = `${recommendation}\n${traderPlan}`.match(
    /目[标標][价價][格位]?\s*\**\s*[：:]\s*(?:HK\$|US\$|[¥￥$])?\s*(\d+(?:\.\d+)?)/i,
  )
  return { action, targetPrice: priceMatch ? Number(priceMatch[1]) : null }
}
