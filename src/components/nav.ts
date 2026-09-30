import { BookOpen, Headphones, Home, Map, NotebookPen, NotebookTabs, PenLine, RotateCcw } from "lucide-react";

// Main navigation; later milestones replace the placeholder pages one by one.
export const NAV = [
  { to: "/", label: "今天", icon: Home },
  { to: "/sentences", label: "今日句组", icon: BookOpen },
  { to: "/map", label: "高中知识地图", icon: Map },
  { to: "/listening", label: "听力 · 听写", icon: Headphones },
  { to: "/writing", label: "写作 · 翻译", icon: PenLine },
  { to: "/words", label: "生词本", icon: NotebookTabs },
  { to: "/mistakes", label: "错题本", icon: RotateCcw },
  { to: "/journal", label: "学习日志", icon: NotebookPen },
];
