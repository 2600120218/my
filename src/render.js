import { state, currentThread, activeKeyValue, keySource } from './store.js';
import { groupThreads, esc, mdToHtml, fmtClock, snippet } from './utils.js';
import { PRICING, isOffPeak, fmtUsd, fmtCny, periodLabel } from './pricing.js';

const $ = (sel, root) => (root || document).querySelector(sel);

const ICON = {
  menu: '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
  plus: '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M12 5v14M5 12h14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
  search: '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><circle cx="11" cy="11" r="6.5" fill="none" stroke="currentColor" stroke-width="1.7"/><path d="M16 16l4 4" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"/></svg>',
  send: '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M12 19V5M6 11l6-6 6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  stop: '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><rect x="7" y="7" width="10" height="10" rx="2" fill="currentColor"/></svg>',
  more: '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><circle cx="5.5" cy="12" r="1.6" fill="currentColor"/><circle cx="12" cy="12" r="1.6" fill="currentColor"/><circle cx="18.5" cy="12" r="1.6" fill="currentColor"/></svg>',
  close: '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
};

function sessionTime(ts) {
  const d = new Date(ts || Date.now());
  const n = new Date();
  const sameDay = d.toDateString() === n.toDateString();
  if (sameDay) return fmtClock(ts);
  return d.getMonth() + 1 + '/' + d.getDate();
}

function matchSearch(thread, q) {
  if (!q) return true;
  const needle = q.toLowerCase();
  if ((thread.title || '').toLowerCase().indexOf(needle) >= 0) return true;
  return (thread.messages || []).some((m) => (m.content || '').toLowerCase().indexOf(needle) >= 0);
}

/* ------------------------------- 侧边栏 ------------------------------- */

export function renderSidebar() {
  const el = $('#sidebar');
  if (!el) return;
  const q = (state.ui.search || '').trim();
  const list = state.threads.filter((t) => matchSearch(t, q));
  const groups = groupThreads(list);

  let body = '';
  if (!groups.length) {
    body = '<div class="sb-empty">' + (q ? '没有匹配的对话' : '还没有对话') + '</div>';
  } else {
    for (const g of groups) {
      body += '<div class="sb-group"><div class="sb-group-title">' + esc(g.label) + '</div>';
      for (const t of g.items) {
        const active = t.id === state.currentId;
        const preview = q && t.messages.length ? snippet(findFirstMatch(t, q), 42) : '';
        body +=
          '<div class="sess' + (active ? ' active' : '') + '" data-thread="' + t.id + '">' +
          '<button class="sess-main" data-action="select-thread" data-id="' + t.id + '">' +
          '<span class="sess-title">' + esc(t.title || '新对话') + '</span>' +
          '<span class="sess-sub">' + esc(preview || sessionTime(t.updatedAt) + ' · ' + t.messages.length + ' 条') + '</span>' +
          '</button>' +
          '<button class="sess-more" data-action="thread-menu" data-id="' + t.id + '" aria-label="更多">' + ICON.more + '</button>' +
          '</div>';
      }
      body += '</div>';
    }
  }

  el.innerHTML =
    '<div class="sb-inner">' +
    '<div class="sb-top">' +
    '<button class="btn-new" data-action="new-thread">' + ICON.plus + '<span>新建对话</span></button>' +
    '</div>' +
    '<div class="sb-search">' + ICON.search +
    '<input id="sb-search-input" type="search" placeholder="搜索对话内容" value="' + esc(state.ui.search) + '" />' +
    '</div>' +
    '<div class="sb-list">' + body + '</div>' +
    renderCostPanel() +
    '</div>';
  // 光标保持在搜索框末尾
}

function findFirstMatch(t, q) {
  const needle = q.toLowerCase();
  const hit = (t.messages || []).find((m) => (m.content || '').toLowerCase().indexOf(needle) >= 0);
  return hit ? hit.content : t.title;
}

