import {
  state,
  loadAll,
  currentThread,
  createThread,
  selectThread,
  deleteThread,
  togglePin,
  renameThread,
  addMessage,
  updateMessage,
  truncateFrom,
  persistThreads,
  activeKeyValue,
  recordUsage,
  resetCost,
  rollCostDay,
  persistUi,
} from './store.js';
import { renderAll, renderSidebar, renderChat, renderComposer, renderStreamingMessage, showToast, confirmDialog, promptDialog, openThreadMenu, closeThreadMenu, closeModal, openModal, autoGrow, scrollToBottom, canDismissModal } from './render.js';
import { openSettings, closeSettings } from './settings.js';
import { streamChat, summarizeHistory } from './api.js';
import { uid, esc, copyText, mdToHtml } from './utils.js';

let abortCtrl = null;
let rafPending = false;

/* --------------------------------- 启动 --------------------------------- */

let booted = false;

function boot() {
  if (booted) return;
  booted = true;

  installErrorReporting();
  // 先绑定事件，再渲染：这样即使渲染阶段抛错，按钮也不会"全部失灵"
  bindGlobal();

  try {
    loadAll();
    rollCostDay();
    state.ui.draft = { threadId: state.currentId, text: '' };
    renderAll();
  } catch (err) {
    reportError(err, '初始化失败');
    try {
      loadAll();
      renderAll();
    } catch (e2) {
      /* 保底失败则只显示错误 */
    }
  }

  window.addEventListener('resize', () => {
    if (window.innerWidth > 860) setSidebar(false, true);
  });

  // ?section=keys 可直接打开设置并定位到密钥区
  try {
    const params = new URLSearchParams(window.location.search);
    if (params.get('section') === 'keys') setTimeout(() => openSettings('keys'), 60);
  } catch (e) {
    /* ignore */
  }
  // 每日凌晨自动归零：每分钟检查一次日期是否变化
  setInterval(() => {
    if (rollCostDay()) {
      renderSidebar();
      if (state.ui.costOpen) showToast('已跨天，今日费用自动归零');
    }
  }, 60000);
}

/* ---------------------------- 错误可见化 ---------------------------- */

function reportError(err, prefix) {
  const msg = (err && (err.message || err)) || '未知错误';
  if (window.console && console.error) console.error('[' + (prefix || 'error') + ']', err);
  try {
    showToast((prefix ? prefix + '：' : '') + msg);
  } catch (e) {
    /* ignore */
  }
}

function installErrorReporting() {
  window.addEventListener('error', (e) => {
    if (e && e.message && /Script error/i.test(e.message)) return;
    reportError(e && e.error ? e.error : new Error(e.message), '页面错误');
  });
  window.addEventListener('unhandledrejection', (e) => {
    reportError(e && e.reason, '请求异常');
    if (e && e.preventDefault) e.preventDefault();
  });
}

function setSidebar(open, silent) {
  state.ui.sidebarOpen = open;
  const sb = document.getElementById('sidebar');
  const scrim = document.getElementById('scrim');
  if (sb) sb.classList.toggle('open', open);
  if (scrim) scrim.classList.toggle('show', open);
  if (!silent) {
    const btn = document.querySelector('[data-action="toggle-sidebar"]');
    if (btn && open) btn.setAttribute('aria-expanded', 'true');
  }
}

/* ------------------------------- 对话发送 ------------------------------- */

function readComposer() {
  const input = document.getElementById('composer-input');
  return input ? input.value : '';
}

function setComposer(text, focus) {
  const t = currentThread();
  state.ui.draft = { threadId: t ? t.id : null, text: text || '', focus: !!focus };
  renderComposer();
  const input = document.getElementById('composer-input');
  if (input && focus) {
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
  }
}

async function doSend() {
  if (state.ui.sending) return;
  const t = currentThread();
  if (!t) return;
  const text = readComposer().trim();
  if (!text) return;

  if (!activeKeyValue()) {
    showToast('请先在设置页保存 API Key');
    openSettings();
    return;
  }

  const userCount = t.messages.filter((m) => m.role === 'user').length + 1;
  if (state.settings.pauseEvery25 && userCount > 0 && userCount % 25 === 0) {
    const ok = await confirmDialog({
      title: '已连续对话 ' + userCount + ' 轮',
      text: '是否继续？这只是一次例行确认，可在设置中关闭。',
      okText: '继续',
      cancelText: '暂停',
    });
    if (!ok) return;
  }

  setComposer('', false);
  addMessage(t, { role: 'user', content: text });
  renderAll();
  await generate(t);
}

