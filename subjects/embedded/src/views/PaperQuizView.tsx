// 整卷作答页:按 paperId 找卷,交给整卷作答器(mode=past-exam)。
import { pastPaperFiles } from "../content";
import PaperRunner from "../components/PaperRunner";
import type { View } from "./types";

export default function PaperQuizView({ paperId, go }: { paperId: string; go: (v: View) => void }) {
  const paper = pastPaperFiles.find((p) => p.id === paperId);

  if (!paper) {
    return (
      <div className="pt-10 text-center text-[14px]" style={{ color: "var(--tk-muted)" }}>
        卷子 {paperId} 不在构建产物里——确认 content/past-exams/papers/ 下有对应文件后重新构建。
      </div>
    );
  }
  return (
    <PaperRunner
      title={paper.title}
      questions={paper.questions}
      mode="past-exam"
      course="past-exam"
      chapterId={paper.id}
      kpId={paper.id}
      onExit={() => go({ kind: "past" })}
    />
  );
}
