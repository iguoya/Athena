import { motion, useReducedMotion } from "motion/react";

const blobs = [
  { color: "var(--blob-a)", size: 380, style: { top: -120, right: "8%" }, drift: { x: -40, y: 30 }, duration: 18 },
  { color: "var(--blob-b)", size: 420, style: { bottom: -160, left: "20%" }, drift: { x: 36, y: -24 }, duration: 22 },
  { color: "var(--blob-c)", size: 260, style: { top: "38%", right: -60 }, drift: { x: -28, y: 34 }, duration: 26 },
];

// Soft drifting colour blobs behind the glass panels; the journal skin sets them transparent.
export function Backdrop() {
  const reduce = useReducedMotion();
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      {blobs.map((b, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full opacity-70 blur-[60px] [:root[data-style=night]_&]:opacity-55"
          style={{ ...b.style, width: b.size, height: b.size, background: b.color }}
          animate={reduce ? undefined : { x: b.drift.x, y: b.drift.y, scale: 1.12 }}
          transition={{ duration: b.duration, repeat: Infinity, repeatType: "mirror", ease: "easeInOut" }}
        />
      ))}
    </div>
  );
}