function renderCostPanel() {
  const c = state.cost;
  const open = state.ui.costOpen;
  const detail = open
    ? '<div class="cost-panel" id="cost-panel">' +
      row('今日总消耗', fmtCny(c.usd)) +
      row('请求次数', String(c.requests)) +
      '<div class="cost-divider"></div>' +
      row('输入 tokens', String(c.promptTokens)) +
      row('缓存命中输入', String(c.cacheHitTokens)) +
      row('输出 tokens', String(c.completionTokens)) +
      '<div class="cost-divider"></div>' +
      row('计价口径', isOffPeak(new Date()) ? '空闲价' : '高峰价 ×2') +
      '<div class="cost-note">输入 $' + PRICING.perMillion.input + '/M，缓存命中 $' + PRICING.perMillion.cacheInput +
      '/M，输出 $' + PRICING.perMillion.output + '/M；高峰翻倍；汇率 ' + PRICING.fx + '</div>' +
      '<div class="cost-note">' + esc(periodLabel(new Date())) + ' · 原价 ' + fmtUsd(c.usd) + '</div>' +
      '<button class="cost-reset" data-action="reset-cost">手动清零</button>' +
      '</div>'
    : '';

  return (
    '<div class="sb-foot">' +
    '<div class="sb-links">' +
    '<button class="sb-link" data-action="compress">压缩历史</button>' +
    '<button class="sb-link" data-action="open-settings">设置</button>' +
    '<button class="sb-link cost-toggle' + (open ? ' open' : '') + '" data-action="toggle-cost">费用</button>' +
    '</div>' +
    detail +
    '</div>'
  );
}

function row(label, value) {
  return '<div class="cost-row"><span>' + esc(label) + '</span><b>' + esc(value) + '</b></div>';
}

/* ------------------------------- 顶栏 ------------------------------- */

export function renderHeader() {
  const el = $('#header');
  if (!el) return;
  const t = currentThread();
  el.innerHTML =
    '<button class="icon-btn" data-action="toggle-sidebar" aria-label="侧边栏">' + ICON.menu + '</button>' +
    '<div class="header-title">' + esc(t && t.title ? t.title : 'DeepSeek') + '</div>' +
    '<button class="icon-btn" data-action="new-thread" aria-label="新建对话">' + ICON.plus + '</button>';
}

/* ------------------------------- 对话区 ------------------------------- */

const SUGGESTIONS = [
  '帮我写一段自我介绍',
  '解释一下什么是向量数据库',
  '把这段话润色得更正式',
  '给我一个周末学习计划',
];

export function renderChat() {
  const el = $('#chat');
  if (!el) return;
  const t = currentThread();
  if (!t) {
    el.innerHTML = '';
    return;
  }
  if (!t.messages.length) {
    const noKey = keySource() === 'none';
    el.innerHTML =
      '<div class="welcome">' +
      '<div class="welcome-logo">' + whale() + '</div>' +
      '<h1>我是 DeepSeek，很高兴见到你！</h1>' +
      (noKey ? '<button class="welcome-hint" data-action="open-settings">尚未配置 API Key，点此打开设置填写</button>' : '') +
      '<div class="chips">' +
      SUGGESTIONS.map((s) => '<button class="suggest" data-action="suggest" data-text="' + esc(s) + '">' + esc(s) + '</button>').join('') +
      '</div></div>';
    return;
  }

  let html = '<div class="msg-list">';
  if (t.summary && t.summary.text) {
    html +=
      '<div class="summary-banner"><div class="summary-head"><span>已压缩的历史摘要</span>' +
      '<button class="link-btn" data-action="clear-summary">取消压缩</button></div>' +
      '<div class="summary-text">' + esc(t.summary.text) + '</div></div>';
  }
  for (const m of t.messages) html += renderMessage(m, t);
  html += '</div>';
  el.innerHTML = html;
  scrollToBottom(false);
}

