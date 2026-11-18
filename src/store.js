import { uid, b64encode, b64decode, dayKey } from './utils.js';
import { computeUsd } from './pricing.js';

const K = {
  threads: 'ds.threads.v1',
  settings: 'ds.settings.v1',
  keys: 'ds.keys.v1',
  cost: 'ds.cost.v1',
  ui: 'ds.ui.v1',
};

/** 系统提示词默认值：用户可在设置页随时修改；系统不会自动改写。 */
export const DEFAULT_SYSTEM_PROMPT = '你是一位乐于助人的 AI 助手。请用清晰、准确、有条理的中文回答用户的问题。';

export const DEFAULT_SETTINGS = {
  temperature: 0.85,
  topP: 0.95,
  systemPrompt: DEFAULT_SYSTEM_PROMPT,
  contextLimit: 20,
  pauseEvery25: true,
};

export const state = {
  threads: [],
  currentId: null,
  settings: { ...DEFAULT_SETTINGS },
  keys: [],
  activeKeyId: null,
  cost: freshCost(),
  ui: {
    sidebarOpen: false,
    costOpen: false,
    search: '',
    settingsOpen: false,
    editing: null,
    sending: false,
  },
};

function freshCost() {
  return { date: dayKey(), promptTokens: 0, cacheHitTokens: 0, completionTokens: 0, requests: 0, usd: 0 };
}

function read(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw);
  } catch (e) {
    return fallback;
  }
}

function write(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch (e) {
    console.warn('[store] 写入 localStorage 失败', e);
    return false;
  }
}

export function loadAll() {
  const threads = read(K.threads, []);
  // 结构兜底：任何一条脏数据都不应该让整个应用起不来
  state.threads = (Array.isArray(threads) ? threads : [])
    .filter((t) => t && t.id)
    .map((t) => ({
      id: t.id,
      title: typeof t.title === 'string' && t.title ? t.title : '新对话',
      createdAt: Number(t.createdAt) || Date.now(),
      updatedAt: Number(t.updatedAt) || Number(t.createdAt) || Date.now(),
      pinned: !!t.pinned,
      thinking: !!t.thinking,
      webSearch: !!t.webSearch,
      summary: t.summary && typeof t.summary.text === 'string' ? t.summary : null,
      roundsSinceConfirm: Number(t.roundsSinceConfirm) || 0,
      messages: (Array.isArray(t.messages) ? t.messages : [])
        .filter((m) => m && (m.role === 'user' || m.role === 'assistant'))
        .map((m) => ({
          id: m.id || uid(),
          role: m.role,
          content: typeof m.content === 'string' ? m.content : '',
          reasoning: typeof m.reasoning === 'string' ? m.reasoning : '',
          createdAt: Number(m.createdAt) || Date.now(),
        })),
    }));

  const settings = read(K.settings, {});
  state.settings = { ...DEFAULT_SETTINGS };
  for (const key of Object.keys(DEFAULT_SETTINGS)) {
    if (settings && settings[key] !== undefined && settings[key] !== null) state.settings[key] = settings[key];
  }
  // 数值范围保护（只在读取时兜底，不会因对话而改动）
  state.settings.temperature = clampNum(state.settings.temperature, 0, 2, DEFAULT_SETTINGS.temperature);
  state.settings.topP = clampNum(state.settings.topP, 0, 1, DEFAULT_SETTINGS.topP);
  state.settings.contextLimit = Math.round(clampNum(state.settings.contextLimit, 2, 100, DEFAULT_SETTINGS.contextLimit));

  const keys = read(K.keys, []);
  state.keys = Array.isArray(keys) ? keys.filter((k) => k && k.id && typeof k.value === 'string') : [];
  const savedActive = read('ds.activeKey.v1', null);
  state.activeKeyId = savedActive && state.keys.some((k) => k.id === savedActive) ? savedActive : state.keys[0] ? state.keys[0].id : null;

  const cost = read(K.cost, null);
  if (cost && cost.date === dayKey()) {
    const base = freshCost();
    base.promptTokens = Number(cost.promptTokens) || 0;
    base.completionTokens = Number(cost.completionTokens) || 0;
    base.cacheHitTokens = Number(cost.cacheHitTokens) || 0;
    base.requests = Number(cost.requests) || 0;
    base.usd = Number(cost.usd) || 0;
    state.cost = base;
  } else {
    state.cost = freshCost();
  }

  const ui = read(K.ui, {});
  if (ui && typeof ui === 'object') {
    state.ui.costOpen = !!ui.costOpen;
  }

  if (!state.threads.length) {
    const t = createThread(true);
    state.currentId = t.id;
  } else {
    const last = read('ds.currentId.v1', null);
    state.currentId = state.threads.some((t) => t.id === last) ? last : state.threads[0].id;
  }
}

