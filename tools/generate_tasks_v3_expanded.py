#!/usr/bin/env python3
"""
Generate expanded closed-loop tasks (50+ tasks) covering readback/retry semantics.
Extends the original 16-task v3 set with more variations and categories.
"""
from __future__ import annotations

import json
from pathlib import Path

RELAYS = ["relay1", "relay2"]
SENSORS = ["water_sensor", "temperature_sensor", "humidity_sensor"]
WAIT_MS = [50, 100, 200, 500]

TASKS = []


def tid(n: int) -> str:
    return f"V3E_{n:03d}"


# ── Category 1: readback basic (relay on/off, all combinations) ──────────────
_readback_id = 0
for relay in RELAYS:
    for value, label in [(1, "on"), (0, "off")]:
        _readback_id += 1
        TASKS.append({
            "task_id": tid(_readback_id),
            "category": "readback_basic",
            "prompt": f"Turn {label} {relay} and verify by reading it back; halt after verification.",
            "allowed_devices": [relay],
            "expected_status": "success",
            "expected_mir": (
                f"task {tid(_readback_id)} {{\n"
                f"  require cap({relay})\n"
                f"  set {relay} = {value}\n"
                f"  readback {relay} expect {value}\n"
                f"  halt\n}}"
            ),
        })

# ── Category 2: readback with sensor context ─────────────────────────────────
_sensor_readback_id = _readback_id
for sensor in SENSORS:
    for relay in RELAYS:
        for value, label in [(1, "on"), (0, "off")]:
            _sensor_readback_id += 1
            TASKS.append({
                "task_id": tid(_sensor_readback_id),
                "category": "readback_sensor_context",
                "prompt": f"Read {sensor}, then turn {label} {relay} and verify {relay} reads back as {value}; halt.",
                "allowed_devices": [sensor, relay],
                "expected_status": "success",
                "expected_mir": (
                    f"task {tid(_sensor_readback_id)} {{\n"
                    f"  require cap({sensor})\n"
                    f"  require cap({relay})\n"
                    f"  read {sensor}\n"
                    f"  set {relay} = {value}\n"
                    f"  readback {relay} expect {value}\n"
                    f"  halt\n}}"
                ),
            })

# ── Category 3: retry with varying counts ────────────────────────────────────
_retry_id = _sensor_readback_id
for relay in RELAYS:
    for count in [1, 2, 3, 4, 5]:
        for value, label in [(1, "on"), (0, "off")]:
            _retry_id += 1
            TASKS.append({
                "task_id": tid(_retry_id),
                "category": "retry_varying_count",
                "prompt": f"Try up to {count} times to turn {label} {relay} and verify it reads back as {value}; halt after the retry loop.",
                "allowed_devices": [relay],
                "expected_status": "success",
                "expected_mir": (
                    f"task {tid(_retry_id)} {{\n"
                    f"  require cap({relay})\n"
                    f"  retry {count} times {{\n"
                    f"    set {relay} = {value}\n"
                    f"    readback {relay} expect {value}\n"
                    f"  }}\n"
                    f"  halt\n}}"
                ),
            })

# ── Category 4: retry_fail (mismatched expectation) ──────────────────────────
_retry_fail_id = _retry_id
for relay in RELAYS:
    for count in [2, 3]:
        for set_val, expect_val, label in [(1, 0, "on but expect 0"), (0, 1, "off but expect 1")]:
            _retry_fail_id += 1
            TASKS.append({
                "task_id": tid(_retry_fail_id),
                "category": "retry_fail",
                "prompt": f"Try up to {count} times to turn {label.split(' but')[0]} {relay}, but verify it reads back as {expect_val}; halt after the retry loop.",
                "allowed_devices": [relay],
                "expected_status": "success",
                "expected_mir": (
                    f"task {tid(_retry_fail_id)} {{\n"
                    f"  require cap({relay})\n"
                    f"  retry {count} times {{\n"
                    f"    set {relay} = {set_val}\n"
                    f"    readback {relay} expect {expect_val}\n"
                    f"  }}\n"
                    f"  halt\n}}"
                ),
            })

