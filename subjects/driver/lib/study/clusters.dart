import "dart:math";

import "../core/models.dart";
/// 考点簇（主仓库 ADR 0076 决策 9、ADR 0079）：把「考同一个点、换了问法」的题聚成一簇。
///
/// 为什么需要：`topic_id` 太粗（科目一 2497 题只有 11 个知识点，同知识点只等于同章节），
/// 出处条款又太稀（绝大多数条款只被一道题引用）。所以用「题干与正确答案的文字相似度」为主、
/// 「引用同一条具体条款」为辅来聚类。
///
/// 这是**确定性的纯函数**：同样的题库永远算出同样的簇，不落盘、不进 git、不会过期。
/// 用途只有一个：强化练习里，错了一道题，就出它同簇的另一种问法，检验是真懂还是背了那道题。
class ClusterIndex {
  const ClusterIndex(this.clusters, this._byQuestion);

  /// 每一簇的题号（成员按题号排序；簇按首个成员排序）。
  final List<List<String>> clusters;
  final Map<String, int> _byQuestion;

  static const empty = ClusterIndex([], {});

  bool get isEmpty => clusters.isEmpty;

  /// 在某个簇里的题数。
  int get coveredQuestions => _byQuestion.length;

  /// 与 [id] 同簇的其他题（不含它自己）；不在任何簇里就是空。
  List<String> mates(String id) {
    final index = _byQuestion[id];
    if (index == null) return const [];
    return [for (final m in clusters[index]) if (m != id) m];
  }
}

/// 一道题进入聚类要满足的最少文字量（规范化后）：太短的题干没有可比性。
const clusterMinTextLength = 8;

/// 两题「文字几乎一样」的上限：高于它视为重复题，不当作换了问法。
const clusterDuplicateSimilarity = 0.97;

/// 引用的条款被这么多题以上引用，就算泛泛的条款（如整本考试大纲的一节），不当作线索。
const clusterGenericClauseSize = 6;

/// 一簇最多多少题：再大说明链式相连出了不相干的题。
const clusterMaxSize = 8;

/// 聚类。只在同一个知识点（章节）内比较；带图片或自绘标志的题不参与（它们的题干几乎都一样，
/// 文字相似度没有意义，区别全在图上）。
ClusterIndex buildClusters(
  Iterable<Question> questions, {
  double linkThreshold = 0.55,
  double clauseThreshold = 0.30,
  int maxSize = clusterMaxSize,
}) {
  final byTopic = <String, List<Question>>{};
  for (final q in questions) {
    if (q.image != null || q.sign != null) continue;
    byTopic.putIfAbsent(q.topicId, () => []).add(q);
  }
  final clusters = <List<String>>[];
  for (final topic in byTopic.keys.toList()..sort()) {
    clusters.addAll(_clusterTopic(byTopic[topic]!, linkThreshold, clauseThreshold, maxSize));
  }
  clusters.sort((a, b) => a.first.compareTo(b.first));
  return ClusterIndex(clusters, {
    for (var i = 0; i < clusters.length; i++)
      for (final id in clusters[i]) id: i,
  });
}

// ---------------------------------------------------------------- 内部

/// 只留汉字、字母、数字，统一小写：标点、空白、全半角差异不影响相似度。
String _normalize(String text) {
  final out = StringBuffer();
  for (final rune in text.runes) {
    final isCjk = rune >= 0x4E00 && rune <= 0x9FFF;
    final isDigit = rune >= 0x30 && rune <= 0x39;
    final isLatin = (rune >= 0x41 && rune <= 0x5A) || (rune >= 0x61 && rune <= 0x7A);
    if (isCjk || isDigit || isLatin) out.writeCharCode(isLatin ? String.fromCharCode(rune).toLowerCase().codeUnitAt(0) : rune);
  }
  return out.toString();
}

/// 二元组集合：[withAnswer] 为真时加上正确答案的字面（不跨题干与答案的边界）。
Set<String> _bigrams(Question q, {required bool withAnswer}) {
  final grams = <String>{};
  void add(String text) {
    final s = _normalize(text);
    for (var i = 0; i + 1 < s.length; i++) {
      grams.add(s.substring(i, i + 2));
    }
  }

  add(q.prompt);
  if (withAnswer) {
    for (final c in q.choices) {
      if (c.ok) add(c.label);
    }
  }
  return grams;
}

/// 只有正确答案字面的二元组。
Set<String> _answerBigrams(Question q) {
  final grams = <String>{};
  for (final c in q.choices) {
    if (!c.ok) continue;
    final s = _normalize(c.label);
    for (var i = 0; i + 1 < s.length; i++) {
      grams.add(s.substring(i, i + 2));
    }
  }
  return grams;
}

/// 归一化的 tf-idf 向量（二元组出现与否，权重取 idf；太常见的二元组丢掉）。
List<Map<String, double>> _vectors(List<Set<String>> grams) {
  final n = grams.length;
  final df = <String, int>{};
  for (final g in grams) {
    for (final gram in g) {
      df[gram] = (df[gram] ?? 0) + 1;
    }
  }
  final stop = max(3, (n * 0.25).floor());
  final weight = <String, double>{
    for (final e in df.entries)
      if (e.value <= stop) e.key: log(n / e.value),
  };
  final out = <Map<String, double>>[];
  for (final g in grams) {
    final v = <String, double>{for (final gram in g) if (weight.containsKey(gram)) gram: weight[gram]!};
    final norm = sqrt(v.values.fold(0.0, (sum, w) => sum + w * w));
    out.add(norm == 0 ? const {} : {for (final e in v.entries) e.key: e.value / norm});
  }
  return out;
}

