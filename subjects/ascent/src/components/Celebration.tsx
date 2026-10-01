import { motion, AnimatePresence } from "motion/react";

const COLORS = ["var(--accent)", "var(--accent-2)", "var(--blob-c)", "#f7d06b"];

// A short confetti burst when the day's required steps are all done.
export function Celebration({ show, message }: { show: boolean; message: string }) {
  const pieces = Array.from({ length: 36 }, (_, i) => {
    const angle = (i / 36) * Math.PI * 2;
    const dist = 140 + (i % 5) * 36;
    return {
      x: Math.cos(angle) * dist,
      y: Math.sin(angle) * dist - 60,
      rotate: (i * 47) % 360,
      color: COLORS[i % COLORS.length],
    };
  });
  return (
    <AnimatePresence>
      {show && (
        <motion.div
          className="pointer-events-none fixed inset-0 z-40 grid place-items-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {pieces.map((p, i) => (
            <motion.span
              key={i}
              className="absolute h-3 w-2 rounded-sm"
              style={{ background: p.color }}
              initial={{ x: 0, y: 0, rotate: 0, opacity: 1 }}
              animate={{ x: p.x, y: p.y + 120, rotate: p.rotate + 360, opacity: 0 }}
              transition={{ duration: 1.6, ease: [0.2, 0.8, 0.2, 1] }}
            />
          ))}
          <motion.div
            className="glass px-8 py-5 text-center"
            initial={{ scale: 0.6, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 260, damping: 18 }}
          >
            <p className="font-display text-2xl font-semibold">{message}</p>
            <p className="text-sm text-muted">今天的收获已经记进学习日志</p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
