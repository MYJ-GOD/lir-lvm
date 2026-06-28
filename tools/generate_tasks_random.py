#!/usr/bin/env python3
"""
Random task generator for LIR generation evaluation.
Generates tasks from parameterized templates with random device/param selection.
Targets 500+ tasks to address H1 (experiment scale).
"""
from __future__ import annotations

import argparse
import json
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple

# ── Device definitions ──
ACTUATORS = ["relay1", "relay2"]
SENSORS = ["water_sensor", "temperature_sensor", "humidity_sensor"]
ALL_DEVICES = ACTUATORS + SENSORS

# ── Wait values (ms) ──
WAIT_VALUES = [50, 100, 200, 300, 500, 1000, 2000]

# ── Prompt templates (Chinese) ──
PROMPT_TEMPLATES = {
    "single_set": {
        "on": "打开 {device}。",
        "off": "关闭 {device}。",
    },
    "single_read": {
        "read": "读取 {device} 的当前值。",
    },
    "set_wait_halt": {
        "on": "打开 {device}，等待 {wait} 毫秒，然后停止。",
        "off": "关闭 {device}，等待 {wait} 毫秒，然后停止。",
    },
    "wait_read": {
        "read": "等待 {wait} 毫秒，然后读取 {device}。",
    },
    "set_wait_read": {
        "on": "打开 {actuator}，等待 {wait} 毫秒，然后读取 {sensor}。",
        "off": "关闭 {actuator}，等待 {wait} 毫秒，然后读取 {sensor}。",
    },
    "multi_read": {
        "2": "依次读取 {dev1} 和 {dev2} 的值。",
        "3": "依次读取 {dev1}、{dev2} 和 {dev3} 的值。",
    },
    "pulse": {
        "pulse": "对 {device} 发送一个 {wait}ms 脉冲（先打开再关闭）。",
    },
    "set_read_multi": {
        "on": "打开 {actuator}，然后读取 {sensor}。",
        "off": "关闭 {actuator}，然后读取 {sensor}。",
    },
    "multi_set": {
        "both_on": "同时打开 {dev1} 和 {dev2}。",
        "both_off": "同时关闭 {dev1} 和 {dev2}。",
        "mixed": "打开 {dev1}，关闭 {dev2}。",
    },
    "set_wait_multi_read": {
        "on": "打开 {actuator}，等待 {wait} 毫秒，然后依次读取 {s1} 和 {s2}。",
        "off": "关闭 {actuator}，等待 {wait} 毫秒，然后依次读取 {s1} 和 {s2}。",
    },
    "long_sequence": {
        "seq": "打开 {a1}，等待 {w1} 毫秒，读取 {s1}，然后关闭 {a1}，等待 {w2} 毫秒，读取 {s2}。",
    },
    "pulse_read": {
        "pulse": "对 {actuator} 发送 {wait}ms 脉冲，然后读取 {sensor}。",
    },
}


def make_task_id(prefix: str, idx: int) -> str:
    return f"{prefix}_{idx:04d}"


def gen_single_set(task_id: str, rng: random.Random) -> dict:
    device = rng.choice(ACTUATORS)
    value = rng.choice([0, 1])
    action = "on" if value == 1 else "off"
    prompt = PROMPT_TEMPLATES["single_set"][action].format(device=device)
    mir = f"task {task_id} {{\n  require cap({device})\n  set {device} = {value}\n  halt\n}}\n"
    return {
        "task_id": task_id,
        "category": "single_set",
        "prompt": prompt,
        "allowed_devices": [device],
        "expected_status": "success",
        "expected_mir": mir,
    }


def gen_single_read(task_id: str, rng: random.Random) -> dict:
    device = rng.choice(ALL_DEVICES)
    prompt = PROMPT_TEMPLATES["single_read"]["read"].format(device=device)
    mir = f"task {task_id} {{\n  require cap({device})\n  read {device}\n  halt\n}}\n"
    return {
        "task_id": task_id,
        "category": "single_read",
        "prompt": prompt,
        "allowed_devices": [device],
        "expected_status": "success",
        "expected_mir": mir,
    }


