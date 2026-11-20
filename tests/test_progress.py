"""Tests for Rich progress bar reporting and result summary helpers."""

from __future__ import annotations

from ytdownloader.progress import (
    DownloadProgressReporter,
    build_progress,
    make_progress_hook,
    summarize_result,
)


def test_progress_reporter_updates_downloading_and_finished():
    progress = build_progress()
    reporter = DownloadProgressReporter(progress, "Video 1/2")
    hook = make_progress_hook(reporter)

    hook({"status": "downloading", "total_bytes": 1000, "downloaded_bytes": 400})
    task = progress.tasks[reporter.task_id]
    assert task.total == 1000
    assert task.completed == 400

    hook({"status": "finished", "total_bytes": 1000, "downloaded_bytes": 1000})
    task = progress.tasks[reporter.task_id]
    assert task.completed == 1000


def test_progress_reporter_set_label():
    progress = build_progress()
    reporter = DownloadProgressReporter(progress, "Initial")
    reporter.set_label("Updated")
    assert progress.tasks[reporter.task_id].fields["label"] == "Updated"


def test_summarize_result_with_and_without_size():
    assert summarize_result({"title": "Demo", "filesize": 2048}) == "Demo (2.0 KB)"
    assert summarize_result({"title": "Demo"}) == "Demo"
    assert summarize_result({}) == "Unknown"
