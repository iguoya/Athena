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
  const builtApp = join(
    root,
    "src-tauri/target/release/bundle/macos/athena-english.app",
  );
  if (!existsSync(builtApp)) {
    console.error(
      "找不到 macOS app bundle，请先成功执行 npm run tauri -- build。\n" +
        `预期位置：${builtApp}`,
    );
    process.exit(1);
  }

  const destApp = join(binDir, "athena-english.app");
  rmSync(destApp, { recursive: true, force: true });
  cpSync(builtApp, destApp, { recursive: true });
  chmodSync(join(destApp, "Contents/MacOS/athena-english"), 0o755);
  installed = destApp;
} else {
  const candidates = [
    join(root, "src-tauri/target/release/athena-english"),
    join(root, "src-tauri/target/release/athena-english.exe"),
  ];
  const built = candidates.find((path) => existsSync(path));
  if (!built) {
    console.error("找不到 tauri build 产物，请先成功执行 npm run tauri -- build");
    process.exit(1);
  }

  const destBin = join(binDir, "athena-english.bin");
  copyFileSync(built, destBin);
  chmodSync(destBin, 0o755);
  installed = destBin;
}

const launcher = `#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export ATHENA_ENGLISH_ROOT="$ROOT"

if [[ "$(uname -s)" == "Darwin" ]]; then
  TARGET="$ROOT/bin/athena-english.app/Contents/MacOS/athena-english"
else
  TARGET="$ROOT/bin/athena-english.bin"
fi

if [[ ! -x "$TARGET" ]]; then
  echo "英语自学应用尚未构建：$TARGET" >&2
  echo "请在 $ROOT 执行 npm run build:app" >&2
  exit 1
fi

exec "$TARGET" "$@"
`;
writeFileSync(join(binDir, "athena-english"), launcher, { mode: 0o755 });
chmodSync(join(binDir, "athena-english"), 0o755);
console.log("已安装:", installed);
