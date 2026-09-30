import { Outlet, useLocation } from "react-router";
import { AnimatePresence, motion } from "motion/react";
import { Backdrop } from "./Backdrop";
import { Sidebar } from "./Sidebar";
import { TitleBar } from "./TitleBar";

export function AppShell() {
  const location = useLocation();
  return (
    <div className="flex h-full">
      <Backdrop />
      <TitleBar />
      <Sidebar />
      <main className="min-w-0 flex-1 overflow-y-auto px-8 pb-10 pt-11">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
