/**
 * 构建：把静态资源复制到 dist/。
 * 不引入任何依赖，只用到 Node 内置模块。
 */
import { rm, mkdir, cp, readdir, stat } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const dist = path.join(root, 'dist');

const ENTRIES = ['index.html', 'src'];

async function main() {
  await rm(dist, { recursive: true, force: true });
  await mkdir(dist, { recursive: true });

  for (const entry of ENTRIES) {
    const from = path.join(root, entry);
    if (!existsSync(from)) throw new Error('缺少构建入口：' + entry);
    await cp(from, path.join(dist, entry), { recursive: true });
  }

  const files = await walk(dist);
  const total = files.reduce((sum, f) => sum + f.size, 0);
  console.log('✔ 构建完成 → dist/');
  console.log('  文件数：' + files.length + '，体积：' + (total / 1024).toFixed(1) + ' KB');
  for (const f of files.slice(0, 20)) {
    console.log('  · ' + path.relative(dist, f.path) + '  ' + (f.size / 1024).toFixed(1) + ' KB');
  }
}

async function walk(dir, acc) {
  const out = acc || [];
  const items = await readdir(dir, { withFileTypes: true });
  for (const item of items) {
    const full = path.join(dir, item.name);
    if (item.isDirectory()) await walk(full, out);
    else {
      const s = await stat(full);
      out.push({ path: full, size: s.size });
    }
  }
  return out;
}

main().catch((err) => {
  console.error('✘ 构建失败：' + err.message);
  process.exit(1);
});
