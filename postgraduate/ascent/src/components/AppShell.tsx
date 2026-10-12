import { Outlet, useLocation } from "react-router";
import { AnimatePresence, motion } from "motion/react";
import { Backdrop } from "./Backdrop";
import { Sidebar } from "./Sidebar";
import { TitleBar } from "./TitleBar";
import { UpdateToast } from "./UpdateToast";
import { cn } from "@/lib/utils";

export function AppShell() {
  const location = useLocation();
  // Home must fit one screen on 200% DPI laptops; the vocab learner runs the same
  // one-screen flow. Other pages may scroll with wheel (no visible bar).
  const fixedHeight = location.pathname === "/" || location.pathname.startsWith("/vocab");
  return (
    <div className="flex h-full overflow-hidden">
      <Backdrop />
      <TitleBar />
      <UpdateToast />
      <Sidebar />
      <main
        className={cn(
          "scroll-soft min-w-0 flex-1 px-4 pt-9 sm:px-5 xl:px-7",
          fixedHeight ? "overflow-hidden pb-3" : "overflow-y-auto pb-5 xl:pb-6",
        )}
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: fixedHeight ? 0 : 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: fixedHeight ? 0 : -4 }}
            transition={{ duration: 0.22, ease: "easeOut" }}
            className={cn(fixedHeight && "h-full")}
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