function clampNum(v, min, max, fallback) {
  const n = Number(v);
  if (!isFinite(n)) return fallback;
  return Math.min(max, Math.max(min, n));
}

/* ----------------------------- 对话 ----------------------------- */

export function persistThreads() {
  write(K.threads, state.threads);
  write('ds.currentId.v1', state.currentId);
}

export function currentThread() {
  return state.threads.find((t) => t.id === state.currentId) || null;
}

export function createThread(silent) {
  const now = Date.now();
  const thread = {
    id: uid(),
    title: '新对话',
    createdAt: now,
    updatedAt: now,
    pinned: false,
    thinking: false,
    webSearch: false,
    messages: [],
    summary: null,
    roundsSinceConfirm: 0,
  };
  state.threads.unshift(thread);
  state.currentId = thread.id;
  if (!silent) persistThreads();
  return thread;
}

export function selectThread(id) {
  if (!state.threads.some((t) => t.id === id)) return;
  state.currentId = id;
  persistThreads();
}

export function deleteThread(id) {
  const idx = state.threads.findIndex((t) => t.id === id);
  if (idx < 0) return;
  state.threads.splice(idx, 1);
  if (state.currentId === id) {
    if (!state.threads.length) createThread(true);
    state.currentId = state.threads[0].id;
  }
  persistThreads();
}

export function togglePin(id) {
  const t = state.threads.find((x) => x.id === id);
  if (!t) return;
  t.pinned = !t.pinned;
  t.updatedAt = t.updatedAt || Date.now();
  persistThreads();
}

export function renameThread(id, title) {
  const t = state.threads.find((x) => x.id === id);
  if (!t) return;
  t.title = String(title || '').slice(0, 80) || '新对话';
  persistThreads();
}

export function touchThread(thread) {
  thread.updatedAt = Date.now();
  if (thread.title === '新对话') {
    const first = thread.messages.find((m) => m.role === 'user');
    if (first) thread.title = (first.content || '').replace(/\s+/g, ' ').slice(0, 24) || '新对话';
  }
  persistThreads();
}

export function addMessage(thread, msg) {
  const message = Object.assign(
    { id: uid(), createdAt: Date.now(), content: '', reasoning: '' },
    msg
  );
  thread.messages.push(message);
  touchThread(thread);
  return message;
}

export function updateMessage(thread, id, patch) {
  const msg = thread.messages.find((m) => m.id === id);
  if (!msg) return null;
  Object.assign(msg, patch);
  persistThreads();
  return msg;
}

/** 从 index 起（含）截断，用于撤回 / 编辑后重生成 */
export function truncateFrom(thread, index) {
  if (index < 0) return;
  thread.messages.splice(index);
  persistThreads();
}

/* ----------------------------- 设置 ----------------------------- */

export function persistSettings() {
  write(K.settings, state.settings);
}

export function setSetting(key, value) {
  state.settings[key] = value;
  persistSettings();
}

/* ----------------------------- 密钥 ----------------------------- */

export function persistKeys() {
  write(K.keys, state.keys);
  write('ds.activeKey.v1', state.activeKeyId);
}

export function addKey(name, rawValue) {
  const key = { id: uid(), name: String(name || '').trim() || '未命名密钥', value: b64encode(rawValue) };
  state.keys.push(key);
  if (!state.activeKeyId) state.activeKeyId = key.id;
  persistKeys();
  return key;
}

export function removeKey(id) {
  state.keys = state.keys.filter((k) => k.id !== id);
  if (state.activeKeyId === id) state.activeKeyId = state.keys[0] ? state.keys[0].id : null;
  persistKeys();
}

export function setActiveKey(id) {
  if (!state.keys.some((k) => k.id === id)) return;
  state.activeKeyId = id;
  persistKeys();
}

