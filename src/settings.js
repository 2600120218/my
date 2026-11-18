import {
  state,
  setSetting,
  addKey,
  removeKey,
  setActiveKey,
  maskKey,
  buildExport,
  applyImport,
  DEFAULT_SETTINGS,
  envKey,
} from './store.js';
import { esc, download, b64decode, debounce } from './utils.js';
import { openModal, closeModal, showToast, confirmDialog, renderAll } from './render.js';
import { PRICING } from './pricing.js';

let modalEl = null;

/** 打开设置页；section 可选 'keys'，会滚动到密钥区 */
export function openSettings(section) {
  modalEl = openModal(settingsHtml(), { wide: true });
  if (!modalEl) return;
  try {
    bind(modalEl);
  } catch (err) {
    console.error('[settings] 绑定失败', err);
    showToast('设置页初始化失败：' + ((err && err.message) || err));
  }
  if (section === 'keys') {
    const box = modalEl.querySelector('#set-keys');
    if (box) setTimeout(() => box.scrollIntoView({ block: 'start' }), 30);
  }
}

function settingsHtml() {
  const s = state.settings;
  return (
    '<div class="modal-head"><h3>设置</h3><button class="icon-btn" id="settings-close" type="button" aria-label="关闭">✕</button></div>' +
    '<div class="modal-body settings-body">' +

    /* 模型参数 */
    '<section class="set-section">' +
    '<div class="set-title">模型参数</div>' +
    slider('temperature', '温度（Temperature）', s.temperature, 0, 2, 0.05, '控制创造性，越高越有想象力') +
    slider('topP', 'Top P', s.topP, 0, 1, 0.01, '控制词汇多样性，越高越丰富') +
    '<div class="set-note">这两个值只由你手动修改，系统不会自动调整。</div>' +
    '</section>' +

    /* 系统提示词 */
    '<section class="set-section">' +
    '<div class="set-title">系统提示词</div>' +
    '<textarea class="text-area" id="system-prompt" rows="5" placeholder="' + esc(DEFAULT_SETTINGS.systemPrompt) + '">' + esc(s.systemPrompt) + '</textarea>' +
    '<div class="set-row-end"><button class="btn ghost" id="reset-prompt" type="button">恢复默认</button>' +
    '<span class="set-note">只对之后发送的消息生效</span></div>' +
    '</section>' +

    /* 对话 */
    '<section class="set-section">' +
    '<div class="set-title">对话</div>' +
    '<label class="set-row"><span>上下文的消息数量上限</span>' +
    '<input class="num-input" id="context-limit" type="number" min="2" max="100" step="1" value="' + s.contextLimit + '" /></label>' +
    '<label class="set-row"><span>每 25 步暂停确认</span>' +
    '<input id="pause-25" type="checkbox" class="switch"' + (s.pauseEvery25 ? ' checked' : '') + ' /></label>' +
    '<div class="set-note">开启后每连续对话 25 轮会弹窗确认一次，避免误触消耗额度。</div>' +
    '</section>' +

    /* 密钥 */
    '<section class="set-section" id="set-keys">' +
    '<div class="set-title">密钥管理</div>' +
    '<div class="set-hint">密钥只保存在本机 localStorage（Base64 编码），不会上传、不会写入源码，也不会随导出文件带走。</div>' +
    (envKey()
      ? '<div class="env-badge">已检测到环境变量 DEEPSEEK_API_KEY（仅本地预览由 dev server 注入，线上不会存在）</div>'
      : '') +
    '<div class="key-form">' +
    '<input class="text-input" id="key-name" maxlength="20" placeholder="名称，如 主密钥 / 备用" autocomplete="off" />' +
    '<input class="text-input" id="key-value" type="password" placeholder="sk-...（粘贴后回车即可保存）" autocomplete="off" spellcheck="false" />' +
    '<button class="btn primary" id="key-save" type="button">保存密钥</button>' +
    '</div>' +
    keyListHtml() +
    '</section>' +

    /* 导入导出 */
    '<section class="set-section">' +
    '<div class="set-title">历史记录</div>' +
    '<div class="set-hint">导出的 .json 包含全部对话（含系统提示词、温度等参数与密钥名称），可经 AirDrop / 微信 / 邮件传输。</div>' +
    '<div class="set-row-btns">' +
    '<button class="btn" id="export-history" type="button">导出历史</button>' +
    '<button class="btn" id="import-history" type="button">导入历史</button>' +
    '<input type="file" id="import-file" accept=".json,application/json" hidden />' +
    '</div>' +
    '<div class="set-note">导入会替换当前全部对话，但不会覆盖本机的密钥与温度等设置。</div>' +
    '</section>' +

    /* 关于 */
    '<section class="set-section">' +
    '<div class="set-title">关于</div>' +
    '<div class="set-note">模型 deepseek-flash · 计费按空闲 $' + PRICING.perMillion.input + '/M 输入、$' +
    PRICING.perMillion.output + '/M 输出、缓存命中 $' + PRICING.perMillion.cacheInput + '/M，高峰翻倍，汇率 ' + PRICING.fx + '。</div>' +
    '</section>' +

    '</div>'
  );
}

