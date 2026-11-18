/**
 * 本地预览服务器（可选：从环境变量注入 API Key）
 *
 *   Windows PowerShell:  $env:DEEPSEEK_API_KEY="sk-xxx"; node scripts/serve.mjs
 *   macOS / Linux:       DEEPSEEK_API_KEY=sk-xxx node scripts/serve.mjs
 *
 * 注意：密钥只在内存里，通过 /index.html 的 window.DS_ENV 注入给浏览器，
 *      不会写入任何文件，也不会进入 dist/ 或 git 仓库。
 */
import http from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import path from 'node:path';

const root = path.resolve(process.argv[2] || '.');
const port = Number(process.argv[3] || 5173);
const envApiKey = String(process.env.DEEPSEEK_API_KEY || '').trim();

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
};

function injectEnv(html) {
  if (!envApiKey) return html;
  const payload = JSON.stringify({ apiKey: envApiKey }).replace(/</g, '\\u003c');
  const tag = '<script>window.DS_ENV=' + payload + ';</script>\n    <script type="module"';
  return html.replace('<script type="module"', tag);
}

const server = http.createServer(async (req, res) => {
  try {
    const url = decodeURIComponent((req.url || '/').split('?')[0]);
    let file = path.join(root, url === '/' ? 'index.html' : url);
    if (!file.startsWith(root)) {
      res.writeHead(403);
      return res.end('Forbidden');
    }
    let info = await stat(file).catch(() => null);
    if (info && info.isDirectory()) {
      file = path.join(file, 'index.html');
      info = await stat(file).catch(() => null);
    }
    if (!info) {
      res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
      return res.end('404 Not Found: ' + url);
    }

    let data = await readFile(file);
    if (path.extname(file).toLowerCase() === '.html') {
      data = Buffer.from(injectEnv(data.toString('utf8')), 'utf8');
    }

    res.writeHead(200, {
      'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream',
      'Cache-Control': 'no-store',
    });
    res.end(data);
  } catch (err) {
    res.writeHead(500);
    res.end(String(err && err.message));
  }
});

server.listen(port, () => {
  console.log('预览地址： http://127.0.0.1:' + port + '/');
  console.log('根目录：   ' + root);
  console.log('环境变量： ' + (envApiKey ? '已读取 DEEPSEEK_API_KEY（仅内存注入）' : '未设置 DEEPSEEK_API_KEY（可在设置页手动填写）'));
});
