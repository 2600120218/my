/**
 * deepseek-flash 计费（价格写死在代码中，不从任何接口读取）
 *
 * 空闲时段（北京时间 00:30 - 08:30）：
 *   输入        $0.15 / 百万 tokens
 *   缓存命中输入 $0.0075 / 百万 tokens
 *   输出        $0.60 / 百万 tokens
 * 高峰时段（其余时间）：以上价格翻倍。
 * 展示前按汇率 7.2 折算为人民币，精确到分。
 */

export const PRICING = {
  currency: 'USD',
  perMillion: {
    input: 0.15,
    cacheInput: 0.0075,
    output: 0.6,
  },
  peakMultiplier: 2,
  fx: 7.2,
};

/** 空闲时段：北京时间 00:30 - 08:30 */
export function isOffPeak(date) {
  const d = date || new Date();
  const mins = d.getHours() * 60 + d.getMinutes();
  return mins >= 30 && mins < 8 * 60 + 30;
}

export function rateFor(kind, date) {
  const base = PRICING.perMillion[kind] || 0;
  return isOffPeak(date) ? base : base * PRICING.peakMultiplier;
}

/**
 * 按一次请求返回的 usage 计算美元费用。
 * usage 字段兼容 OpenAI 风格：prompt_tokens / completion_tokens / prompt_cache_hit_tokens
 */
export function computeUsd(usage, date) {
  const prompt = Number(usage.promptTokens || 0);
  const cacheHit = Math.min(Number(usage.cacheHitTokens || 0), prompt);
  const normalIn = Math.max(prompt - cacheHit, 0);
  const out = Number(usage.completionTokens || 0);
  const usd =
    (normalIn / 1e6) * rateFor('input', date) +
    (cacheHit / 1e6) * rateFor('cacheInput', date) +
    (out / 1e6) * rateFor('output', date);
  return usd;
}

export function usdToCny(usd) {
  return Number(usd || 0) * PRICING.fx;
}

/** "精确到分" */
export function fmtCny(usd) {
  const cny = usdToCny(usd);
  if (cny > 0 && cny < 0.01) return '¥0.01';
  return '¥' + cny.toFixed(2);
}

export function fmtUsd(usd) {
  return '$' + Number(usd || 0).toFixed(4);
}

export function periodLabel(date) {
  return isOffPeak(date) ? '空闲时段（00:30-08:30，标准价）' : '高峰时段（价格翻倍）';
}
