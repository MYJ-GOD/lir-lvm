#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from run_generation_eval import load_jsonl, normalize_candidate_mir


DEVICE_NAMES = {
    "relay1",
    "relay2",
    "water_sensor",
    "temperature_sensor",
    "humidity_sensor",
}


def extract_json_block(text: str) -> Optional[str]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    start = cleaned.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(cleaned)):
        if cleaned[i] == "{":
            depth += 1
        elif cleaned[i] == "}":
            depth -= 1
            if depth == 0:
                return cleaned[start : i + 1]
    return None


def canonicalize_expected(mir_text: str) -> Optional[Tuple[Tuple[str, ...], ...]]:
    lines = [line.strip() for line in mir_text.splitlines() if line.strip()]
    actions: List[Tuple[str, ...]] = []
    for line in lines:
        if line.startswith("task ") or line == "}":
            continue
        m = re.fullmatch(r"require cap\(([^)]+)\)", line)
        if m:
            continue
        m = re.fullmatch(r"set ([A-Za-z0-9_]+) = ([01])", line)
        if m:
            actions.append(("set", m.group(1), m.group(2)))
            continue
        m = re.fullmatch(r"read ([A-Za-z0-9_]+)", line)
        if m:
            actions.append(("read", m.group(1)))
            continue
        m = re.fullmatch(r"wait ([0-9]+)ms", line)
        if m:
            actions.append(("wait", m.group(1)))
            continue
        if line == "halt":
            actions.append(("halt",))
            continue
        return None
    return tuple(actions)


def canonicalize_mir(task_id: str, text: str) -> Optional[Tuple[Tuple[str, ...], ...]]:
    normalized = normalize_candidate_mir(task_id, text)
    return canonicalize_expected(normalized)