# ── Category 5: retry with wait ──────────────────────────────────────────────
_retry_wait_id = _retry_fail_id
for relay in RELAYS:
    for wait_ms in WAIT_MS:
        for value, label in [(1, "on"), (0, "off")]:
            _retry_wait_id += 1
            TASKS.append({
                "task_id": tid(_retry_wait_id),
                "category": "retry_wait",
                "prompt": f"Try up to 3 times to turn {label} {relay}, wait {wait_ms}ms, verify it reads back as {value}, and halt after the retry loop.",
                "allowed_devices": [relay],
                "expected_status": "success",
                "expected_mir": (
                    f"task {tid(_retry_wait_id)} {{\n"
                    f"  require cap({relay})\n"
                    f"  retry 3 times {{\n"
                    f"    set {relay} = {value}\n"
                    f"    wait {wait_ms}ms\n"
                    f"    readback {relay} expect {value}\n"
                    f"  }}\n"
                    f"  halt\n}}"
                ),
            })

# ── Category 6: multi-device readback ────────────────────────────────────────
_multi_id = _retry_wait_id
# Both relays, various on/off combinations
for v1, l1 in [(1, "on"), (0, "off")]:
    for v2, l2 in [(1, "on"), (0, "off")]:
        _multi_id += 1
        TASKS.append({
            "task_id": tid(_multi_id),
            "category": "multi_device_readback",
            "prompt": f"Turn {l1} relay1 and verify it reads back as {v1}, then turn {l2} relay2 and verify it reads back as {v2}; halt.",
            "allowed_devices": ["relay1", "relay2"],
            "expected_status": "success",
            "expected_mir": (
                f"task {tid(_multi_id)} {{\n"
                f"  require cap(relay1)\n"
                f"  require cap(relay2)\n"
                f"  set relay1 = {v1}\n"
                f"  readback relay1 expect {v1}\n"
                f"  set relay2 = {v2}\n"
                f"  readback relay2 expect {v2}\n"
                f"  halt\n}}"
            ),
        })

# ── Category 7: multi-device with sensor + relay readback ────────────────────
_multi_sensor_id = _multi_id
for sensor in SENSORS:
    for relay in RELAYS:
        for value, label in [(1, "on"), (0, "off")]:
            _multi_sensor_id += 1
            TASKS.append({
                "task_id": tid(_multi_sensor_id),
                "category": "multi_device_sensor_relay",
                "prompt": f"Turn {label} {relay}, verify {relay} reads back as {value}, then read {sensor} and halt.",
                "allowed_devices": [relay, sensor],
                "expected_status": "success",
                "expected_mir": (
                    f"task {tid(_multi_sensor_id)} {{\n"
                    f"  require cap({relay})\n"
                    f"  require cap({sensor})\n"
                    f"  set {relay} = {value}\n"
                    f"  readback {relay} expect {value}\n"
                    f"  read {sensor}\n"
                    f"  halt\n}}"
                ),
            })

# ── Category 8: long sequences ───────────────────────────────────────────────
_long_id = _multi_sensor_id
for relay in RELAYS:
    for wait_ms in [50, 100, 200]:
        _long_id += 1
        TASKS.append({
            "task_id": tid(_long_id),
            "category": "long_sequence",
            "prompt": f"Turn on {relay}, verify it, wait {wait_ms}ms, turn off {relay}, verify it reads back as 0, and halt.",
            "allowed_devices": [relay],
            "expected_status": "success",
            "expected_mir": (
                f"task {tid(_long_id)} {{\n"
                f"  require cap({relay})\n"
                f"  set {relay} = 1\n"
                f"  readback {relay} expect 1\n"
                f"  wait {wait_ms}ms\n"
                f"  set {relay} = 0\n"
                f"  readback {relay} expect 0\n"
                f"  halt\n}}"
            ),
        })

# ── Category 9: retry + sensor read after retry ─────────────────────────────
_retry_sensor_id = _long_id
for sensor in SENSORS:
    for relay in RELAYS:
        _retry_sensor_id += 1
        TASKS.append({
            "task_id": tid(_retry_sensor_id),
            "category": "retry_then_sensor",
            "prompt": f"Try up to 2 times to turn on {relay} and verify it reads back as 1, then read {sensor} and halt.",
            "allowed_devices": [relay, sensor],
            "expected_status": "success",
            "expected_mir": (
                f"task {tid(_retry_sensor_id)} {{\n"
                f"  require cap({relay})\n"
                f"  require cap({sensor})\n"
                f"  retry 2 times {{\n"
                f"    set {relay} = 1\n"
                f"    readback {relay} expect 1\n"
                f"  }}\n"
                f"  read {sensor}\n"
                f"  halt\n}}"
            ),
        })