function renderMessage(m, thread) {
  const editing = state.ui.editing && state.ui.editing.id === m.id;
  const streaming = state.ui.sending && m.id === state.ui.streamingId;

  if (editing) {
    return (
      '<div class="msg ' + m.role + '" data-msg-id="' + m.id + '">' +
      '<div class="edit-box">' +
      '<textarea class="edit-input" data-edit-input="' + m.id + '">' + esc(m.content) + '</textarea>' +
      '<div class="edit-actions">' +
      '<button class="btn ghost" data-action="cancel-edit">取消</button>' +
      '<button class="btn primary" data-action="save-edit" data-id="' + m.id + '">保存并重新生成</button>' +
      '</div></div></div>'
    );
  }

  if (m.role === 'user') {
    return (
      '<div class="msg user" data-msg-id="' + m.id + '">' +
      '<div class="bubble user-bubble"><div class="md">' + mdToHtml(m.content) + '</div></div>' +
      '<div class="msg-actions">' +
      act('copy-msg', m.id, '复制') +
      act('edit-msg', m.id, '编辑') +
      act('undo-msg', m.id, '撤回') +
      '</div></div>'
    );
  }

  const reasoningHtml =
    m.reasoning && m.reasoning.trim()
      ? '<details class="reasoning"' + (streaming ? ' open' : '') + '><summary>深度思考</summary><div class="reasoning-body">' +
        esc(m.reasoning) + '</div></details>'
      : '';

  return (
    '<div class="msg assistant" data-msg-id="' + m.id + '">' +
    '<div class="avatar">' + whale() + '</div>' +
    '<div class="assistant-main">' +
    reasoningHtml +
    '<div class="md" data-streaming="' + (streaming ? '1' : '0') + '">' + mdToHtml(m.content || (streaming ? '' : '')) +
    (streaming ? '<span class="caret"></span>' : '') + '</div>' +
    '<div class="msg-actions">' +
    act('copy-msg', m.id, '复制') +
    act('edit-msg', m.id, '编辑') +
    act('regen-msg', m.id, '重新生成') +
    act('undo-msg', m.id, '撤回') +
    '</div></div></div>'
  );
}

function act(action, id, label) {
  return '<button class="act" data-action="' + action + '" data-id="' + id + '">' + esc(label) + '</button>';
}

function whale() {
  return '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M3.5 11.5c1.6 0 3-1 3.7-2.4C8.4 6.6 10.9 5 13.6 5c3.6 0 6.5 2.7 6.5 6.1 0 3.2-2.4 5.6-5.3 5.9-.5 1.6-1.9 2.5-3.4 2.5-1 0-1.9-.4-2.6-1.1M6.5 13.2c.9 2.9 3.4 4.6 6.4 4.6" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/><circle cx="15.4" cy="9.6" r=".9" fill="currentColor"/></svg>';
}

export function renderStreamingMessage(message) {
  if (!message) return;
  const node = document.querySelector('[data-msg-id="' + message.id + '"]');
  if (!node) return;
  const md = node.querySelector('.md');
  if (!md) return;
  md.innerHTML = mdToHtml(message.content) + (state.ui.sending ? '<span class="caret"></span>' : '');
  const details = node.querySelector('details.reasoning .reasoning-body');
  if (details && message.reasoning) details.textContent = message.reasoning;
  scrollToBottom(true);
}

export function scrollToBottom(force) {
  const el = $('#chat');
  if (!el) return;
  const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 160;
  if (force || nearBottom) el.scrollTop = el.scrollHeight;
}

/* ------------------------------- 输入区 ------------------------------- */

export function renderComposer() {
  const el = $('#composer');
  if (!el) return;
  const t = currentThread();
  const thinking = !!(t && t.thinking);
  const webSearch = !!(t && t.webSearch);
  const draft = state.ui.draft && state.ui.draft.threadId === (t && t.id) ? state.ui.draft.text : '';

  el.innerHTML =
    '<div class="composer">' +
    '<div class="toggles">' +
    '<button class="chip' + (thinking ? ' on' : '') + '" data-action="toggle-thinking">深度思考</button>' +
    '<button class="chip' + (webSearch ? ' on' : '') + '" data-action="toggle-search">联网搜索</button>' +
    '</div>' +
    '<div class="input-row">' +
    '<textarea id="composer-input" rows="1" placeholder="给 DeepSeek 发送消息">' + esc(draft) + '</textarea>' +
    '<button class="send' + (state.ui.sending ? ' streaming' : '') + '" data-action="' + (state.ui.sending ? 'stop' : 'send') + '">' +
    (state.ui.sending ? ICON.stop : ICON.send) +
    '</button>' +
    '</div>' +
    '<div class="composer-hint">内容由 AI 生成，请自行甄别</div>' +
    '</div>';

  const input = $('#composer-input');
  if (input) {
    autoGrow(input);
    if (draft && state.ui.draft && state.ui.draft.focus) {
      input.focus();
      input.setSelectionRange(input.value.length, input.value.length);
    }
  }
}

export function autoGrow(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 180) + 'px';
}

/* ------------------------------- 弹层 ------------------------------- */

