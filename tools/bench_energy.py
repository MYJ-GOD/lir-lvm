"""
bench_energy.py  —  P0-2 energy benchmark: UM25C + ESP8266 synchronised sampler.

Usage (one group at a time; flash the corresponding firmware first):
    python tools/bench_energy.py --group bytecode --out result/E_POWER/energy_bytecode.csv
    python tools/bench_energy.py --group json     --out result/E_POWER/energy_json.csv
    python tools/bench_energy.py --group native   --out result/E_POWER/energy_native.csv

Ports default to the confirmed mapping:
    ESP8266 serial log : COM3  (115200)
    UM25C  Bluetooth   : COM5  (115200)

How it works:
  - Two threads run concurrently: one reads UM25C power frames (~2 Hz),
    one reads ESP8266 TICK lines from the tight-loop firmware.
  - Both streams are timestamped with time.monotonic().
  - After collection (--seconds, default 60 s), the script:
      1. Averages the UM25C power samples  → mean_power_mW
      2. Uses consecutive TICK lines to compute µs/task (interpretation cost)
      3. energy_per_task_uJ = mean_power_mW * us_per_task / 1000
  - Output CSV: group, mean_power_mW, us_per_task, uJ_per_task, n_power_samples, n_ticks
"""

import argparse, csv, os, struct, threading, time
import serial  # pyserial

# UM25C binary frame: 0xF0 request → 130-byte response
_UM25C_REQ   = b'\xf0'
_UM25C_FRAME = 130

def _parse_um25c(frame: bytes) -> dict | None:
    """Parse a 130-byte UM25C frame; return dict or None on bad frame."""
    if len(frame) < 130:
        return None
    v_mv  = ((frame[2] << 8) | frame[3])        # mV  (divide by 1000 for V)
    i_ua  = ((frame[4] << 8) | frame[5])        # 0.1 mA units → µA
    mw    = ((frame[8] << 8) | frame[9])        # mW
    return {"v_mv": v_mv, "i_0_1ma": i_ua, "mw": mw}

def _um25c_reader(port: str, samples: list, stop: threading.Event):
    """Background thread: poll UM25C and append (timestamp, mw) to samples."""
    try:
        with serial.Serial(port, 115200, timeout=2) as s:
            while not stop.is_set():
                s.reset_input_buffer()
                s.write(_UM25C_REQ)
                s.flush()
                frame = s.read(_UM25C_FRAME)
                parsed = _parse_um25c(frame)
                if parsed:
                    samples.append((time.monotonic(), parsed["mw"]))
                time.sleep(0.45)  # UM25C updates ~2 Hz
    except Exception as e:
        print(f"[UM25C] error: {e}")

def _esp_reader(port: str, ticks: list, stop: threading.Event):
    """Background thread: read ESP8266 TICK lines and record timestamps."""
    try:
        with serial.Serial(port, 115200, timeout=1) as s:
            s.reset_input_buffer()
            while not stop.is_set():
                line = s.readline().decode("ascii", errors="ignore").strip()
                if line.startswith("BANNER"):
                    print(f"[ESP]  {line}")
                elif line.startswith("TICK"):
                    ticks.append((time.monotonic(), line))
    except Exception as e:
        print(f"[ESP] error: {e}")

def run(group: str, esp_port: str, um25c_port: str, seconds: int, out_path: str):
    power_samples: list = []
    ticks: list = []
    stop = threading.Event()

    t_um = threading.Thread(target=_um25c_reader, args=(um25c_port, power_samples, stop), daemon=True)
    t_esp = threading.Thread(target=_esp_reader, args=(esp_port, ticks, stop), daemon=True)

    print(f"[bench] group={group}  ESP={esp_port}  UM25C={um25c_port}  duration={seconds}s")
    print("[bench] waiting for ESP banner…")
    t_um.start()
    t_esp.start()

    time.sleep(seconds)
    stop.set()
    t_um.join(timeout=3)
    t_esp.join(timeout=3)

    # --- compute metrics ---
    if not power_samples:
        print("[bench] ERROR: no power samples from UM25C. Check COM5 / Bluetooth pairing.")
        return
    if len(ticks) < 2:
        print(f"[bench] ERROR: only {len(ticks)} TICK line(s). Is the correct firmware flashed?")
        return

    mean_mw = sum(s[1] for s in power_samples) / len(power_samples)

    # us_per_task: average µs per single task execution derived from consecutive TICKs
    # TICK line format: "TICK <reps> <elapsed_us> <top> <fault>"
    us_per_rep_list = []
    prev_reps, prev_us = None, None
    for _, line in ticks:
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            reps = int(parts[1]); elapsed = int(parts[2])
        except ValueError:
            continue
        if prev_reps is not None and reps > prev_reps:
            delta_us = elapsed - prev_us
            delta_reps = reps - prev_reps
            us_per_rep_list.append(delta_us / delta_reps)
        prev_reps, prev_us = reps, elapsed

    if not us_per_rep_list:
        print("[bench] ERROR: could not compute µs/task from TICK lines.")
        return

    us_per_task = sum(us_per_rep_list) / len(us_per_rep_list)
    uj_per_task = mean_mw * us_per_task / 1000.0  # mW * µs / 1000 = µJ

    print(f"\n{'='*50}")
    print(f"group          : {group}")
    print(f"mean_power_mW  : {mean_mw:.2f} mW  (n={len(power_samples)})")
    print(f"us_per_task    : {us_per_task:.2f} us/task  (n={len(us_per_rep_list)} intervals)")
    print(f"uJ_per_task    : {uj_per_task:.4f} uJ/task")
    print(f"{'='*50}\n")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["group", "mean_power_mW", "us_per_task", "uJ_per_task",
                    "n_power_samples", "n_ticks"])
        w.writerow([group, f"{mean_mw:.3f}", f"{us_per_task:.3f}",
                    f"{uj_per_task:.4f}", len(power_samples), len(ticks)])
    print(f"[bench] saved → {out_path}")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--group",    required=True, choices=["bytecode", "json", "native"])
    p.add_argument("--esp",      default="COM3")
    p.add_argument("--um25c",    default="COM5")
    p.add_argument("--seconds",  type=int, default=60)
    p.add_argument("--out",      required=True)
    args = p.parse_args()
    run(args.group, args.esp, args.um25c, args.seconds, args.out)

if __name__ == "__main__":
    main()
