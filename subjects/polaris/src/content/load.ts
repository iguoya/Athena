import polaris from "@content/polaris.json";
import sourceFile from "@content/sources/catalog.json";
import { buildCatalog, type Catalog } from "./catalog";
import type { PolarisDocument, Source } from "./types";

// 内容在应用根目录的 content/ 里，是唯一来源；这里只做形状断言，校验归 scripts/contract.py。
export function loadCatalog(): Catalog {
  return buildCatalog(polaris as unknown as PolarisDocument, sourceFile.sources as Source[]);
}