export function showToast(text) {
  const root = $('#toast-root');
  if (!root) return;
  const node = document.createElement('div');
  node.className = 'toast';
  node.textContent = text;
  root.appendChild(node);
  setTimeout(() => {
    node.classList.add('out');
    setTimeout(() => node.remove(), 260);
  }, 2200);
}

let modalLocked = false;

export function closeModal() {
  const root = $('#modal-root');
  if (root) root.innerHTML = '';
  modalLocked = false;
}

/** 弹窗是否允许被点击遮罩 / Esc 关闭 */
export function canDismissModal() {
  return !modalLocked;
}

export function openModal(html, opts) {
  const root = $('#modal-root');
  if (!root) return;
  const options = opts || {};
  modalLocked = options.dismissible === false;
  root.innerHTML =
    '<div class="modal-scrim" data-action="' + (options.dismissible === false ? 'noop' : 'close-modal') + '"></div>' +
    '<div class="modal' + (options.wide ? ' wide' : '') + '" role="dialog" aria-modal="true">' + html + '</div>';
  const modal = root.querySelector('.modal');
  if (options.onMount && modal) options.onMount(modal);
  return modal;
}

export function confirmDialog(opts) {
  return new Promise((resolve) => {
    const modal = openModal(
      '<div class="modal-head"><h3>' + esc(opts.title || '确认') + '</h3></div>' +
        '<div class="modal-body"><p>' + esc(opts.text || '') + '</p></div>' +
        '<div class="modal-foot">' +
        '<button class="btn ghost" data-confirm="0">' + esc(opts.cancelText || '取消') + '</button>' +
        '<button class="btn primary" data-confirm="1">' + esc(opts.okText || '确定') + '</button>' +
        '</div>',
      { dismissible: false }
    );
    if (!modal) return resolve(false);
    modal.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-confirm]');
      if (!btn) return;
      closeModal();
      resolve(btn.getAttribute('data-confirm') === '1');
    });
  });
}

export function promptDialog(opts) {
  return new Promise((resolve) => {
    const modal = openModal(
      '<div class="modal-head"><h3>' + esc(opts.title || '输入') + '</h3></div>' +
        '<div class="modal-body"><input class="text-input" id="prompt-input" value="' + esc(opts.value || '') + '" placeholder="' + esc(opts.placeholder || '') + '" /></div>' +
        '<div class="modal-foot">' +
        '<button class="btn ghost" data-confirm="0">取消</button>' +
        '<button class="btn primary" data-confirm="1">确定</button>' +
        '</div>',
      { dismissible: false, onMount: (m) => { const i = m.querySelector('#prompt-input'); if (i) { i.focus(); i.select(); } } }
    );
    if (!modal) return resolve(null);
    modal.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-confirm]');
      if (!btn) return;
      const input = modal.querySelector('#prompt-input');
      const val = input ? input.value : '';
      closeModal();
      resolve(btn.getAttribute('data-confirm') === '1' ? val : null);
    });
    const input = modal.querySelector('#prompt-input');
    if (input) {
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const val = input.value;
          closeModal();
          resolve(val);
        }
      });
    }
  });
}

/* ------------------------------- 会话菜单 ------------------------------- */

let menuNode = null;

export function closeThreadMenu() {
  if (menuNode && menuNode.parentNode) menuNode.parentNode.removeChild(menuNode);
  menuNode = null;
}

export function openThreadMenu(id, anchor) {
  closeThreadMenu();
  const t = state.threads.find((x) => x.id === id);
  if (!t) return;
  const node = document.createElement('div');
  node.className = 'thread-menu';
  node.innerHTML =
    '<button data-action="pin-thread" data-id="' + id + '">' + (t.pinned ? '取消置顶' : '置顶') + '</button>' +
    '<button data-action="rename-thread" data-id="' + id + '">重命名</button>' +
    '<button class="danger" data-action="delete-thread" data-id="' + id + '">删除（不可恢复）</button>';
  document.body.appendChild(node);
  menuNode = node;
  const rect = anchor.getBoundingClientRect();
  const w = 168;
  const top = Math.min(rect.bottom + 6, window.innerHeight - 140);
  const left = Math.min(Math.max(8, rect.right - w), window.innerWidth - w - 8);
  node.style.top = top + 'px';
  node.style.left = left + 'px';
}

export function renderAll() {
  renderSidebar();
  renderHeader();
  renderChat();
  renderComposer();
}
