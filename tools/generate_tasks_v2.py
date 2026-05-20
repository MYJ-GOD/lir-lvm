#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


RELAYS = ["relay1", "relay2"]
SENSORS = ["water_sensor", "temperature_sensor", "humidity_sensor"]
READABLE = ["relay1", "relay2", "water_sensor", "temperature_sensor", "humidity_sensor"]
WAITS_SHORT = [50, 100, 200, 500]
WAITS_LONG = [100, 200, 500, 1000]


def task(task_id: str, category: str, prompt: str, allowed_devices: list[str], expected_mir: str) -> dict:
    return {
        "task_id": task_id,
        "category": category,
        "prompt": prompt,
        "allowed_devices": allowed_devices,
        "expected_status": "success",
        "expected_mir": expected_mir,
    }


def main() -> int:
    out_path = Path(__file__).resolve().parent.parent / "data" / "tasks_v2.jsonl"
    rows = []
    n = 1

    def next_id() -> str:
        nonlocal n
        tid = f"V2_{n:03d}"
        n += 1
        return tid

    # single_set
    for relay in RELAYS:
        for value, word in [(1, "打开"), (0, "关闭")]:
            tid = next_id()
            rows.append(
                task(
                    tid,
                    "single_set",
                    f"{word} {relay}。",
                    [relay],
                    f"task {tid.lower()} {{\n  require cap({relay})\n  set {relay} = {value}\n  halt\n}}\n",
                )
            )

    # single_read
    for dev in READABLE:
        tid = next_id()
        rows.append(
            task(
                tid,
                "single_read",
                f"读取 {dev} 的当前值。",
                [dev],
                f"task {tid.lower()} {{\n  require cap({dev})\n  read {dev}\n  halt\n}}\n",
            )
        )

    # set_wait_halt
    for relay in RELAYS:
        for value, word in [(1, "打开"), (0, "关闭")]:
            for ms in WAITS_SHORT:
                tid = next_id()
                rows.append(
                    task(
                        tid,
                        "set_wait_halt",
                        f"{word} {relay}，等待 {ms} 毫秒，然后停止。",
                        [relay],
                        f"task {tid.lower()} {{\n  require cap({relay})\n  set {relay} = {value}\n  wait {ms}ms\n  halt\n}}\n",
                    )
                )

    # wait_read
    for sensor in SENSORS:
        for ms in WAITS_LONG:
            tid = next_id()
            rows.append(
                task(
                    tid,
                    "wait_read",
                    f"等待 {ms} 毫秒后读取 {sensor}。",
                    [sensor],
                    f"task {tid.lower()} {{\n  require cap({sensor})\n  wait {ms}ms\n  read {sensor}\n  halt\n}}\n",
                )
            )

    # set_wait_read
    for relay in RELAYS:
        for sensor in SENSORS:
            for value, word in [(1, "打开"), (0, "关闭")]:
                for ms in WAITS_SHORT:
                    tid = next_id()
                    rows.append(
                        task(
                            tid,
                            "set_wait_read",
                            f"{word} {relay}，等待 {ms} 毫秒，然后读取 {sensor}。",
                            [relay, sensor],
                            f"task {tid.lower()} {{\n  require cap({relay})\n  require cap({sensor})\n  set {relay} = {value}\n  wait {ms}ms\n  read {sensor}\n  halt\n}}\n",
                        )
                    )

    # multi_read ordered pairs
    for i, dev1 in enumerate(READABLE):
        for j, dev2 in enumerate(READABLE):
            if i == j:
                continue
            tid = next_id()
            rows.append(
                task(
                    tid,
                    "multi_read",
                    f"先读取 {dev1}，再读取 {dev2}。",
                    [dev1, dev2],
                    f"task {tid.lower()} {{\n  require cap({dev1})\n  require cap({dev2})\n  read {dev1}\n  read {dev2}\n  halt\n}}\n",
                )
            )

    # pulse
    for relay in RELAYS:
        for ms in WAITS_SHORT:
            tid = next_id()
            rows.append(
                task(
                    tid,
                    "pulse",
                    f"打开 {relay}，等待 {ms} 毫秒，关闭 {relay}，然后停止。",
                    [relay],
                    f"task {tid.lower()} {{\n  require cap({relay})\n  set {relay} = 1\n  wait {ms}ms\n  set {relay} = 0\n  halt\n}}\n",
                )
            )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(str(out_path))
    print(f"count={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
