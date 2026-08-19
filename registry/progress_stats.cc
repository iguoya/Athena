#include "registry/progress_stats.h"

#include <algorithm>

double ChapterProgress::completion_ratio() const {
    if (total <= 0) {
        return 0.0;
    }
    return static_cast<double>(mastery_sum) / (total * kMaxMastery);
}

double CategoryProgress::average_mastery() const {
    if (total <= 0) {
        return 0.0;
    }
    return static_cast<double>(mastery_sum) / total;
}

array<int, kMasteryLevels> CategoryProgress::mastery_histogram() const {
    array<int, kMasteryLevels> histogram{};
    for (const auto& chapter : chapters) {
        for (const auto& [title, mastery] : chapter.subchapter_mastery) {
            // 数据来自 SQLite，理论上已经限定在 0-5，但存储层没有 CHECK
            // 约束，越界值在这里夹住而不是越界写数组。
            const int level = clamp(mastery, 0, kMaxMastery);
            histogram[static_cast<size_t>(level)]++;
        }
    }
    return histogram;
}

CategoryProgress aggregate_category_progress(
    const ChapterCatalog& catalog,
    const string& category_name,
    const map<string, int>& mastery_by_id) {
    CategoryProgress progress;

    const auto& all_chapters = catalog.chapters();
    const auto found = all_chapters.find(category_name);
    if (found == all_chapters.end()) {
        return progress;
    }

    for (const auto& chapter : found->second) {
        if (chapter.subchapters.empty()) {
            continue;
        }

        ChapterProgress chapter_progress;
        chapter_progress.chapter_title = chapter.title;
        for (const auto& subchapter : chapter.subchapters) {
            const string function_id =
                make_function_id(category_name, chapter.name, subchapter.name);
            int mastery = 0;
            if (const auto entry = mastery_by_id.find(function_id);
                entry != mastery_by_id.end()) {
                mastery = entry->second;
            }

            chapter_progress.subchapter_mastery.emplace_back(
                subchapter.title, mastery);
            chapter_progress.total++;
            chapter_progress.mastery_sum += mastery;
            if (mastery >= kMaxMastery) {
                chapter_progress.mastered++;
            } else if (mastery > 0) {
                chapter_progress.in_progress++;
            }
        }

        progress.total += chapter_progress.total;
        progress.mastered += chapter_progress.mastered;
        progress.in_progress += chapter_progress.in_progress;
        progress.mastery_sum += chapter_progress.mastery_sum;
        progress.chapters.push_back(std::move(chapter_progress));
    }

    progress.not_started =
        progress.total - progress.mastered - progress.in_progress;
    return progress;
}
