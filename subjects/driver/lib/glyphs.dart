import "package:flutter/material.dart";

/// 界面图标对照表（ADR 0049）：一个概念只用一个图标，一个图标只表示一个意思，
/// 统一用 Material 实心（Filled）风格。界面代码只用这里的名字，不直接写 `Icons.xxx`；
/// `test/glyphs_test.dart` 守住「不重复、不混描边、别处不写 Icons.」三条。
///
/// 小汽车 `directions_car` 不在表里：它是应用标志（`AppMark`，ADR 0048），不拿来当功能图标。
abstract final class Glyph {
  // ── 导航与科目 ──
  static const subject1 = Icons.gavel;
  static const subject2 = Icons.local_parking;
  static const subject4 = Icons.health_and_safety;
  static const locked = Icons.lock;
  static const unlocked = Icons.lock_open;
  static const wrongBook = Icons.bookmark;
  static const wrongBookCleared = Icons.bookmark_remove;
  static const review = Icons.fact_check;
  static const numbers = Icons.pin;

  // ── 科目一 / 科目四：练习、考试与题目 ──
  static const practice = Icons.list_alt;
  static const topic = Icons.article;
  static const question = Icons.quiz;
  static const pending = Icons.pending_actions;
  static const mockExam = Icons.assignment;
  static const submit = Icons.assignment_turned_in;
  static const examFailed = Icons.assignment_late;
  static const examHistory = Icons.timeline;
  static const duration = Icons.timer;
  static const topicAccuracy = Icons.bar_chart;
  static const recentDays = Icons.date_range;
  static const goal = Icons.flag;
  static const finish = Icons.done_all;
  static const position = Icons.format_list_numbered;
  static const serial = Icons.tag;
  static const hot = Icons.local_fire_department;
  static const band = Icons.signal_cellular_alt;
  static const errorProne = Icons.warning_amber;
  static const kindJudge = Icons.thumbs_up_down;
  static const kindSingle = Icons.radio_button_checked;
  static const kindMulti = Icons.library_add_check;
  static const explain = Icons.lightbulb;
  static const source = Icons.menu_book;
  static const readAloud = Icons.volume_up;
  static const readAloudOff = Icons.volume_off;
  static const speed = Icons.speed;

  // ── 对错与订正 ──
  /// 对：答对、已掌握、操作成功。
  static const correct = Icons.check_circle;

  /// 错：答错、错了几次、还错着、默演漏了。
  static const wrong = Icons.cancel;
  static const stubborn = Icons.priority_high;
  static const improving = Icons.trending_up;
  static const weak = Icons.trending_down;
  static const graduated = Icons.playlist_remove;
  static const bySubject = Icons.category;

  // ── 激励与提醒 ──
  static const notice = Icons.notifications;
  static const streak = Icons.bolt;
  static const topicDone = Icons.verified;
  static const achievement = Icons.emoji_events;

  // ── 科目二：练车日与项目手册 ──
  static const practiceDay = Icons.today;
  static const handbook = Icons.library_books;
  static const log = Icons.history;
  static const examReady = Icons.sports_score;
  static const beforeDrill = Icons.wb_sunny;
  static const afterDrill = Icons.nights_stay;
  static const brief = Icons.checklist;
  static const reviewDay = Icons.rate_review;
  static const record = Icons.edit_note;
  static const runs = Icons.insights;
  static const runCount = Icons.repeat;
  static const passable = Icons.task_alt;
  static const trend = Icons.show_chart;
  static const formTable = Icons.table_chart;
  static const mistake = Icons.error;
  static const untried = Icons.fiber_new;
  static const rules = Icons.rule;
  static const caution = Icons.report;
  static const tips = Icons.tips_and_updates;
  static const pointCard = Icons.push_pin;
  static const coach = Icons.campaign;
  static const rehearse = Icons.record_voice_over;
  static const compare = Icons.visibility;
  static const animation = Icons.animation;
  static const more = Icons.add_circle;
  static const less = Icons.remove_circle;
  static const addPhoto = Icons.add_photo_alternate;

  // ── 动画播放 ──
  static const play = Icons.play_arrow;
  static const pause = Icons.pause;
  static const playStep = Icons.play_circle;
  static const stepBack = Icons.skip_previous;
  static const stepNext = Icons.skip_next;
  static const restart = Icons.replay;

  // ── 同步 ──
  static const sync = Icons.cloud_sync;
  static const syncFailed = Icons.sync_problem;
  static const cloudFolder = Icons.cloud;
  static const backup = Icons.backup;
  static const credentials = Icons.key;
  static const chooseFolder = Icons.folder_open;

  // ── 通用操作 ──
  static const next = Icons.arrow_forward;
  static const back = Icons.arrow_back;
  static const goTo = Icons.chevron_right;
  static const close = Icons.close;
  static const info = Icons.info;
  static const edit = Icons.edit;
  static const delete = Icons.delete;
  static const save = Icons.save;

  /// 列表前的小圆点，纯装饰。
  static const bullet = Icons.circle;
}