def gen_set_wait_halt(task_id: str, rng: random.Random) -> dict:
    device = rng.choice(ACTUATORS)
    value = rng.choice([0, 1])
    wait = rng.choice(WAIT_VALUES)
    action = "on" if value == 1 else "off"
    prompt = PROMPT_TEMPLATES["set_wait_halt"][action].format(device=device, wait=wait)
    mir = f"task {task_id} {{\n  require cap({device})\n  set {device} = {value}\n  wait {wait}ms\n  halt\n}}\n"
    return {
        "task_id": task_id,
        "category": "set_wait_halt",
        "prompt": prompt,
        "allowed_devices": [device],
        "expected_status": "success",
        "expected_mir": mir,
    }


def gen_wait_read(task_id: str, rng: random.Random) -> dict:
    device = rng.choice(ALL_DEVICES)
    wait = rng.choice(WAIT_VALUES)
    prompt = PROMPT_TEMPLATES["wait_read"]["read"].format(device=device, wait=wait)
    mir = f"task {task_id} {{\n  require cap({device})\n  wait {wait}ms\n  read {device}\n  halt\n}}\n"
    return {
        "task_id": task_id,
        "category": "wait_read",
        "prompt": prompt,
        "allowed_devices": [device],
        "expected_status": "success",
        "expected_mir": mir,
    }


def gen_set_wait_read(task_id: str, rng: random.Random) -> dict:
    actuator = rng.choice(ACTUATORS)
    sensor = rng.choice(SENSORS)
    value = rng.choice([0, 1])
    wait = rng.choice(WAIT_VALUES)
    action = "on" if value == 1 else "off"
    prompt = PROMPT_TEMPLATES["set_wait_read"][action].format(
        actuator=actuator, sensor=sensor, wait=wait
    )
    mir = (
        f"task {task_id} {{\n"
        f"  require cap({actuator})\n"
        f"  require cap({sensor})\n"
        f"  set {actuator} = {value}\n"
        f"  wait {wait}ms\n"
        f"  read {sensor}\n"
        f"  halt\n"
        f"}}\n"
    )
    return {
        "task_id": task_id,
        "category": "set_wait_read",
        "prompt": prompt,
        "allowed_devices": [actuator, sensor],
        "expected_status": "success",
        "expected_mir": mir,
    }


def gen_multi_read(task_id: str, rng: random.Random) -> dict:
    n = rng.choice([2, 3])
    devices = rng.sample(ALL_DEVICES, n)
    dev_names = "、".join(devices)
    prompt = PROMPT_TEMPLATES["multi_read"][str(n)].format(
        dev1=devices[0], dev2=devices[1],
        dev3=devices[2] if n == 3 else "",
    )
    caps = "\n".join(f"  require cap({d})" for d in devices)
    reads = "\n".join(f"  read {d}" for d in devices)
    mir = f"task {task_id} {{\n{caps}\n{reads}\n  halt\n}}\n"
    return {
        "task_id": task_id,
        "category": "multi_read",
        "prompt": prompt,
        "allowed_devices": devices,
        "expected_status": "success",
        "expected_mir": mir,
    }


def gen_pulse(task_id: str, rng: random.Random) -> dict:
    device = rng.choice(ACTUATORS)
    wait = rng.choice(WAIT_VALUES)
    prompt = PROMPT_TEMPLATES["pulse"]["pulse"].format(device=device, wait=wait)
    mir = (
        f"task {task_id} {{\n"
        f"  require cap({device})\n"
        f"  set {device} = 1\n"
        f"  wait {wait}ms\n"
        f"  set {device} = 0\n"
        f"  halt\n"
        f"}}\n"
    )
    return {
        "task_id": task_id,
        "category": "pulse",
        "prompt": prompt,
        "allowed_devices": [device],
        "expected_status": "success",
        "expected_mir": mir,
    }


