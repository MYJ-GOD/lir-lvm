import math

def wilson(k, n, z=1.96):
    p = k/n
    denom = 1 + z**2/n
    center = (p + z**2/(2*n)) / denom
    margin = z * math.sqrt((p*(1-p) + z**2/(4*n))/n) / denom
    return (round(center - margin, 3), round(center + margin, 3))

print("=== Wilson CI Verifications ===")
print("113/113:", wilson(113, 113))
print("582/600:", wilson(582, 600))
print("598/600 (IR valid, random):", wilson(598, 600))
print("91/96 (closed loop):", wilson(91, 96))
print("100/113 (success@1):", wilson(100, 113))
print("13/113 (success@2):", wilson(13, 113))
print("98/113 (LIR semantic):", wilson(98, 113))
print("90/113 (JSON semantic):", wilson(90, 113))
print("78/113 (Python basic):", wilson(78, 113))
print("13/15 (control flow):", wilson(13, 15))
print("102/113 (qwen3:8b):", wilson(102, 113))
print("112/113 (deepseek-v4-pro):", wilson(112, 113))

print("\n=== Calculation Verifications ===")
print("(77.54 - 40.00) / 77.54 =", (77.54 - 40.00) / 77.54)
print("188.1 / 10.9 =", 188.1 / 10.9)
print("285.9 / 108.0 =", 285.9 / 108.0)
print("150.8 / 10.9 =", 150.8 / 10.9)
print("150.8 / 86.1 =", 150.8 / 86.1)

print("\n=== Random task sum verification ===")
cats = [50,50,50,50,50,50,50,46,45,48,45,48]
print("Sum of per-category passes:", sum(cats), "/ 600")
print("TSR:", sum(cats)/600)

print("\n=== Real-world task sum verification (29-task set) ===")
# Real-world set = 19 sequential + 10 closed-loop (retry/readback) = 29 tasks
seq_pass, seq_total = 17, 19          # sequential IoT patterns
loop_pass, loop_total = 6, 10         # closed-loop retry/readback patterns
total_pass = seq_pass + loop_pass
total_tasks = seq_total + loop_total
print(f"Sequential pass: {seq_pass}/{seq_total} = {seq_pass/seq_total:.3f}")
print(f"Closed-loop pass (v4): {loop_pass}/{loop_total} = {loop_pass/loop_total:.3f}")
print(f"Total v4: {total_pass}/{total_tasks} = {total_pass/total_tasks:.3f}")

# JSON baseline on the same 29-task set
json_pass = 25
print(f"JSON total: {json_pass}/{total_tasks} = {json_pass/total_tasks:.3f}")

print("\n=== Temperature sweep monotonic check ===")
tsr = [1.000, 0.985, 0.941, 0.882, 0.858, 0.847]
ir = [1.000, 0.988, 0.971, 0.950, 0.914, 0.926]
print("TSR monotonic decreasing:", all(tsr[i] >= tsr[i+1] for i in range(len(tsr)-1)))
print("IR Valid monotonic decreasing:", all(ir[i] >= ir[i+1] for i in range(len(ir)-1)))
if not all(ir[i] >= ir[i+1] for i in range(len(ir)-1)):
    for i in range(len(ir)-1):
        if ir[i] < ir[i+1]:
            print(f"  VIOLATION: IR Valid at temp={i*0.2} ({ir[i]}) < temp={(i+1)*0.2} ({ir[i+1]})")
