// content/guide.json 的类型。校验由 scripts/check.py 做，这里只描述形状。
export interface GuidePoint {
  point: string;
  detail: string;
}

export interface GuideNode {
  id: string;
  title: string;
  kind: string;
  source: string;
  launch: string;
  purpose: string;
  points: GuidePoint[];
  tradeoff: string;
  milestones: string[];
  timeHint: string;
}

export interface GuideStage {
  id: string;
  node: string;
  name: string;
  claim: string;
  why: string[];
}

export interface GuideCompanion {
  id: string;
  title: string;
  launch: string;
  note: string;
}

export interface GuideBookCompare {
  aspect: string;
  siefken: string;
  selinger: string;
}

export interface Guide {
  schema: number;
  updated: string;
  mainline: string;
  overview: {
    claim: string;
    paragraphs: string[];
    howto: string[];
  };
  stages: GuideStage[];
  toolTrack: {
    claim: string;
    essay: string[];
  };
  nodes: GuideNode[];
  companions: GuideCompanion[];
  books: {
    essay: string[];
    compare: GuideBookCompare[];
    default: string;
    single: string;
    backtrack: string;
  };
  gap: {
    claim: string;
    essay: string[];
  };
  graph: {
    order: string[];
    tools: string[];
  };
}