function buildPayload(thread) {
  const system = state.settings.systemPrompt || '';
  const summary = thread.summary && thread.summary.text ? thread.summary.text : '';
  const systemContent = summary
    ? system + '\n\n【此前对话摘要（本地完整记录仍保留）】\n' + summary
    : system;

  const messages = [{ role: 'system', content: systemContent }];
  let history = thread.messages.filter((m) => m.role === 'user' || m.role === 'assistant');
  if (summary) {
    // 压缩后：摘要 + 最近 5 轮完整对话
    history = history.slice(-10);
  } else {
    const limit = Math.max(2, state.settings.contextLimit || 20);
    history = history.slice(-limit);
  }
  while (history.length && history[0].role !== 'user') history.shift();

  for (const m of history) {
    if (!m.content || !m.content.trim()) continue;
    messages.push({ role: m.role, content: m.content });
  }
  return messages;
}

async function generate(thread) {
  if (state.ui.sending) return;
  const apiKey = activeKeyValue();
  if (!apiKey) {
    showToast('请先在设置页保存 API Key');
    openSettings();
    return;
  }

  const payload = buildPayload(thread);
  if (payload.length < 2) {
    showToast('没有可发送的内容');
    return;
  }
  if (!thread.messages.some((m) => m.role === 'user')) return;

  const reply = addMessage(thread, { role: 'assistant', content: '', reasoning: '' });
  state.ui.sending = true;
  state.ui.streamingId = reply.id;
  state.ui.abort = new AbortController();
  abortCtrl = state.ui.abort;

  renderAll();
  scrollToBottom(true);

  let usageRecorded = false;
  const onUsage = (u) => {
    if (usageRecorded) return;
    usageRecorded = true;
    recordUsage(u);
  };

  try {
    const result = await streamChat({
      apiKey,
      messages: payload,
      temperature: state.settings.temperature,
      topP: state.settings.topP,
      thinking: !!thread.thinking,
      webSearch: !!thread.webSearch,
      signal: state.ui.abort.signal,
      onDelta: (delta, full) => {
        reply.content = full;
        scheduleStreamRender(reply);
      },
      onReasoning: (delta, full) => {
        reply.reasoning = full;
      },
      onUsage,
    });
    reply.content = result.content;
    reply.reasoning = result.reasoning || reply.reasoning;
    if (result.usage) onUsage(result.usage);
  } catch (err) {
    if (err && err.name === 'AbortError') {
      reply.content = reply.content || '';
      showToast('已停止生成');
    } else {
      const message = (err && err.message) || '请求失败';
      showToast(message);
      if (!reply.content || !reply.content.trim()) {
        thread.messages = thread.messages.filter((m) => m.id !== reply.id);
      }
    }
  } finally {
    state.ui.sending = false;
    state.ui.streamingId = null;
    state.ui.abort = null;
    abortCtrl = null;
    persistThreads();
    renderAll();
    scrollToBottom(false);
  }
}

function scheduleStreamRender(msg) {
  if (rafPending) return;
  rafPending = true;
  requestAnimationFrame(() => {
    rafPending = false;
    renderStreamingMessage(msg);
  });
}

function stopStreaming() {
  if (abortCtrl) abortCtrl.abort();
}

/* ------------------------------- 消息操作 ------------------------------- */

function findIndex(thread, id) {
  return thread.messages.findIndex((m) => m.id === id);
}

async function onEditMessage(id) {
  const t = currentThread();
  if (!t) return;
  state.ui.editing = { id };
  renderChat();
  const box = document.querySelector('[data-edit-input="' + id + '"]');
  if (box) {
    box.focus();
    box.setSelectionRange(box.value.length, box.value.length);
  }
}

function onSaveEdit(id) {
  const t = currentThread();
  if (!t) return;
  const box = document.querySelector('[data-edit-input="' + id + '"]');
  if (!box) return;
  const text = box.value.trim();
  if (!text) {
    showToast('内容不能为空');
    return;
  }
  const idx = findIndex(t, id);
  if (idx < 0) return;
  const msg = t.messages[idx];
  msg.content = text;
  truncateFrom(t, idx + 1);
  state.ui.editing = null;
  persistThreads();

  if (msg.role === 'user') {
    renderAll();
    generate(t);
  } else {
    renderAll();
    showToast('已保存，可点击「重新生成」继续');
  }
}

