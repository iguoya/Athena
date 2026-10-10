import {
  atmosphereLayers,
  interiorLayers,
  sourceTitle,
  sourceUrl,
} from "../content/load";
import { openExternal } from "../ui/external";
import { useEarth } from "../state/store";

/** 选中层的详情：范围、描述、地壳的大陆/大洋两套厚度、可点击的出处。 */
export function LayerDetail() {
  const selectedLayerId = useEarth((s) => s.selectedLayerId);
  const select = useEarth((s) => s.select);
  if (!selectedLayerId) return null;

  const interior = interiorLayers.find((l) => l.id === selectedLayerId);
  const atmosphere = atmosphereLayers.find((l) => l.id === selectedLayerId);
  if (!interior && !atmosphere) return null;
  const sourceIds = (interior ?? atmosphere)!.sourceIds;

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
      <div className="mb-1 flex items-start justify-between gap-2">
        <h4 className="text-base font-semibold text-slate-800">
          {(interior ?? atmosphere)!.name}
          <span className="ml-2 text-xs font-normal text-slate-400">
            {(interior ?? atmosphere)!.english}
          </span>
        </h4>
        <button
          onClick={() => select(null)}
          className="rounded px-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          aria-label="关闭详情"
        >
          ✕
        </button>
      </div>
      <p className="mb-2 text-xs text-slate-500">
        {interior
          ? `深度 ${interior.topDepthKm}–${interior.bottomDepthKm} km（厚度约 ${
              interior.bottomDepthKm - interior.topDepthKm
            } km）`
          : atmosphere!.topHeightKm === null
            ? `高度 ${atmosphere!.bottomHeightKm} km 以上（上界不封闭，${atmosphere!.topHeightNote}）`
            : `高度 ${atmosphere!.bottomHeightKm}–${atmosphere!.topHeightKm} km${
                atmosphere!.topHeightNote ? `（${atmosphere!.topHeightNote}）` : ""
              }`}
      </p>
      {interior?.bottomDepthKmOceanic != null && (
        <p className="mb-2 rounded bg-amber-50 px-2 py-1 text-xs text-amber-800">
          地壳厚度分两套：大陆典型 {interior.bottomDepthKmContinental} km（范围{" "}
          {interior.bottomDepthRangeKm?.join("–")} km），大洋典型 {interior.bottomDepthKmOceanic}{" "}
          km——「35 km」只是大陆印象值。
        </p>
      )}
      <p className="leading-relaxed text-slate-700">{(interior ?? atmosphere)!.description}</p>
      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1">
        {sourceIds.map((id) => (
          <button
            key={id}
            onClick={() => {
              const url = sourceUrl(id);
              if (url) void openExternal(url);
            }}
            className="text-xs text-sky-600 underline decoration-dotted hover:text-sky-800"
            title={sourceTitle(id)}
          >
            出处：{id}
          </button>
        ))}
      </div>
    </div>
  );
}
