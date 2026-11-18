export function uid() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

export function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function b64encode(str) {
  return btoa(unescape(encodeURIComponent(str)));
}

export function b64decode(str) {
  try {
    return decodeURIComponent(escape(atob(str)));
  } catch (e) {
    return '';
  }
}

export function pad2(n) {
  return n < 10 ? '0' + n : String(n);
}

export function fmtClock(ts) {
  const d = new Date(ts);
  return pad2(d.getHours()) + ':' + pad2(d.getMinutes());
}

export function fmtDateTime(ts) {
  const d = new Date(ts);
  return d.getFullYear() + '-' + pad2(d.getMonth() + 1) + '-' + pad2(d.getDate()) + ' ' + pad2(d.getHours()) + ':' + pad2(d.getMinutes());
}

export function dayKey(d) {
  const t = d || new Date();
  return t.getFullYear() + '-' + pad2(t.getMonth() + 1) + '-' + pad2(t.getDate());
}

export function startOfToday() {
  const n = new Date();
  return new Date(n.getFullYear(), n.getMonth(), n.getDate()).getTime();
}

const DAY = 86400000;

export function groupThreads(threads) {
  const groups = [];
  const pinned = threads.filter((t) => t.pinned).sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));
  if (pinned.length) groups.push({ label: '置顶', items: pinned });

  const rest = threads.filter((t) => !t.pinned).sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));
  const today = startOfToday();
  const buckets = [];
  const index = new Map();
  for (const t of rest) {
    const at = t.updatedAt || t.createdAt || 0;
    let label;
    if (at >= today) label = '今天';
    else if (at >= today - 6 * DAY) label = '7天内';
    else if (at >= today - 29 * DAY) label = '30天内';
    else {
      const d = new Date(at);
      label = d.getFullYear() + '年' + (d.getMonth() + 1) + '月';
    }
    if (!index.has(label)) {
      const bucket = { label, items: [] };
      index.set(label, bucket);
      buckets.push(bucket);
    }
    index.get(label).items.push(t);
  }
  return groups.concat(buckets);
}

export function debounce(fn, delay) {
  let timer = null;
  return function () {
    const args = arguments;
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(null, args), delay || 200);
  };
}

/* ---------------- 轻量 Markdown 渲染 ---------------- */

function inline(text) {
  return text
    .replace(/`([^`\n]+)`/g, (m, c) => '<code class="inline">' + c + '</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
}

function renderPlainBlock(block) {
  const lines = block.split('\n');
  const out = [];
  let list = null;
  const flushList = () => {
    if (list) {
      out.push('<' + list.tag + '>' + list.items.join('') + '</' + list.tag + '>');
      list = null;
    }
  };
  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) {
      flushList();
      continue;
    }
    const h = /^(#{1,6})\s+(.*)$/.exec(line);
    if (h) {
      flushList();
      const level = Math.min(h[1].length + 2, 6);
      out.push('<h' + level + '>' + inline(h[2]) + '</h' + level + '>');
      continue;
    }
    const ul = /^[-*·]\s+(.*)$/.exec(line);
    if (ul) {
      if (!list || list.tag !== 'ul') {
        flushList();
        list = { tag: 'ul', items: [] };
      }
      list.items.push('<li>' + inline(ul[1]) + '</li>');
      continue;
    }
    const ol = /^\d+[.)]\s+(.*)$/.exec(line);
    if (ol) {
      if (!list || list.tag !== 'ol') {
        flushList();
        list = { tag: 'ol', items: [] };
      }
      list.items.push('<li>' + inline(ol[1]) + '</li>');
      continue;
    }
    flushList();
    if (/^>\s?/.test(line)) out.push('<blockquote>' + inline(line.replace(/^>\s?/, '')) + '</blockquote>');
    else out.push('<p>' + inline(line) + '</p>');
  }
  flushList();
  return out.join('');
}

export function mdToHtml(src) {
  if (!src) return '';
  let text = String(src).replace(/\r\n/g, '\n');
  const fences = (text.match(/```/g) || []).length;
  if (fences % 2 === 1) text += '\n```';

  const blocks = [];
  text = text.replace(/```([^\n`]*)\n([\s\S]*?)```/g, (m, lang, code) => {
    const label = (lang || '').trim() || 'text';
    blocks.push(
      '<pre class="code"><span class="code-lang">' +
        esc(label) +
        '</span><button class="code-copy" type="button" data-copy="' +
        esc(code) +
        '">复制</button><code>' +
        esc(code.replace(/\n$/, '')) +
        '</code></pre>'
    );
    return '\u0000B' + (blocks.length - 1) + '\u0000';
  });

  const parts = text.split(/\n{2,}/);
  let html = parts
    .map((p) => (p.indexOf('\u0000B') === 0 ? p : renderPlainBlock(esc(p))))
    .join('');

  html = html.replace(/\u0000B(\d+)\u0000/g, (m, i) => blocks[Number(i)] || '');
  return html;
}

export function plainText(md) {
  return String(md || '')
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/[#>*`_\-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function snippet(text, n) {
  const t = plainText(text);
  return t.length > n ? t.slice(0, n) + '…' : t;
}

export function copyText(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(text);
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.opacity = '0';
  document.body.appendChild(ta);
  ta.select();
  try {
    document.execCommand('copy');
  } catch (e) {
    /* ignore */
  }
  document.body.removeChild(ta);
  return Promise.resolve();
}

export function download(name, content, type) {
  const blob = new Blob([content], { type: type || 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
