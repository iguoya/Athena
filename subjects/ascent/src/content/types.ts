// Content model from ADR 0010. Sentences are first-class; every sentence names a registered source (ADR 0005).

export type SegmentRole = "main" | "clause" | "phrase" | "plain";

export type Segment = { text: string; role: SegmentRole };

export type Gloss = {
  /** Lower-case words of the sentence this gloss applies to (a phrase lists all of its words). */
  words: string[];
  lemma: string;
  pos: string;
  simpleEn: string;
  cn: string;
};

export type Sentence = {
  id: string;
  en: string;
  cn: string;
  scene: string;
  grammar: string[];
  grammarNote: string;
  source: string;
  segments: Segment[];
  glosses: Gloss[];
};

export type SentenceSet = {
  id: string;
  title: string;
  subtitle: string;
  chapter: number;
  unit: string;
  exams: string[];
  review: "draft" | "reviewed";
  reviewNote?: string;
  sentences: Sentence[];
};

export type Source = {
  title: string;
  year: number;
  url: string;
  kind: string;
  license: string;
};

/** A single grammar tag used on sentences and in review cards (ADR 0007). */
export type GrammarPattern = {
  id: string;
  name: string;
  difficulty: number;
};

/** One high-school unit on the chapter-1 knowledge map (ADR 0017). */
export type GrammarUnit = {
  id: string;
  name: string;
  order: number;
  difficulty: number;
  blurb: string;
  patterns: GrammarPattern[];
};

export type GrammarChapter = {
  chapter: number;
  title: string;
  subtitle: string;
  blurb: string;
  units: GrammarUnit[];
};