function onUndoMessage(id) {
  const t = currentThread();
  if (!t) return;
  const idx = findIndex(t, id);
  if (idx < 0) return;
  const msg = t.messages[idx];
  const draft = msg.role === 'user' ? msg.content : '';
  truncateFrom(t, idx);
  renderAll();
  if (draft) setComposer(draft, true);
  showToast('已撤回该轮对话');
}

async function onRegenerate(id) {
  const t = currentThread();
  if (!t || state.ui.sending) return;
  const idx = findIndex(t, id);
  if (idx < 0) return;
  if (idx === 0) {
    showToast('没有可重新生成的上下文');
    return;
  }
  truncateFrom(t, idx);
  renderAll();
  await generate(t);
}

/* ------------------------------- 压缩历史 ------------------------------- */

async function onCompress() {
  const t = currentThread();
  if (!t) return;
  if (t.messages.length < 12) {
    showToast('对话还比较短（至少 6 轮后再压缩）');
    return;
  }
  const ok = await confirmDialog({
    title: '压缩历史',
    text: '将用 deepseek-chat 把较早的对话浓缩成 200~300 字摘要。本地完整记录仍会保留，之后发送给模型的内容只有摘要 + 最近 5 轮对话。此操作只在点击时发生。',
    okText: '开始压缩',
  });
  if (!ok) return;

  const apiKey = activeKeyValue();
  if (!apiKey) {
    showToast('请先在设置页保存 API Key');
    return;
  }

  const cutoff = Math.max(0, t.messages.length - 10);
  const older = t.messages.slice(0, cutoff);
  const transcript = older
    .map((m) => (m.role === 'user' ? '用户：' : '助手：') + (m.content || ''))
    .join('\n')
    .slice(0, 20000);

  const modal = openModal(
    '<div class="modal-head"><h3>正在压缩历史</h3></div>' +
      '<div class="modal-body"><p class="loading-line"><span class="spinner"></span>正在调用 deepseek-chat 生成摘要…</p></div>',
    { dismissible: false }
  );
  try {
    const res = await summarizeHistory({ apiKey, transcript });
    t.summary = { text: res.text, createdAt: Date.now(), covered: cutoff };
    persistThreads();
    showToast('已压缩 ' + cutoff + ' 条消息');
  } catch (err) {
    showToast('压缩失败：' + ((err && err.message) || '未知错误'));
  } finally {
    closeModal();
    renderAll();
  }
}

/* ------------------------------- 侧边栏操作 ------------------------------- */

function onNewThread() {
  createThread();
  state.ui.editing = null;
  setComposer('', false);
  renderAll();
  setSidebar(false);
  const input = document.getElementById('composer-input');
  if (input) input.focus();
}

async function onRenameThread(id) {
  const t = state.threads.find((x) => x.id === id);
  if (!t) return;
  const name = await promptDialog({ title: '重命名对话', value: t.title, placeholder: '对话名称' });
  if (name == null) return;
  renameThread(id, name);
  renderAll();
}

async function onDeleteThread(id) {
  closeThreadMenu();
  const ok = await confirmDialog({
    title: '删除对话',
    text: '该对话及其全部消息将被永久删除，无法恢复。',
    okText: '删除',
  });
  if (!ok) return;
  deleteThread(id);
  state.ui.editing = null;
  setComposer('', false);
  renderAll();
  showToast('对话已删除');
}

/* ------------------------------- 全局事件 ------------------------------- */

function bindGlobal() {
  document.addEventListener('click', onDocumentClick);
  document.addEventListener('keydown', onKeyDown);
  document.addEventListener('input', onInput);
  document.addEventListener('change', onChange);
}