def canonicalize_json(text: str) -> Optional[Tuple[Tuple[str, ...], ...]]:
    block = extract_json_block(text)
    if not block:
        return None
    try:
        obj = json.loads(block)
    except Exception:
        return None

    # unwrap single top-level task key
    if isinstance(obj, dict) and len(obj) == 1:
        only_key = next(iter(obj))
        if isinstance(obj[only_key], dict):
            obj = obj[only_key]

    if not isinstance(obj, dict):
        return None

    actions: List[Tuple[str, ...]] = []

    def append_action(device: str, action_name: str) -> bool:
        a = action_name.lower()
        if a in {"open", "on", "enable"}:
            actions.append(("set", device, "1"))
            return True
        if a in {"close", "off", "disable"}:
            actions.append(("set", device, "0"))
            return True
        if a in {"read_state", "read", "get_state", "read_current_value", "read_value"}:
            actions.append(("read", device))
            return True
        if a in {"stop", "halt", "end"}:
            return True
        return False

    def append_wait(value) -> bool:
        try:
            actions.append(("wait", str(int(value))))
            return True
        except Exception:
            return False

    def parse_instruction_item(item: dict, inherited_device: Optional[str] = None) -> bool:
        device = inherited_device
        if not isinstance(item, dict):
            return False
        if isinstance(item.get("device"), str):
            device = item["device"]
        elif isinstance(item.get("id"), str):
            device = item["id"]

        if "action" in item:
            if device is None:
                return False
            if not append_action(device, str(item["action"])):
                return False
        elif item.get("type") == "read":
            if device is None:
                return False
            actions.append(("read", device))
        elif item.get("type") == "wait":
            wait_val = item.get("ms", item.get("time", item.get("delay", item.get("wait"))))
            if wait_val is None or not append_wait(wait_val):
                return False
        elif "delay" in item:
            if not append_wait(item["delay"]):
                return False
        elif "wait" in item:
            if not append_wait(item["wait"]):
                return False
        elif "ms" in item and len(item) <= 3:
            if not append_wait(item["ms"]):
                return False
        elif "next" not in item:
            return False

        if "next" in item:
            nxt = item["next"]
            if not isinstance(nxt, dict):
                return False
            if not parse_instruction_item(nxt, device):
                return False
        return True

    device = obj.get("device")
    action = obj.get("action")
    instruction = obj.get("instruction")
    wait_ms = obj.get("wait_ms") or obj.get("wait") or obj.get("delay_ms")

    if isinstance(obj.get("instructions"), list):
        inherited_device = device if isinstance(device, str) else None
        for item in obj["instructions"]:
            if not parse_instruction_item(item, inherited_device):
                return None
    elif isinstance(obj.get("devices"), list):
        devices = obj["devices"]
        if devices and all(isinstance(x, dict) for x in devices):
            for item in devices:
                dev = item.get("device") or item.get("id")
                if not isinstance(dev, str):
                    return None
                if "action" in item and not append_action(dev, str(item["action"])):
                    return None
            root_wait = obj.get("wait_time") or obj.get("wait_ms") or obj.get("delay_ms")
            if root_wait is not None and not append_wait(root_wait):
                return None
            root_actions = obj.get("actions")
            if isinstance(root_actions, list):
                for item in root_actions:
                    if not parse_instruction_item(item, None):
                        return None
    elif isinstance(obj.get("actions"), list) and isinstance(device, str):
        for item in obj["actions"]:
            if not isinstance(item, dict):
                return None
            if "action" in item:
                if not append_action(device, str(item["action"])):
                    return None
            elif "delay" in item:
                if not append_wait(item["delay"]):
                    return None
            elif "wait" in item:
                if not append_wait(item["wait"]):
                    return None
            elif item.get("type") == "wait":
                if not append_wait(item.get("time", item.get("ms"))):
                    return None
            elif item.get("type") in {"stop", "halt"}:
                continue
            else:
                return None
    elif isinstance(action, str) and isinstance(device, str):
        if not append_action(device, action):
            return None
        if wait_ms is not None:
            if not append_wait(wait_ms):
                return None
    elif isinstance(instruction, str) and isinstance(device, str):
        if not append_action(device, instruction):
            return None
    else:
        # support {"relay1": {"action": "off", "wait": 200}}
        device_keys = [k for k in obj.keys() if k in DEVICE_NAMES]
        if len(device_keys) == 1 and isinstance(obj[device_keys[0]], dict):
            device = device_keys[0]
            inner = obj[device]
            if "action" in inner:
                if not append_action(device, str(inner["action"])):
                    return None
            else:
                return None
            inner_wait = inner.get("wait_ms") or inner.get("wait") or inner.get("delay_ms")
            if inner_wait is not None and not append_wait(inner_wait):
                return None
        elif len(device_keys) == 1 and isinstance(obj[device_keys[0]], list):
            device = device_keys[0]
            for item in obj[device]:
                if not isinstance(item, dict):
                    return None
                if "action" in item:
                    if not append_action(device, str(item["action"])):
                        return None
                elif "delay" in item:
                    if not append_wait(item["delay"]):
                        return None
                elif item.get("type") == "wait":
                    if not append_wait(item.get("time", item.get("ms"))):
                        return None
                else:
                    return None
        else:
            return None

    actions.append(("halt",))
    return tuple(actions)


def canonicalize_python(text: str) -> Optional[Tuple[Tuple[str, ...], ...]]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        m = re.search(r"```(?:python)?\s*([\s\S]*?)```", cleaned, re.IGNORECASE)
        if m:
            cleaned = m.group(1).strip()
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    actions: List[Tuple[str, ...]] = []
    for line in lines:
        # ignore pure print and assignments around read
        if line.startswith("print("):
            continue
        m = re.search(r"(relay[12])\.(on|open)\(\)", line)
        if m:
            actions.append(("set", m.group(1), "1"))
            continue
        m = re.search(r"(relay[12])\.(off|close)\(\)", line)
        if m:
            actions.append(("set", m.group(1), "0"))
            continue
        m = re.search(r"(relay[12]|water_sensor|temperature_sensor|humidity_sensor)\.(read_state|read)\(\)", line)
        if m:
            actions.append(("read", m.group(1)))
            continue
        m = re.search(r"(?:time\.)?sleep\(([\d\.]+)\)", line)
        if m:
            raw = m.group(1)
            try:
                if "." in raw:
                    ms = int(round(float(raw) * 1000))
                else:
                    ms = int(raw)
                actions.append(("wait", str(ms)))
            except Exception:
                return None
            continue
        m = re.search(r"(water_sensor|temperature_sensor|humidity_sensor)\.read\(\)", line)
        if m:
            actions.append(("read", m.group(1)))
            continue
        m = re.search(r"(relay[12])\.stop\(\)", line)
        if m:
            continue
        # unsupported line
        return None
    actions.append(("halt",))
    return tuple(actions)


