import { useEffect } from "react";
import { createHashRouter, RouterProvider } from "react-router";
import { AppShell } from "@/components/AppShell";
import { Today } from "@/pages/Today";
import { Placeholder } from "@/pages/Placeholder";
import { Sentences } from "@/pages/Sentences";
import { NAV } from "@/components/nav";
import { applySkin, useSkin } from "@/theme/skins";

const router = createHashRouter([
  {
    element: <AppShell />,
    children: [
      { index: true, element: <Today /> },
      { path: "/sentences", element: <Sentences /> },
      ...NAV.filter((n) => n.to !== "/" && n.to !== "/sentences").map((n) => ({ path: n.to, element: <Placeholder /> })),
    ],
  },
]);

export default function App() {
  const skin = useSkin((s) => s.skin);
  useEffect(() => applySkin(skin), [skin]);
  return <RouterProvider router={router} />;
}