/**
 * 环境变量注入的密钥（仅本地 dev server 会注入，GitHub Pages 上永远为空）。
 * 由 scripts/serve.mjs 读取 process.env.DEEPSEEK_API_KEY 后写入 window.DS_ENV。
 */
export function envKey() {
  if (typeof window === 'undefined') return '';
  const cfg = window.DS_ENV;
  if (!cfg || typeof cfg.apiKey !== 'string') return '';
  return cfg.apiKey.trim();
}

export function activeKeyValue() {
  const k = state.keys.find((x) => x.id === state.activeKeyId);
  const stored = k ? b64decode(k.value).trim() : '';
  return stored || envKey();
}

/** 当前密钥来源：'local' | 'env' | 'none' */
export function keySource() {
  const k = state.keys.find((x) => x.id === state.activeKeyId);
  if (k && b64decode(k.value).trim()) return 'local';
  if (envKey()) return 'env';
  return 'none';
}

export function maskKey(raw) {
  if (!raw) return '';
  if (raw.length <= 10) return raw.slice(0, 2) + '***';
  return raw.slice(0, 6) + '…' + raw.slice(-4);
}

/* ----------------------------- 费用 ----------------------------- */

export function persistCost() {
  write(K.cost, state.cost);
}

export function rollCostDay() {
  if (state.cost.date !== dayKey()) {
    state.cost = freshCost();
    persistCost();
    return true;
  }
  return false;
}

export function recordUsage(usage) {
  rollCostDay();
  const promptTokens = Number(usage.promptTokens || 0);
  const completionTokens = Number(usage.completionTokens || 0);
  const cacheHitTokens = Number(usage.cacheHitTokens || 0);
  state.cost.promptTokens += promptTokens;
  state.cost.completionTokens += completionTokens;
  state.cost.cacheHitTokens += cacheHitTokens;
  state.cost.requests += 1;
  state.cost.usd += computeUsd({ promptTokens, completionTokens, cacheHitTokens }, new Date());
  persistCost();
}

export function resetCost() {
  state.cost = freshCost();
  persistCost();
}

/* ----------------------------- UI 状态 ----------------------------- */

export function persistUi() {
  write(K.ui, { costOpen: state.ui.costOpen });
}

/* ----------------------------- 导入 / 导出 ----------------------------- */

export function buildExport() {
  return {
    app: 'deepseek-chat-demo',
    version: 1,
    exportedAt: new Date().toISOString(),
    settings: {
      systemPrompt: state.settings.systemPrompt,
      temperature: state.settings.temperature,
      topP: state.settings.topP,
      contextLimit: state.settings.contextLimit,
      pauseEvery25: state.settings.pauseEvery25,
    },
    keyNames: state.keys.map((k) => k.name),
    threads: state.threads.map((t) => ({
      id: t.id,
      title: t.title,
      createdAt: t.createdAt,
      updatedAt: t.updatedAt,
      pinned: !!t.pinned,
      thinking: !!t.thinking,
      webSearch: !!t.webSearch,
      summary: t.summary || null,
      messages: (t.messages || []).map((m) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        reasoning: m.reasoning || '',
        createdAt: m.createdAt,
      })),
    })),
  };
}

export function applyImport(data) {
  if (!data || !Array.isArray(data.threads)) throw new Error('文件格式不正确：缺少 threads 数组');
  const threads = data.threads
    .filter((t) => t && Array.isArray(t.messages))
    .map((t) => ({
      id: t.id || uid(),
      title: t.title || '新对话',
      createdAt: t.createdAt || Date.now(),
      updatedAt: t.updatedAt || Date.now(),
      pinned: !!t.pinned,
      thinking: false,
      webSearch: false,
      summary: t.summary && t.summary.text ? t.summary : null,
      roundsSinceConfirm: 0,
      messages: t.messages
        .filter((m) => m && (m.role === 'user' || m.role === 'assistant'))
        .map((m) => ({
          id: m.id || uid(),
          role: m.role,
          content: String(m.content || ''),
          reasoning: String(m.reasoning || ''),
          createdAt: m.createdAt || Date.now(),
        })),
    }));
  if (!threads.length) throw new Error('文件中没有任何对话');
  state.threads = threads;
  state.currentId = threads[0].id;
  persistThreads();
  return threads.length;
}
