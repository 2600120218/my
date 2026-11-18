# 部署清单

> ⚠️ 本次会话里我这边的命令执行被环境禁止（`bash` / `pwsh` 全部 `spawn EPERM`），
> 所以 **打包、git 提交、推送、Pages 配置都没能由我执行**，下面每一步都请在你自己的终端跑。
> 代码已按"设置页可用 + 支持环境变量密钥"改好，见第 1 节。

---

## 0. 本次修复了什么

| 问题 | 修复 |
|---|---|
| 设置按钮点了没反应 | `boot()` 改成**先绑定事件再渲染**，渲染异常不再导致所有按钮集体失效；初始化包 try/catch，失败会以 toast 显示原因 |
| 设置页内容绑定脆弱 | 密钥区改为**直接 `addEventListener`**（不依赖事件委托），保存按钮 / 回车都能保存；滑块、开关、导入导出各自直连 |
| 本地数据脏导致白屏 | `loadAll()` 对 threads / cost / settings 做结构兜底 |
| 找不到在哪填 Key | 首页在未配置密钥时显示一条提示，点它直接打开设置；`?section=keys` 也会定位到密钥区 |
| 不想在 UI 里填 Key | dev server 支持 `DEEPSEEK_API_KEY` 环境变量注入（只进内存，不落盘、不进 dist） |

---

## 1. 本地验收

```bash
node scripts/serve.mjs          # http://127.0.0.1:5173
```

带环境变量（推荐，免手填）：

```powershell
# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-你的key"; node scripts/serve.mjs
```

```bash
# macOS / Linux
DEEPSEEK_API_KEY=sk-你的key node scripts/serve.mjs
```

启动日志会打印「已读取 DEEPSEEK_API_KEY（仅内存注入）」。此时设置页顶部会显示蓝色角标提示。
**这个注入只存在于 dev server 进程里**：`dist/` 产物、git 仓库、GitHub Pages 上都没有它。

验收清单：首页提示 → 点开设置 → 填 Key → 保存 → 回到对话发一条 → 侧边栏「费用」点开看数字 → 撤回/编辑/压缩。

---

## 2. 构建

```bash
node scripts/build.mjs        # 等价于 pnpm build
ls dist                       # index.html + src/
```

上线前自查（确认没有把密钥打进去）：

```bash
grep -r "sk-" dist/ || echo "干净：dist 中无密钥"
```

---

## 3. 初始化仓库并提交

```bash
git init
git add .
git commit -m "init"
git branch -M main
git grep -n "sk-" || echo "干净：源码中无密钥"
```

---

## 4. 推送到 GitHub

```bash
git remote add origin https://github.com/2600120218/my.git
git push -u origin main
```

> 用 PAT 推送：`git remote set-url origin https://<用户名>:<TOKEN>@github.com/2600120218/my.git`，
> 推完记得改回不带 token 的地址，避免 token 留在 `.git/config` 里。

---

## 5. 配置 GitHub Pages

仓库里已有 `.github/workflows/pages.yml`，推荐 Actions：

1. `https://github.com/2600120218/my/settings/pages`
2. **Build and deployment → Source** 选 **GitHub Actions**
3. 去 `https://github.com/2600120218/my/actions` 确认 workflow 变绿

备选（用 gh-pages 分支，把 dist 当发布源）：

```bash
pnpm build
cd dist && git init && git add -A && git commit -m "deploy"
git branch -M gh-pages
git push -f https://github.com/2600120218/my.git gh-pages
cd ..
```
然后 Pages → Source 选 **Deploy from a branch** → `gh-pages` → `/ (root)`。

---

## 6. 访问链接

```
https://2600120218.github.io/my/
```

手机浏览器直接打开即可（首屏就是对话页）。首次打开需要在设置页填一次 Key，
或者按第 7 节搭一个反代让 Key 留在服务端。

---

## 7. 关于"在 GitHub 仓库后台配置 API Key 密文"

### 先说结论（重要）

**纯静态的 GitHub Pages 站点无法安全读取 GitHub Secret。** 原因：