function slider(id, label, value, min, max, step, hint) {
  return (
    '<div class="slider-block">' +
    '<div class="slider-head"><span>' + esc(label) + '</span><b id="' + id + '-val">' + Number(value).toFixed(2) + '</b></div>' +
    '<input class="range" id="' + id + '" type="range" min="' + min + '" max="' + max + '" step="' + step + '" value="' + value + '" />' +
    '<div class="set-note">' + esc(hint) + '</div>' +
    '</div>'
  );
}

function keyListHtml() {
  return '<div class="key-list" id="key-list">' + keyItemsHtml() + '</div>';
}

function keyItemsHtml() {
  if (!state.keys.length) {
    return '<div class="set-note">还没有保存任何密钥。' + (envKey() ? '当前使用环境变量中的密钥。' : '保存一个密钥后即可开始对话。') + '</div>';
  }
  return state.keys
    .map((k) => {
      const active = k.id === state.activeKeyId;
      return (
        '<div class="key-item' + (active ? ' active' : '') + '">' +
        '<button class="key-pick" type="button" data-key-action="use" data-id="' + k.id + '">' +
        '<span class="dot' + (active ? ' on' : '') + '"></span>' +
        '<span class="key-name">' + esc(k.name) + '</span>' +
        '<span class="key-mask">' + esc(maskKey(b64decode(k.value))) + '</span>' +
        '</button>' +
        '<button class="act danger" type="button" data-key-action="del" data-id="' + k.id + '">删除</button>' +
        '</div>'
      );
    })
    .join('');
}

/* ------------------------------ 事件绑定 ------------------------------ */

function bind(modal) {
  // 1. 关闭
  const closeBtn = modal.querySelector('#settings-close');
  if (closeBtn) closeBtn.addEventListener('click', () => closeSettings());

  // 2. 滑块
  bindSlider(modal, 'temperature', (v) => setSetting('temperature', v));
  bindSlider(modal, 'topP', (v) => setSetting('topP', v));

  // 3. 系统提示词
  const prompt = modal.querySelector('#system-prompt');
  if (prompt) {
    const persist = () => setSetting('systemPrompt', prompt.value);
    prompt.addEventListener('input', debounce(persist, 300));
    prompt.addEventListener('change', persist);
    prompt.addEventListener('blur', persist);
  }

  const resetBtn = modal.querySelector('#reset-prompt');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      const box = modal.querySelector('#system-prompt');
      if (box) box.value = DEFAULT_SETTINGS.systemPrompt;
      setSetting('systemPrompt', DEFAULT_SETTINGS.systemPrompt);
      showToast('已恢复默认系统提示词');
    });
  }

  // 4. 上下文条数 / 暂停确认
  const ctx = modal.querySelector('#context-limit');
  if (ctx) {
    ctx.addEventListener('change', () => {
      let v = Math.round(Number(ctx.value));
      if (!isFinite(v)) v = DEFAULT_SETTINGS.contextLimit;
      v = Math.min(100, Math.max(2, v));
      ctx.value = String(v);
      setSetting('contextLimit', v);
    });
  }

  const pause = modal.querySelector('#pause-25');
  if (pause) pause.addEventListener('change', () => setSetting('pauseEvery25', pause.checked));

  // 5. 密钥：直接绑定，不依赖事件委托
  const saveBtn = modal.querySelector('#key-save');
  const keyValueInput = modal.querySelector('#key-value');
  const keyNameInput = modal.querySelector('#key-name');

  const doSave = () => saveKey(modal, keyNameInput, keyValueInput);
  if (saveBtn) saveBtn.addEventListener('click', doSave);
  if (keyValueInput) {
    keyValueInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        doSave();
      }
    });
  }

  bindKeyList(modal);

  // 6. 导入 / 导出
  const exportBtn = modal.querySelector('#export-history');
  if (exportBtn) {
    exportBtn.addEventListener('click', () => {
      const data = buildExport();
      const name = 'deepseek-history-' + new Date().toISOString().slice(0, 10) + '.json';
      download(name, JSON.stringify(data, null, 2));
      showToast('已导出 ' + data.threads.length + ' 个对话');
    });
  }

  const fileInput = modal.querySelector('#import-file');
  const importBtn = modal.querySelector('#import-history');
  if (importBtn && fileInput) importBtn.addEventListener('click', () => fileInput.click());

  if (fileInput) {
    fileInput.addEventListener('change', () => {
      const file = fileInput.files && fileInput.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const data = JSON.parse(String(reader.result || '{}'));
          const count = applyImport(data);
          renderAll();
          showToast('已导入 ' + count + ' 个对话');
          closeSettings();
        } catch (err) {
          showToast('导入失败：' + (err && err.message ? err.message : '文件无法解析'));
        }
      };
      reader.onerror = () => showToast('读取文件失败');
      reader.readAsText(file);
      fileInput.value = '';
    });
  }
}

