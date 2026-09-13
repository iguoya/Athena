import {
  chmodSync,
  copyFileSync,
  cpSync,
  existsSync,
  mkdirSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const binDir = join(root, "bin");
mkdirSync(binDir, { recursive: true });

let installed;

if (process.platform === "darwin") {
  // macOS 的 WKWebView 需要完整的 app bundle 上下文。只复制
  // target/release/athena-math 这个 Mach-O 会得到一个能开窗但不加载页面的白屏程序。
  const builtApp = join(
    root,
    "src-tauri/target/release/bundle/macos/athena-math.app",
  );
  if (!existsSync(builtApp)) {
    console.error(
      "找不到 macOS app bundle，请先成功执行 npm run tauri -- build。\n" +
        `预期位置：${builtApp}`,
    );
    process.exit(1);
  }

  const destApp = join(binDir, "athena-math.app");
  rmSync(destApp, { recursive: true, force: true });
  cpSync(builtApp, destApp, { recursive: true });
  chmodSync(join(destApp, "Contents/MacOS/athena-math"), 0o755);
  installed = destApp;
} else {
  const candidates = [
    join(root, "src-tauri/target/release/athena-math"),
    join(root, "src-tauri/target/release/athena-math.exe"),
  ];
  const built = candidates.find((path) => existsSync(path));
  if (!built) {
    console.error("找不到 tauri build 产物，请先成功执行 npm run tauri -- build");
    process.exit(1);
  }

  const destBin = join(binDir, "athena-math.bin");
  copyFileSync(built, destBin);
  chmodSync(destBin, 0o755);
  installed = destBin;
}

// 覆盖入口为转发脚本（若尚不是脚本，保留 .bin 真身）
const launcher = `#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export ATHENA_MATH_ROOT="$ROOT"

if [[ "$(uname -s)" == "Darwin" ]]; then
  TARGET="$ROOT/bin/athena-math.app/Contents/MacOS/athena-math"
else
  TARGET="$ROOT/bin/athena-math.bin"
fi

if [[ ! -x "$TARGET" ]]; then
  echo "数学学习应用尚未构建：$TARGET" >&2
  echo "请在 $ROOT 执行 npm run build:app" >&2
  exit 1
fi

exec "$TARGET" "$@"
`;
writeFileSync(join(binDir, "athena-math"), launcher, { mode: 0o755 });
chmodSync(join(binDir, "athena-math"), 0o755);
console.log("已安装:", installed);