function onDocumentClick(e) {
  // 会话菜单：点外部关闭
  const menu = e.target.closest('.thread-menu');
  if (!menu && !e.target.closest('[data-action="thread-menu"]')) closeThreadMenu();

  // 代码块复制
  const copyBtn = e.target.closest('[data-copy]');
  if (copyBtn) {
    copyText(copyBtn.getAttribute('data-copy'));
    showToast('已复制');
    return;
  }

  // 模态遮罩
  if (e.target.classList && e.target.classList.contains('modal-scrim')) {
    if (canDismissModal()) closeSettings();
    return;
  }
  // 模态内部交给各自的处理函数
  if (e.target.closest('#modal-root')) return;

  const btn = e.target.closest('[data-action]');
  if (!btn) return;
  const action = btn.getAttribute('data-action');
  const id = btn.getAttribute('data-id');

  switch (action) {
    case 'toggle-sidebar': {
      const sb = document.getElementById('sidebar');
      setSidebar(!(sb && sb.classList.contains('open')));
      break;
    }
    case 'new-thread':
      onNewThread();
      break;
    case 'select-thread':
      if (id === state.currentId) {
        setSidebar(false);
        break;
      }
      state.ui.editing = null;
      selectThread(id);
      setComposer('', false);
      renderAll();
      setSidebar(false);
      break;
    case 'thread-menu':
      closeThreadMenu();
      openThreadMenu(id, btn);
      break;
    case 'pin-thread':
      closeThreadMenu();
      togglePin(id);
      renderAll();
      break;
    case 'rename-thread':
      closeThreadMenu();
      onRenameThread(id);
      break;
    case 'delete-thread':
      closeThreadMenu();
      onDeleteThread(id);
      break;
    case 'toggle-thinking': {
      const t = currentThread();
      if (!t) break;
      t.thinking = !t.thinking;
      persistThreads();
      renderComposer();
      break;
    }
    case 'toggle-search': {
      const t = currentThread();
      if (!t) break;
      t.webSearch = !t.webSearch;
      persistThreads();
      renderComposer();
      break;
    }
    case 'send':
      doSend();
      break;
    case 'stop':
      stopStreaming();
      break;
    case 'suggest':
      setComposer(btn.getAttribute('data-text') || '', true);
      break;
    case 'copy-msg': {
      const t = currentThread();
      const msg = t && t.messages.find((m) => m.id === id);
      if (msg) {
        copyText(msg.content);
        showToast('已复制');
      }
      break;
    }
    case 'edit-msg':
      onEditMessage(id);
      break;
    case 'cancel-edit':
      state.ui.editing = null;
      renderChat();
      break;
    case 'save-edit':
      onSaveEdit(id);
      break;
    case 'undo-msg':
      onUndoMessage(id);
      break;
    case 'regen-msg':
      onRegenerate(id);
      break;
    case 'compress':
      closeThreadMenu();
      setSidebar(false);
      onCompress();
      break;
    case 'open-settings':
      setSidebar(false);
      openSettings();
      break;
    case 'toggle-cost':
      state.ui.costOpen = !state.ui.costOpen;
      persistUi();
      renderSidebar();
      break;
    case 'reset-cost':
      resetCost();
      renderSidebar();
      showToast('今日费用已清零');
      break;
    case 'clear-summary': {
      const t = currentThread();
      if (!t) break;
      t.summary = null;
      persistThreads();
      renderAll();
      showToast('已取消压缩');
      break;
    }
    case 'noop':
      break;
    default:
      break;
  }
}

function onKeyDown(e) {
  if (e.key === 'Escape') {
    closeThreadMenu();
    if (canDismissModal()) closeSettings();
    setSidebar(false);
    return;
  }
  const input = e.target;
  if (input && input.id === 'composer-input') {
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      e.preventDefault();
      doSend();
    }
    return;
  }
  if (input && input.matches && input.matches('.edit-input')) {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      const mid = input.getAttribute('data-edit-input');
      if (mid) onSaveEdit(mid);
    }
  }
}

function onInput(e) {
  const target = e.target;
  if (!target) return;

  if (target.id === 'composer-input') {
    const t = currentThread();
    state.ui.draft = { threadId: t ? t.id : null, text: target.value };
    autoGrow(target);
    return;
  }

  if (target.id === 'sb-search-input') {
    const pos = target.selectionStart;
    state.ui.search = target.value;
    renderSidebar();
    const next = document.getElementById('sb-search-input');
    if (next) {
      next.focus();
      try {
        next.setSelectionRange(pos, pos);
      } catch (err) {
        /* ignore */
      }
    }
  }
}

function onChange(e) {
  const target = e.target;
  if (!target) return;
  if (target.id === 'system-prompt') {
    /* 由设置页自身处理 */
  }
}

document.addEventListener('DOMContentLoaded', boot);
if (document.readyState !== 'loading') boot();