function bindSlider(modal, id, onValue) {
  const input = modal.querySelector('#' + id);
  const label = modal.querySelector('#' + id + '-val');
  if (!input) return;
  input.addEventListener('input', () => {
    const v = Math.round(Number(input.value) * 100) / 100;
    if (label) label.textContent = v.toFixed(2);
    onValue(v);
  });
}

function saveKey(modal, nameInput, valueInput) {
  const raw = valueInput ? String(valueInput.value || '') : '';
  // 从聊天窗口/文档里粘贴常带空格、换行、引号，这里统一清洗
  const value = raw.replace(/\s+/g, '').replace(/^["']|["']$/g, '').replace(/^Bearer/i, '').trim();
  if (!value) {
    showToast('请先输入 API Key');
    if (valueInput) valueInput.focus();
    return;
  }
  if (value.length < 12) {
    showToast('API Key 长度不对，请检查是否复制完整');
    return;
  }
  const name = nameInput ? String(nameInput.value || '').trim() : '';
  const key = addKey(name || '密钥 ' + (state.keys.length + 1), value);
  setActiveKey(key.id);
  if (valueInput) valueInput.value = '';
  if (nameInput) nameInput.value = '';
  refreshKeys(modal);
  const hint = modal.querySelector('#key-list');
  if (hint) hint.scrollIntoView({ block: 'nearest' });
  showToast('密钥「' + key.name + '」已保存到本机');
}

function bindKeyList(modal) {
  const list = modal.querySelector('#key-list');
  if (!list) return;
  list.querySelectorAll('[data-key-action]').forEach((btn) => {
    btn.addEventListener('click', async () => {
      const action = btn.getAttribute('data-key-action');
      const id = btn.getAttribute('data-id');
      if (action === 'use') {
        setActiveKey(id);
        refreshKeys(modal);
        const k = state.keys.find((x) => x.id === id);
        showToast('已切换到「' + (k ? k.name : '') + '」');
        return;
      }
      if (action === 'del') {
        const target = state.keys.find((k) => k.id === id);
        const ok = await confirmDialog({
          title: '删除密钥',
          text: '确定删除「' + (target ? target.name : '') + '」吗？该操作不可恢复。',
          okText: '删除',
        });
        if (!ok) return;
        removeKey(id);
        refreshKeys(modal);
        showToast('密钥已删除');
      }
    });
  });
}

function refreshKeys(modal) {
  const host = modal.querySelector('#key-list');
  if (!host) return;
  host.innerHTML = keyItemsHtml();
  bindKeyList(modal);
}

export function closeSettings() {
  const prompt = modalEl && modalEl.querySelector('#system-prompt');
  if (prompt) setSetting('systemPrompt', prompt.value);
  closeModal();
  modalEl = null;
}
