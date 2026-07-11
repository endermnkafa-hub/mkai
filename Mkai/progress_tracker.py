from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_PATH = Path(__file__).with_name("progress-status.json")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_default_status() -> dict[str, Any]:
    return {
        "project": "MKAI",
        "start_time": now_iso(),
        "last_update_time": now_iso(),
        "current_task": "Tune prompt quality and verify stronger model availability",
        "summary": "Real progress tracker is active. Backend and UI are live; remaining work focuses on model quality and prompt tuning.",
        "tasks": [
            {
                "id": "tracker-system",
                "name": "Implement real progress tracker",
                "status": "done",
                "weight": 20,
                "updated_at": now_iso(),
            },
            {
                "id": "backend-health",
                "name": "Verify backend health and live response",
                "status": "done",
                "weight": 20,
                "updated_at": now_iso(),
            },
            {
                "id": "provider-routing",
                "name": "Update provider routing and config",
                "status": "done",
                "weight": 20,
                "updated_at": now_iso(),
            },
            {
                "id": "chat-verification",
                "name": "Verify chat endpoint response",
                "status": "done",
                "weight": 20,
                "updated_at": now_iso(),
            },
            {
                "id": "prompt-quality",
                "name": "Tune prompt quality",
                "status": "in-progress",
                "weight": 10,
                "updated_at": now_iso(),
            },
            {
                "id": "stronger-model",
                "name": "Verify stronger local model availability",
                "status": "pending",
                "weight": 10,
                "updated_at": now_iso(),
            },
        ],
    }


def load_status() -> dict[str, Any]:
    if not STATUS_PATH.exists():
        return build_default_status()

    with STATUS_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if "tasks" not in data:
        data["tasks"] = build_default_status()["tasks"]
    if "start_time" not in data:
        data["start_time"] = now_iso()
    if "last_update_time" not in data:
        data["last_update_time"] = now_iso()
    if "current_task" not in data:
        data["current_task"] = "Track the next meaningful development step"
    return data


def _task_status(task: dict[str, Any]) -> str:
    if "status" in task and task.get("status") in {"done", "in-progress", "pending"}:
        return str(task.get("status"))
    if task.get("done") is True:
        return "done"
    if task.get("done") is False:
        return "pending"
    return "pending"


def recalculate(data: dict[str, Any]) -> dict[str, Any]:
    tasks = data.get("tasks", [])
    total_weight = sum(int(task.get("weight", 1)) for task in tasks)
    completed_weight = sum(int(task.get("weight", 1)) for task in tasks if _task_status(task) == "done")
    remaining_weight = max(0, total_weight - completed_weight)

    completed_tasks = [task.get("name") or task.get("id") or "Unnamed task" for task in tasks if _task_status(task) == "done"]
    remaining_tasks = [task.get("name") or task.get("id") or "Unnamed task" for task in tasks if _task_status(task) != "done"]

    percentage_complete = round((completed_weight / total_weight * 100) if total_weight else 0, 1)
    remaining_hours = round(max(0.5, 0.8 + (remaining_weight / max(total_weight, 1)) * 2.5), 1)

    current_task = data.get("current_task") or next((task.get("name") or task.get("id") for task in tasks if _task_status(task) == "in-progress"), remaining_tasks[0] if remaining_tasks else "All tracked work completed")

    data["completed_tasks"] = completed_tasks
    data["remaining_tasks"] = remaining_tasks
    data["current_task"] = current_task
    data["percentage_complete"] = percentage_complete
    data["estimated_remaining_time"] = f"{remaining_hours:.1f}h"
    data["last_update_time"] = now_iso()
    return data


def save_status(data: dict[str, Any]) -> None:
    with STATUS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def update_task(task_id: str, status: str, current_task: str | None = None) -> None:
    data = load_status()
    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            task["status"] = status
            task["updated_at"] = now_iso()
            break
    if current_task:
        data["current_task"] = current_task
    save_status(recalculate(data))


def main() -> None:
    parser = argparse.ArgumentParser(description="Update MKAI progress tracking status")
    parser.add_argument("--task-id", dest="task_id")
    parser.add_argument("--status", choices=["done", "in-progress", "pending"])
    parser.add_argument("--current-task")
    parser.add_argument("--summary")
    args = parser.parse_args()

    if args.task_id and args.status:
        update_task(args.task_id, args.status, args.current_task)
        return

    data = load_status()
    if args.summary:
        data["summary"] = args.summary
    if args.current_task:
        data["current_task"] = args.current_task
    save_status(recalculate(data))


if __name__ == "__main__":
    main()