double _cosine(Map<String, double> a, Map<String, double> b) {
  if (a.isEmpty || b.isEmpty) return 0;
  final (small, large) = a.length <= b.length ? (a, b) : (b, a);
  var dot = 0.0;
  for (final e in small.entries) {
    final other = large[e.key];
    if (other != null) dot += e.value * other;
  }
  return dot;
}

/// 同为选择题（非判断）的两道题，答案相同加句式相同并不说明考点相同
/// （追逐竞驶与醉酒驾驶都答「处拘役，并处罚金」），所以要求**题干本身**足够像；
/// 同时**答案也要有点像**——句式骨架一样、讲的却是不同规则的题（「以下哪种说法是正确的」），
/// 区别全在答案里，答案毫不相干就不是同一个点。
const clusterSameFormPromptSimilarity = 0.70;
const clusterSameFormAnswerSimilarity = 0.30;

/// 两道判断题前缀很长很像、只有后半句事实不同的情况很常见（「交警指挥下可从应急车道绕行」与
/// 「……可临时占用对向车道」），所以判断题之间的门槛比跨题型更高。
const clusterJudgePairSimilarity = 0.65;

List<List<String>> _clusterTopic(List<Question> list, double linkThreshold, double clauseThreshold, int maxSize) {
  // 按题号排序，保证结果确定。
  final items = [...list]..sort((a, b) => a.id.compareTo(b.id));
  final n = items.length;
  final fullVectors = _vectors([for (final q in items) _bigrams(q, withAnswer: true)]);
  final promptVectors = _vectors([for (final q in items) _bigrams(q, withAnswer: false)]);
  final answerVectors = _vectors([for (final q in items) _answerBigrams(q)]);
  final lengths = [for (final q in items) _normalize(q.prompt).length];
  final isJudge = [for (final q in items) q.kind == "judge"];

  // 共享的具体条款：同一来源同一定位，且被引用的题不多（泛泛的条款不算线索）。
  final clauseMembers = <String, List<int>>{};
  for (var i = 0; i < n; i++) {
    for (final ref in items[i].sourceRefs) {
      if (ref.locator.trim().isEmpty) continue;
      clauseMembers.putIfAbsent("${ref.sourceId}|${ref.locator}", () => []).add(i);
    }
  }
  final shared = <int>{};
  int pairKey(int i, int j) => i < j ? i * n + j : j * n + i;
  for (final members in clauseMembers.values) {
    if (members.length < 2 || members.length > clusterGenericClauseSize) continue;
    for (var a = 0; a < members.length; a++) {
      for (var b = a + 1; b < members.length; b++) {
        shared.add(pairKey(members[a], members[b]));
      }
    }
  }

  // 候选边：用倒排索引只比有公共二元组的题对，再加上共享条款的题对。
  final postings = <String, List<int>>{};
  for (var i = 0; i < n; i++) {
    if (lengths[i] < clusterMinTextLength) continue;
    for (final gram in fullVectors[i].keys) {
      postings.putIfAbsent(gram, () => []).add(i);
    }
  }
  final candidates = <int>{...shared};
  for (final posting in postings.values) {
    // 一个二元组出现在很多题里时，两两配对的代价大而信息少；已经被 stop 过滤过，这里再保险。
    if (posting.length > 60) continue;
    for (var a = 0; a < posting.length; a++) {
      for (var b = a + 1; b < posting.length; b++) {
        candidates.add(pairKey(posting[a], posting[b]));
      }
    }
  }

  final edges = <(double, int, int)>[];
  for (final key in candidates) {
    final i = key ~/ n;
    final j = key % n;
    if (lengths[i] < clusterMinTextLength || lengths[j] < clusterMinTextLength) continue;
    final full = _cosine(fullVectors[i], fullVectors[j]);
    if (full >= clusterDuplicateSimilarity) continue; // 几乎一模一样：是重复题，不是换了问法
    final sharesClause = shared.contains(key);
    final crossForm = isJudge[i] != isJudge[j]; // 判断题与选择题互换：同一个点的两种问法，最典型的变式
    if (!crossForm && !isJudge[i]) {
      // 两道选择题：看题干本身像不像，答案相同不算数。
      final prompt = _cosine(promptVectors[i], promptVectors[j]);
      final answer = _cosine(answerVectors[i], answerVectors[j]);
      if (answer >= clusterSameFormAnswerSimilarity &&
          (prompt >= clusterSameFormPromptSimilarity || (sharesClause && prompt >= 0.5))) {
        edges.add((prompt, i, j));
      }
      continue;
    }
    final threshold = crossForm ? linkThreshold : max(linkThreshold, clusterJudgePairSimilarity);
    if (full >= threshold || (sharesClause && full >= clauseThreshold)) edges.add((full, i, j));
  }
  // 分高的先并；同分按下标，保证确定。有簇大小上限：并起来超过上限的边直接放弃。
  edges.sort((x, y) {
    final byScore = y.$1.compareTo(x.$1);
    if (byScore != 0) return byScore;
    final byI = x.$2.compareTo(y.$2);
    return byI != 0 ? byI : x.$3.compareTo(y.$3);
  });
  final parent = List<int>.generate(n, (i) => i);
  final size = List<int>.filled(n, 1);
  int find(int x) {
    while (parent[x] != x) {
      parent[x] = parent[parent[x]];
      x = parent[x];
    }
    return x;
  }

  for (final (_, i, j) in edges) {
    final a = find(i);
    final b = find(j);
    if (a == b || size[a] + size[b] > maxSize) continue;
    parent[b] = a;
    size[a] += size[b];
  }
  final groups = <int, List<String>>{};
  for (var i = 0; i < n; i++) {
    groups.putIfAbsent(find(i), () => []).add(items[i].id);
  }
  return [for (final g in groups.values) if (g.length >= 2) g..sort()];
}
