/**
 * DeepSeek Chat Completions 客户端（浏览器直连，SSE 流式）。
 *
 * 说明：
 * - 模型固定为 deepseek-flash；"压缩历史" 使用 deepseek-chat。
 * - 深度思考 / 联网搜索 两个开关互相独立，且只由用户点击控制，
 *   代码中没有任何自动开启或自动关闭的路径。
 * - API Key 只从 localStorage 读取，绝不写死在任何源码里。
 */

const DEFAULT_BASE = 'https://api.deepseek.com';
const CHAT_PATH = '/chat/completions';

/** 允许在浏览器控制台覆盖网关地址（例如自建反代），不影响界面。 */
export function apiBase() {
  try {
    const custom = localStorage.getItem('ds.apiBase.v1');
    if (custom && /^https?:\/\//.test(custom)) return custom.replace(/\/+$/, '');
  } catch (e) {
    /* ignore */
  }
  return DEFAULT_BASE;
}

export const MODEL_CHAT = 'deepseek-flash';
export const MODEL_SUMMARY = 'deepseek-chat';

/**
 * 把两个开关映射到请求体。若你的网关使用别的字段名，只需改这一个函数。
 */
function applyToggles(body, toggles) {
  // 只在开启时附带参数，关闭即不发送（服务端默认关闭），两者互不影响。
  if (toggles.thinking) body.thinking = { type: 'enabled' };
  if (toggles.webSearch) body.web_search = { enable: true };
  return body;
}

function parseErrorMessage(status, text) {
  let detail = '';
  try {
    const json = JSON.parse(text);
    detail = (json.error && (json.error.message || json.error.type)) || json.message || '';
  } catch (e) {
    detail = String(text || '').slice(0, 300);
  }
  if (status === 401) return 'API Key 无效或已过期（401）。请到设置页检查密钥。';
  if (status === 402) return '账户余额不足（402）。';
  if (status === 429) return '请求过于频繁或额度受限（429），请稍后再试。';
  if (status === 404) return '接口地址或模型不存在（404）。' + (detail ? ' ' + detail : '');
  return '请求失败（' + status + '）' + (detail ? '：' + detail : '');
}

/**
 * 流式对话
 * @returns {Promise<{content:string, reasoning:string, usage:object|null}>}
 */
export async function streamChat(options) {
  const { apiKey, messages, temperature, topP, thinking, webSearch, signal, onDelta, onReasoning, onUsage } = options;
  if (!apiKey) throw new Error('缺少 API Key，请先在设置页保存密钥。');

  const body = applyToggles(
    {
      model: MODEL_CHAT,
      messages,
      temperature,
      top_p: topP,
      stream: true,
      stream_options: { include_usage: true },
    },
    { thinking, webSearch }
  );

  const res = await fetch(apiBase() + CHAT_PATH, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: 'Bearer ' + apiKey,
    },
    body: JSON.stringify(body),
    signal,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(parseErrorMessage(res.status, text));
  }
  if (!res.body) throw new Error('当前浏览器不支持流式响应。');

  const reader = res.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let content = '';
  let reasoning = '';
  let usage = null;

  const handleLine = (line) => {
    if (!line.startsWith('data:')) return;
    const payload = line.slice(5).trim();
    if (!payload || payload === '[DONE]') return;
    let json;
    try {
      json = JSON.parse(payload);
    } catch (e) {
      return;
    }
    if (json.usage) {
      usage = {
        promptTokens: json.usage.prompt_tokens || 0,
        completionTokens: json.usage.completion_tokens || 0,
        cacheHitTokens: json.usage.prompt_cache_hit_tokens || 0,
      };
      if (onUsage) onUsage(usage);
    }
    const choice = json.choices && json.choices[0];
    if (!choice) return;
    const delta = choice.delta || {};
    if (delta.reasoning_content) {
      reasoning += delta.reasoning_content;
      if (onReasoning) onReasoning(delta.reasoning_content, reasoning);
    }
    if (delta.content) {
      content += delta.content;
      if (onDelta) onDelta(delta.content, content);
    }
  };

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buffer.indexOf('\n')) >= 0) {
      const line = buffer.slice(0, idx).replace(/\r$/, '');
      buffer = buffer.slice(idx + 1);
      handleLine(line);
    }
  }
  if (buffer.trim()) handleLine(buffer.trim());

  if (!content.trim()) {
    throw new Error('模型没有返回内容，请重试或检查开关设置。');
  }
  return { content, reasoning, usage };
}

/**
 * 手动压缩历史：调用 deepseek-chat 把历史压成 200~300 字摘要。
 * 仅在用户点击"压缩历史"时调用，没有任何自动触发路径。
 */
export async function summarizeHistory(options) {
  const { apiKey, transcript, signal } = options;
  if (!apiKey) throw new Error('缺少 API Key，请先在设置页保存密钥。');

  const body = {
    model: MODEL_SUMMARY,
    messages: [
      {
        role: 'system',
        content:
          '你是对话摘要助手。请把用户提供的对话记录压缩成 200~300 字的中文摘要，' +
          '保留人物关系、称呼、关键事实、已确认的设定、未完成的事项和当前话题走向。' +
          '只输出摘要正文，不要加标题、列表或任何解释。',
      },
      { role: 'user', content: transcript },
    ],
    temperature: 0.3,
    stream: false,
  };

  const res = await fetch(apiBase() + CHAT_PATH, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + apiKey },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(parseErrorMessage(res.status, text));
  }
  const json = await res.json();
  const text = json.choices && json.choices[0] && json.choices[0].message && json.choices[0].message.content;
  if (!text || !text.trim()) throw new Error('摘要生成失败，模型返回为空。');
  return { text: text.trim(), usage: json.usage || null };
}
