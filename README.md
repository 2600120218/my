# DeepSeek 移动端对话客户端

基于 DeepSeek 官方 chat-demo 的交互与视觉风格重写的静态单页应用（零依赖、无构建工具链）。

## 功能

- **对话**：流式输出、深度思考内容折叠展示、代码块复制、停止生成
- **模型**：`deepseek-flash`；深度思考 / 联网搜索两个开关完全独立，只由用户手动切换
- **可编辑会话**：任意轮次撤回、编辑任意消息（含助手回复）后重新生成
- **历史压缩**：手动点击「压缩历史」，调用 `deepseek-chat` 生成 200~300 字摘要；本地完整记录保留，发送给模型的内容只有摘要 + 最近 5 轮
- **侧边栏**：按 置顶 / 今天 / 7天内 / 30天内 / 月份 分组，搜索、置顶、重命名、删除、新建
- **设置页**：温度（0~2，步长 0.05，默认 0.85）、Top P（0~1，步长 0.01，默认 0.95）、系统提示词、上下文消息条数上限、每 25 步暂停确认、多密钥管理、导入/导出历史
- **费用**：侧边栏中默认只显示「费用」二字，点击展开今日总消耗（精确到分）、请求次数、token 明细，每日凌晨自动归零
- **数据**：全部保存在浏览器 `localStorage`，切换对话不丢失

## 本地运行

```bash
node scripts/serve.mjs                       # 手动在设置页填 Key
DEEPSEEK_API_KEY=sk-xxx node scripts/serve.mjs   # 或从环境变量注入（macOS/Linux）
```

Windows PowerShell：

```powershell
$env:DEEPSEEK_API_KEY="sk-xxx"; node scripts/serve.mjs
```

环境变量只在 dev server 进程内存里注入到页面，不写文件、不进 `dist/`。

打开 <http://127.0.0.1:5173>；`http://127.0.0.1:5173/?section=keys` 会直接定位到密钥设置区。

## 构建

```bash
pnpm build                    # 产物在 dist/
pnpm preview                  # 预览 dist/
```

## 部署

见 [DEPLOY.md](./DEPLOY.md)。

## 密钥安全

API Key 只在浏览器里输入，Base64 编码后存进本机 `localStorage`，不会写入源码、不会提交到仓库，
导出的历史 JSON 里也不含 Key（只有密钥名称）。