def equivalent(expected: Tuple[Tuple[str, ...], ...], observed: Optional[Tuple[Tuple[str, ...], ...]]) -> bool:
    return observed == expected


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze semantic equivalence for token comparison outputs.")
    parser.add_argument("--tasks", default=str(Path(__file__).resolve().parent.parent / "data" / "tasks_v1.jsonl"))
    parser.add_argument("--token-csv", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    tasks = load_jsonl(Path(args.tasks))
    expected_map = {task["task_id"]: canonicalize_expected(task["expected_mir"]) for task in tasks}

    rows = list(csv.DictReader(Path(args.token_csv).open("r", encoding="utf-8-sig")))
    analyzed: List[dict] = []
    by_task: Dict[str, Dict[str, dict]] = {}
    for row in rows:
        task_id = row["task_id"]
        fmt = row["format"]
        resp = row["response"]
        expected = expected_map[task_id]
        if fmt == "MIR":
            observed = canonicalize_mir(task_id, resp)
        elif fmt == "JSON":
            observed = canonicalize_json(resp)
        elif fmt == "PYTHON":
            observed = canonicalize_python(resp)
        else:
            observed = None
        ok = expected is not None and equivalent(expected, observed)
        out = dict(row)
        out["semantic_ok"] = "1" if ok else "0"
        out["expected_semantics"] = json.dumps(expected, ensure_ascii=False)
        out["observed_semantics"] = json.dumps(observed, ensure_ascii=False)
        analyzed.append(out)
        by_task.setdefault(task_id, {})[fmt] = out

    out_csv = Path(args.out_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8-sig", newline="") as fh:
        fieldnames = list(analyzed[0].keys()) if analyzed else []
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(analyzed)

    triple_ok = []
    for task_id, group in by_task.items():
        if all(fmt in group and group[fmt]["semantic_ok"] == "1" for fmt in ("MIR", "JSON", "PYTHON")):
            triple_ok.append(task_id)

    lines = [
        "# Token Semantic Analysis",
        "",
        f"- total_tasks: {len(tasks)}",
        f"- triple_equivalent_tasks: {len(triple_ok)}",
        "",
        "## Per-format semantic pass counts",
        "",
    ]
    for fmt in ("MIR", "JSON", "PYTHON"):
        count = sum(1 for row in analyzed if row["format"] == fmt and row["semantic_ok"] == "1")
        lines.append(f"- {fmt}: {count}/{len(tasks)} = {count/len(tasks):.3f}")
    lines += ["", "## Triple-equivalent task IDs", ""]
    if triple_ok:
        for task_id in triple_ok:
            lines.append(f"- {task_id}")
    else:
        lines.append("- none")

    if triple_ok:
        lines += ["", "## Token statistics on triple-equivalent subset", ""]
        for fmt in ("MIR", "JSON", "PYTHON"):
            subset = [row for row in analyzed if row["format"] == fmt and row["task_id"] in triple_ok]
            avg_in = sum(float(row["prompt_eval_count"]) for row in subset) / len(subset)
            avg_out = sum(float(row["eval_count"]) for row in subset) / len(subset)
            avg_bytes = sum(float(row["output_bytes"]) for row in subset) / len(subset)
            lines.append(f"- {fmt}: avg_input_tokens={avg_in:.2f}, avg_output_tokens={avg_out:.2f}, avg_output_bytes={avg_bytes:.2f}")

    Path(args.out_md).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(out_csv))
    print(str(args.out_md))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