def gen_set_read_multi(task_id: str, rng: random.Random) -> dict:
    actuator = rng.choice(ACTUATORS)
    sensor = rng.choice(SENSORS)
    value = rng.choice([0, 1])
    action = "on" if value == 1 else "off"
    prompt = PROMPT_TEMPLATES["set_read_multi"][action].format(
        actuator=actuator, sensor=sensor
    )
    mir = (
        f"task {task_id} {{\n"
        f"  require cap({actuator})\n"
        f"  require cap({sensor})\n"
        f"  set {actuator} = {value}\n"
        f"  read {sensor}\n"
        f"  halt\n"
        f"}}\n"
    )
    return {
        "task_id": task_id,
        "category": "set_read_multi",
        "prompt": prompt,
        "allowed_devices": [actuator, sensor],
        "expected_status": "success",
        "expected_mir": mir,
    }


def gen_multi_set(task_id: str, rng: random.Random) -> dict:
    devs = rng.sample(ACTUATORS, 2)
    variant = rng.choice(["both_on", "both_off", "mixed"])
    if variant == "both_on":
        v1, v2 = 1, 1
    elif variant == "both_off":
        v1, v2 = 0, 0
    else:
        v1, v2 = 1, 0
    prompt = PROMPT_TEMPLATES["multi_set"][variant].format(dev1=devs[0], dev2=devs[1])
    mir = (
        f"task {task_id} {{\n"
        f"  require cap({devs[0]})\n"
        f"  require cap({devs[1]})\n"
        f"  set {devs[0]} = {v1}\n"
        f"  set {devs[1]} = {v2}\n"
        f"  halt\n"
        f"}}\n"
    )
    return {
        "task_id": task_id,
        "category": "multi_set",
        "prompt": prompt,
        "allowed_devices": list(devs),
        "expected_status": "success",
        "expected_mir": mir,
    }


def gen_set_wait_multi_read(task_id: str, rng: random.Random) -> dict:
    actuator = rng.choice(ACTUATORS)
    sensors = rng.sample(SENSORS, 2)
    value = rng.choice([0, 1])
    wait = rng.choice(WAIT_VALUES)
    action = "on" if value == 1 else "off"
    prompt = PROMPT_TEMPLATES["set_wait_multi_read"][action].format(
        actuator=actuator, wait=wait, s1=sensors[0], s2=sensors[1]
    )
    mir = (
        f"task {task_id} {{\n"
        f"  require cap({actuator})\n"
        f"  require cap({sensors[0]})\n"
        f"  require cap({sensors[1]})\n"
        f"  set {actuator} = {value}\n"
        f"  wait {wait}ms\n"
        f"  read {sensors[0]}\n"
        f"  read {sensors[1]}\n"
        f"  halt\n"
        f"}}\n"
    )
    return {
        "task_id": task_id,
        "category": "set_wait_multi_read",
        "prompt": prompt,
        "allowed_devices": [actuator] + sensors,
        "expected_status": "success",
        "expected_mir": mir,
    }


def gen_long_sequence(task_id: str, rng: random.Random) -> dict:
    a1 = rng.choice(ACTUATORS)
    s1, s2 = rng.sample(SENSORS, 2)
    w1, w2 = rng.sample(WAIT_VALUES, 2)
    # Prompt says "打开...然后关闭..." so first set=1, second set=0
    prompt = PROMPT_TEMPLATES["long_sequence"]["seq"].format(
        a1=a1, w1=w1, s1=s1, w2=w2, s2=s2
    )
    mir = (
        f"task {task_id} {{\n"
        f"  require cap({a1})\n"
        f"  require cap({s1})\n"
        f"  require cap({s2})\n"
        f"  set {a1} = 1\n"
        f"  wait {w1}ms\n"
        f"  read {s1}\n"
        f"  set {a1} = 0\n"
        f"  wait {w2}ms\n"
        f"  read {s2}\n"
        f"  halt\n"
        f"}}\n"
    )
    return {
        "task_id": task_id,
        "category": "long_sequence",
        "prompt": prompt,
        "allowed_devices": [a1, s1, s2],
        "expected_status": "success",
        "expected_mir": mir,
    }


