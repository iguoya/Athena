import type { Place } from "@/content/types";

export type PlaceGlyphKind =
  | "capital"
  | "metropolis"
  | "prefecture"
  | "pass"
  | "port"
  | "other";

export function isPortPlace(place: Place): boolean {
  const blob = `${place.id} ${place.modern} ${place.role ?? ""}`;
  // 不含裸「渡」（避免「南渡」误判）；港/渡口/口岸等才算港口符号
  return /港|渡口|要渡|津渡|渡江|口岸|商埠|刺桐/.test(blob);
}

export function placeGlyphKind(place: Place): PlaceGlyphKind {
  if (isPortPlace(place)) return "port";
  switch (place.tier) {
    case "capital":
      return "capital";
    case "metropolis":
      return "metropolis";
    case "pass":
      return "pass";
    case "prefecture":
      return "prefecture";
    default:
      return "other";
  }
}

export const PLACE_GLYPH_LEGEND: Array<{
  kind: PlaceGlyphKind;
  label: string;
}> = [
  { kind: "capital", label: "都城" },
  { kind: "metropolis", label: "重镇" },
  { kind: "prefecture", label: "府州" },
  { kind: "pass", label: "关隘" },
  { kind: "port", label: "港口/渡口" },
  { kind: "other", label: "其他" },
];

/** 小符号：都城回字、重镇实方、府州空心圆、关隘三角、港口锚 */
export function PlaceGlyph({
  kind,
  active,
  alive,
}: {
  kind: PlaceGlyphKind;
  active?: boolean;
  /** 当年份名字存续：实；否则虚淡 */
  alive?: boolean;
}) {
  const stroke = active ? "#c2410c" : "#2a2118";
  const fill = active ? "#c2410c" : "#5c4a32";
  const opacity = alive === false ? 0.35 : 1;
  const dash = alive === false ? "2 1.5" : undefined;

  const common = {
    width: 14,
    height: 14,
    className: "pointer-events-none drop-shadow-sm",
    style: { opacity },
  } as const;

  if (kind === "capital") {
    return (
      <svg {...common} viewBox="0 0 14 14" aria-hidden>
        <rect
          x="1.5"
          y="1.5"
          width="11"
          height="11"
          fill="none"
          stroke={stroke}
          strokeWidth="1.4"
          strokeDasharray={dash}
        />
        <rect
          x="4.2"
          y="4.2"
          width="5.6"
          height="5.6"
          fill={fill}
          stroke="none"
          opacity={alive === false ? 0.45 : 1}
        />
      </svg>
    );
  }
  if (kind === "metropolis") {
    return (
      <svg {...common} viewBox="0 0 14 14" aria-hidden>
        <rect
          x="2.5"
          y="2.5"
          width="9"
          height="9"
          fill={alive === false ? "none" : fill}
          stroke={stroke}
          strokeWidth="1.3"
          strokeDasharray={dash}
        />
      </svg>
    );
  }
  if (kind === "pass") {
    return (
      <svg {...common} viewBox="0 0 14 14" aria-hidden>
        <path
          d="M7 1.8 L12.2 12.2 H1.8 Z"
          fill={alive === false ? "none" : fill}
          stroke={stroke}
          strokeWidth="1.2"
          strokeLinejoin="round"
          strokeDasharray={dash}
        />
      </svg>
    );
  }
  if (kind === "port") {
    return (
      <svg {...common} viewBox="0 0 14 14" aria-hidden>
        <path
          d="M7 1.5 V8.5 M4.2 5.2 H9.8 M3.2 11.2 Q7 8.8 10.8 11.2"
          fill="none"
          stroke={stroke}
          strokeWidth="1.35"
          strokeLinecap="round"
          strokeDasharray={dash}
        />
        <circle cx="7" cy="3.2" r="1.2" fill={fill} opacity={alive === false ? 0.4 : 1} />
      </svg>
    );
  }
  if (kind === "prefecture") {
    return (
      <svg {...common} viewBox="0 0 14 14" aria-hidden>
        <circle
          cx="7"
          cy="7"
          r="4.2"
          fill="none"
          stroke={stroke}
          strokeWidth="1.35"
          strokeDasharray={dash}
        />
      </svg>
    );
  }
  return (
    <svg {...common} viewBox="0 0 14 14" aria-hidden>
      <circle
        cx="7"
        cy="7"
        r="2.6"
        fill={alive === false ? "none" : fill}
        stroke={stroke}
        strokeWidth="1.1"
        strokeDasharray={dash}
      />
    </svg>
  );
}