- GitHub Pages 只有 HTML/JS/CSS，**没有服务端**，浏览器拿不到 Secret；
- 唯一的"注入"办法是在 build 时写进 JS，但 Pages 是全公开的，任何人打开
  `https://2600120218.github.io/my/src/api.js` 都能看到你的 Key——
  这等于把 Key 公开，也违反"禁止写入源码/提交到仓库"。

所以：**GitHub Secret 本身没问题，但它必须配一个"服务端"来使用**。

### 7.1 配置 Secret（这一步正是你问的"后台配置密文"）

1. 打开 `https://github.com/2600120218/my/settings/secrets/actions`
2. **New repository secret**
3. Name：`DEEPSEEK_API_KEY`
4. Secret：粘贴 `sk-...`，**Save**

配置后它出现在 Actions 的 `secrets.DEEPSEEK_API_KEY`，只能在 workflow 里用，
不会出现在页面源码、日志里（Actions 会自动打码）。

### 7.2 让它真正生效：加一层 Cloudflare Worker 反代

Worker 免费额度够用，Key 存成 Worker 的加密环境变量，浏览器只认 Worker 域名。

`worker.js`：

```js
export default {
  async fetch(request, env) {
    const cors = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'content-type, authorization',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
    };
    if (request.method === 'OPTIONS') return new Response(null, { headers: cors });
    if (request.method !== 'POST') return new Response('Method Not Allowed', { status: 405, headers: cors });

    const upstream = await fetch('https://api.deepseek.com/chat/completions', {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        // 关键：用 Worker 里的密钥，忽略浏览器传来的 Authorization
        authorization: 'Bearer ' + env.DEEPSEEK_API_KEY,
      },
      body: request.body,
    });
    return new Response(upstream.body, {
      status: upstream.status,
      headers: { ...cors, 'content-type': upstream.headers.get('content-type') || 'text/event-stream' },
    });
  },
};
```

部署：

```bash
npm i -g wrangler
wrangler init deepseek-proxy      # 选 Worker
wrangler secret put DEEPSEEK_API_KEY   # 粘贴 sk-...，加密存储
wrangler deploy                    # 得到 https://deepseek-proxy.xxx.workers.dev
```

然后在这个网页应用里让它走 Worker（不用改代码）：

1. 打开站点，F12 控制台执行：
   ```js
   localStorage.setItem('ds.apiBase.v1', 'https://deepseek-proxy.xxx.workers.dev');
   location.reload();
   ```
2. 设置页随便存一个占位密钥（例如 `proxy`），只要不为空即可，真实 Key 在 Worker 里。
3. 想让所有访客默认走 Worker，就把 `src/api.js` 里的 `DEFAULT_BASE` 改成你的 Worker 地址再重新部署。

> 这套做法同样可以用 Vercel / Netlify Functions、阿里云函数计算等代替，
> 要点只有一个：**Key 只存在服务端的加密环境变量里，永远不进浏览器。**

---

## 8. 上线后另外两个常见问题

### 8.1 浏览器直连被 CORS 拦

不做反代时，页面直接 fetch `api.deepseek.com` 可能被浏览器拦（`blocked by CORS policy`）。
按 7.2 搭反代即可，或用第 7.2 节的两行控制台命令切换到自己的反代。

### 8.2 模型名 / 开关字段名

- 模型固定 `deepseek-flash`（`src/api.js` 的 `MODEL_CHAT`）。若返回 `model not found`，改成 `deepseek-chat` 或 `deepseek-reasoner`，只改这一处。
- 深度思考 / 联网搜索在 `applyToggles()` 里（只在开启时附带）：
  ```js
  body.thinking   = { type: 'enabled' }
  body.web_search = { enable: true }
  ```
  网关字段名不同就只改这个函数。两个开关互相独立，代码里没有任何自动开关路径。

---

## 9. 安全提醒

- 源码、`dist/`、仓库里**没有任何 API Key**；`.gitignore` 已排除 `.env`、`*.key`、`secrets.json`。
- 密钥只在浏览器 `localStorage`（Base64 编码），换设备各自存；导出的 JSON 不含 Key（只含密钥名称）。
- 这是纯前端应用：任何能打开页面的人都需要自己填 Key，或由你的反代代为持有。
- 一旦怀疑泄露，立即在 DeepSeek 控制台吊销，并检查仓库历史里是否出现过 `sk-`。