def gen_pulse_read(task_id: str, rng: random.Random) -> dict:
    actuator = rng.choice(ACTUATORS)
    sensor = rng.choice(SENSORS)
    wait = rng.choice(WAIT_VALUES)
    prompt = PROMPT_TEMPLATES["pulse_read"]["pulse"].format(
        actuator=actuator, wait=wait, sensor=sensor
    )
    mir = (
        f"task {task_id} {{\n"
        f"  require cap({actuator})\n"
        f"  require cap({sensor})\n"
        f"  set {actuator} = 1\n"
        f"  wait {wait}ms\n"
        f"  set {actuator} = 0\n"
        f"  read {sensor}\n"
        f"  halt\n"
        f"}}\n"
    )
    return {
        "task_id": task_id,
        "category": "pulse_read",
        "prompt": prompt,
        "allowed_devices": [actuator, sensor],
        "expected_status": "success",
        "expected_mir": mir,
    }


# ── Generator registry ──
GENERATORS = [
    ("single_set", gen_single_set),
    ("single_read", gen_single_read),
    ("set_wait_halt", gen_set_wait_halt),
    ("wait_read", gen_wait_read),
    ("set_wait_read", gen_set_wait_read),
    ("multi_read", gen_multi_read),
    ("pulse", gen_pulse),
    ("set_read_multi", gen_set_read_multi),
    ("multi_set", gen_multi_set),
    ("set_wait_multi_read", gen_set_wait_multi_read),
    ("long_sequence", gen_long_sequence),
    ("pulse_read", gen_pulse_read),
]


def generate_tasks(
    n: int,
    seed: int = 42,
    prefix: str = "RND",
    balanced: bool = True,
) -> List[dict]:
    """Generate n random tasks.

    If balanced=True, tasks are distributed evenly across categories.
    """
    rng = random.Random(seed)
    tasks = []

    if balanced:
        # Round-robin across categories
        for i in range(n):
            cat_name, gen_fn = GENERATORS[i % len(GENERATORS)]
            task_id = make_task_id(prefix, i + 1)
            task = gen_fn(task_id, rng)
            tasks.append(task)
    else:
        # Weighted random (favor simpler categories)
        weights = [3, 3, 3, 2, 2, 2, 2, 2, 2, 1, 1, 1]
        for i in range(n):
            cat_name, gen_fn = rng.choices(GENERATORS, weights=weights, k=1)[0]
            task_id = make_task_id(prefix, i + 1)
            task = gen_fn(task_id, rng)
            tasks.append(task)

    # Deduplicate by expected_mir content
    seen = set()
    unique_tasks = []
    for t in tasks:
        h = hashlib.md5(t["expected_mir"].encode()).hexdigest()
        if h not in seen:
            seen.add(h)
            unique_tasks.append(t)

    return unique_tasks


def main() -> int:
    parser = argparse.ArgumentParser(description="Random task generator for LIR evaluation")
    parser.add_argument("--n", type=int, default=600, help="Target number of tasks")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--prefix", default="RND")
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "data" / "tasks_random_500.jsonl"))
    parser.add_argument("--balanced", action="store_true", default=True, help="Balance across categories")
    args = parser.parse_args()

    tasks = generate_tasks(args.n, args.seed, args.prefix, args.balanced)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    # Print summary
    from collections import Counter
    cats = Counter(t["category"] for t in tasks)
    print(f"Generated {len(tasks)} unique tasks (target: {args.n})")
    print(f"Categories ({len(cats)}):")
    for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    print(f"Written to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
