/**
 * 用 resvg 把 icon.svg 渲成 app.json icon.renders 里的位图（启动器不可用时的本机兜底）。
 */
import { Resvg } from "@resvg/resvg-js";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import pngToIco from "png-to-ico";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const svg = readFileSync(join(root, "icon.svg"));

function png(size) {
  const r = new Resvg(svg, {
    fitTo: { mode: "width", value: size },
  });
  return r.render().asPng();
}

const outs = [
  ["src-tauri/icons/32x32.png", 32],
  ["src-tauri/icons/128x128.png", 128],
  ["src-tauri/icons/128x128@2x.png", 256],
  ["src-tauri/icons/icon.png", 512],
  ["src-tauri/icons/StoreLogo.png", 50],
  ["src-tauri/icons/Square30x30Logo.png", 30],
  ["src-tauri/icons/Square44x44Logo.png", 44],
  ["src-tauri/icons/Square71x71Logo.png", 71],
  ["src-tauri/icons/Square89x89Logo.png", 89],
  ["src-tauri/icons/Square107x107Logo.png", 107],
  ["src-tauri/icons/Square142x142Logo.png", 142],
  ["src-tauri/icons/Square150x150Logo.png", 150],
  ["src-tauri/icons/Square284x284Logo.png", 284],
  ["src-tauri/icons/Square310x310Logo.png", 310],
];

for (const [rel, size] of outs) {
  const path = join(root, rel);
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, png(size));
  console.log("wrote", rel);
}

const icoBuf = await pngToIco([
  png(16),
  png(32),
  png(48),
  png(64),
  png(128),
  png(256),
]);
writeFileSync(join(root, "src-tauri/icons/icon.ico"), icoBuf);
console.log("wrote src-tauri/icons/icon.ico");

// icns：Windows 开发可暂留旧文件；有 png2icons 再补。提示即可。
console.log("done (icns: keep existing or run launcher icons on macOS)");
