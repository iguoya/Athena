import { loadCatalog } from "./content/load";

const catalog = loadCatalog();

// 脚手架：证明内容能被直接导入。界面在后续提交里重写。
export function App() {
  return (
    <main style={{ padding: 32, fontFamily: "system-ui" }}>
      <h1>{catalog.title}</h1>
      <p>{catalog.subtitle}</p>
      <p>
        开放 {catalog.maps.length} 张图，共 {catalog.nodeById.size} 个节点（参考层 {catalog.allMaps.length - catalog.maps.length} 张图未开放）。
      </p>
    </main>
  );
}