# ── Category 10: toggle with readback (on-verify-off-verify cycle) ───────────
_toggle_id = _retry_sensor_id
for relay in RELAYS:
    for count in [2, 3]:
        _toggle_id += 1
        TASKS.append({
            "task_id": tid(_toggle_id),
            "category": "toggle_readback",
            "prompt": f"Toggle {relay} {count} times: each cycle turns on {relay} and verifies, then turns off {relay} and verifies; halt after all cycles.",
            "allowed_devices": [relay],
            "expected_status": "success",
            "expected_mir": (
                f"task {tid(_toggle_id)} {{\n"
                f"  require cap({relay})\n"
                f"  repeat {count} times {{\n"
                f"    set {relay} = 1\n"
                f"    readback {relay} expect 1\n"
                f"    set {relay} = 0\n"
                f"    readback {relay} expect 0\n"
                f"  }}\n"
                f"  halt\n}}"
            ),
        })

# ── Category 11: retry with different relay per iteration (cross-device) ────
_cross_id = _toggle_id
for count in [2, 3]:
    _cross_id += 1
    TASKS.append({
        "task_id": tid(_cross_id),
        "category": "cross_device_retry",
        "prompt": f"Repeat {count} times: turn on relay1 and verify, then turn on relay2 and verify; halt after all cycles.",
        "allowed_devices": ["relay1", "relay2"],
        "expected_status": "success",
        "expected_mir": (
            f"task {tid(_cross_id)} {{\n"
            f"  require cap(relay1)\n"
            f"  require cap(relay2)\n"
            f"  repeat {count} times {{\n"
            f"    set relay1 = 1\n"
            f"    readback relay1 expect 1\n"
            f"    set relay2 = 1\n"
            f"    readback relay2 expect 1\n"
            f"  }}\n"
            f"  halt\n}}"
        ),
    })

# ── Category 12: readback all sensors ────────────────────────────────────────
_all_sensor_id = _cross_id
_all_sensor_id += 1
TASKS.append({
    "task_id": tid(_all_sensor_id),
    "category": "readback_all_sensors",
    "prompt": "Read water_sensor, then read temperature_sensor, then read humidity_sensor, and halt.",
    "allowed_devices": ["water_sensor", "temperature_sensor", "humidity_sensor"],
    "expected_status": "success",
    "expected_mir": (
        f"task {tid(_all_sensor_id)} {{\n"
        f"  require cap(water_sensor)\n"
        f"  require cap(temperature_sensor)\n"
        f"  require cap(humidity_sensor)\n"
        f"  read water_sensor\n"
        f"  read temperature_sensor\n"
        f"  read humidity_sensor\n"
        f"  halt\n}}"
    ),
})

_all_sensor_id += 1
TASKS.append({
    "task_id": tid(_all_sensor_id),
    "category": "readback_all_sensors",
    "prompt": "Turn on relay1, verify it, read all three sensors (water_sensor, temperature_sensor, humidity_sensor), then turn off relay1 and verify; halt.",
    "allowed_devices": ["relay1", "water_sensor", "temperature_sensor", "humidity_sensor"],
    "expected_status": "success",
    "expected_mir": (
        f"task {tid(_all_sensor_id)} {{\n"
        f"  require cap(relay1)\n"
        f"  require cap(water_sensor)\n"
        f"  require cap(temperature_sensor)\n"
        f"  require cap(humidity_sensor)\n"
        f"  set relay1 = 1\n"
        f"  readback relay1 expect 1\n"
        f"  read water_sensor\n"
        f"  read temperature_sensor\n"
        f"  read humidity_sensor\n"
        f"  set relay1 = 0\n"
        f"  readback relay1 expect 0\n"
        f"  halt\n}}"
    ),
})


def main() -> int:
    out = Path(__file__).resolve().parent.parent / "data" / "tasks_v3_expanded.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for task in TASKS:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")

    # Print category summary
    from collections import Counter
    cats = Counter(t["category"] for t in TASKS)
    print(f"Generated {len(TASKS)} tasks -> {out}")
    print("Category breakdown:")
    for cat, count in sorted(cats.items()):
        print(f"  {cat}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
