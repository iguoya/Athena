import { atmosphereLayers, data, interiorLayers } from "../content/load";
import { useEarth } from "../state/store";

/** 层列表：大气自外而内、地球内部自地表向下。点击选中，详情见 LayerDetail。 */
export function LayerList() {
  const selectedLayerId = useEarth((s) => s.selectedLayerId);
  const select = useEarth((s) => s.select);

  const renderItem = (args: {
    id: string;
    name: string;
    colorHint: string;
    range: string;
  }) => (
    <button
      key={args.id}
      onClick={() => select(args.id === selectedLayerId ? null : args.id)}
      className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors ${
        args.id === selectedLayerId
          ? "bg-sky-100 text-sky-900 ring-1 ring-sky-300"
          : "hover:bg-slate-100 text-slate-700"
      }`}
    >
      <span
        className="inline-block h-2.5 w-2.5 shrink-0 rounded-full"
        style={{ backgroundColor: args.colorHint }}
      />
      <span className="font-medium">{args.name}</span>
      <span className="ml-auto text-xs text-slate-400 tabular-nums">{args.range}</span>
    </button>
  );

  return (
    <div className="space-y-3">
      <section>
        <h3 className="mb-1 text-xs font-semibold tracking-wide text-slate-400">大气（自外而内）</h3>
        <div className="space-y-0.5">
          {[...atmosphereLayers].reverse().map((layer) =>
            renderItem({
              id: layer.id,
              name: layer.name,
              colorHint: layer.colorHint,
              range:
                layer.topHeightKm === null
                  ? `${layer.bottomHeightKm} km ↗ 渐隐`
                  : `${layer.bottomHeightKm}–${layer.topHeightKm} km`,
            }),
          )}
        </div>
      </section>
      <section>
        <h3 className="mb-1 text-xs font-semibold tracking-wide text-slate-400">地球内部（自地表向下）</h3>
        <div className="space-y-0.5">
          {interiorLayers.map((layer) =>
            renderItem({
              id: layer.id,
              name: layer.name,
              colorHint: layer.colorHint,
              range: `${layer.topDepthKm}–${layer.bottomDepthKm} km 深`,
            }),
          )}
        </div>
      </section>
      <p className="text-xs leading-relaxed text-slate-400">
        {data.meta.disclaimers[1]}
      </p>
    </div>
  );
}
