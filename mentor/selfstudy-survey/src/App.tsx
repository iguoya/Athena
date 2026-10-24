import { useState } from "react";
import { Courses } from "./Courses";
import { Majors } from "./Majors";
import { VIEWS, type Route } from "./nav";
import { Events, Method, Practice, Textbooks } from "./Others";
import { Overview } from "./Overview";
import { Provinces } from "./Provinces";

export default function App() {
  const [route, setRoute] = useState<Route>({ view: "overview" });
  const go = (r: Route) => {
    setRoute(r);
    window.scrollTo(0, 0);
  };
  const current = VIEWS.find((v) => v.id === route.view)!;

  return (
    <div className="app">
      <nav className="rail">
        <div className="brand">
          <b>自考专业调查</b>
          <small>计算机 · 电子信息 · 2025–2026</small>
        </div>
        {VIEWS.map((v) => (
          <button key={v.id} className={v.id === route.view ? "on" : ""} onClick={() => go({ view: v.id })}>
            {v.label}
            <small>{v.hint}</small>
          </button>
        ))}
      </nav>
      <main className="main">
        <header className="top">
          <h1>{current.label}</h1>
          <p>{current.hint}。数据逐条带来源与核对日期，待查不等于没有。</p>
        </header>
        {route.view === "overview" && <Overview go={go} />}
        {route.view === "majors" && <Majors major={route.major} province={route.province} go={go} />}
        {route.view === "provinces" && <Provinces province={route.province} go={go} />}
        {route.view === "courses" && <Courses course={route.course} go={go} />}
        {route.view === "textbooks" && <Textbooks go={go} />}
        {route.view === "practice" && <Practice go={go} />}
        {route.view === "events" && <Events go={go} />}
        {route.view === "method" && <Method go={go} />}
      </main>
    </div>
  );
}
