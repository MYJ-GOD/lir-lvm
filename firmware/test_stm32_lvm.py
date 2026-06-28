#!/usr/bin/env python3
"""
Test script for STM32 LVM firmware.
Sends a simple bytecode sequence and checks the response.

Usage:
  python test_stm32_lvm.py COM_PORT

Example:
  python test_stm32_lvm.py COM3

Test cases:
  1. GTWAY 5; HALT — should return OK
  2. GTWAY 5; LIT 1; IOW 5; HALT — should return OK (relay1 on)
  3. GTWAY 5; LIT 0; IOW 5; HALT — should return OK (relay1 off)
  4. LIT 1; IOW 5; HALT — should return FAULT (unauthorized)
"""

import sys
import serial
import struct
import time

def encode_uvarint(v):
    """Encode unsigned varint."""
    out = []
    while v > 0x7F:
        out.append((v & 0x7F) | 0x80)
        v >>= 7
    out.append(v)
    return bytes(out)

def encode_zigzag64(v):
    """Encode signed integer as zigzag."""
    return encode_uvarint((v << 1) ^ (v >> 63))

def build_bytecode(ops):
    """Build bytecode from list of (opcode, operand) tuples."""
    bc = bytearray()
    for op, arg in ops:
        bc.extend(encode_uvarint(op))
        if arg is not None:
            bc.extend(encode_uvarint(arg))
    return bytes(bc)

def send_and_recv(ser, bytecode):
    """Send bytecode and receive response."""
    # Send: [4-byte LE length][bytecode]
    pkt = struct.pack('<I', len(bytecode)) + bytecode
    ser.write(pkt)
    ser.flush()

    # Wait for response
    time.sleep(0.1)
    if ser.in_waiting < 4:
        time.sleep(0.5)
    if ser.in_waiting < 4:
        return None, "No response"

    # Read length
    len_buf = ser.read(4)
    resp_len = struct.unpack('<I', len_buf)[0]

    # Read response
    resp = ser.read(resp_len)
    if len(resp) < 1:
        return None, "Empty response"

    # Parse response
    if resp[-1] == 0x01:
        # OK response
        return {'status': 'OK', 'raw': resp.hex()}, None
    else:
        # FAULT response
        return {'status': 'FAULT', 'raw': resp.hex()}, None

# Opcodes (matching firmware)
OP_GTWAY = 80
OP_WAIT  = 81
OP_HALT  = 82
OP_LIT   = 30
OP_IOW   = 70
OP_IOR   = 71

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_stm32_lvm.py COM_PORT")
        print("Example: python test_stm32_lvm.py COM3")
        sys.exit(1)

    port = sys.argv[1]
    print(f"Connecting to {port}...")
    try:
        ser = serial.Serial(port, 115200, timeout=2)
        time.sleep(2)  # Wait for STM32 to reset after serial connection
        print("Connected.\n")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Test cases
    tests = [
        {
            'name': 'Test 1: GTWAY 5; HALT (basic capability + halt)',
            'ops': [(OP_GTWAY, 5), (OP_HALT, None)],
            'expect': 'OK',
        },
        {
            'name': 'Test 2: GTWAY 5; LIT 1; IOW 5; HALT (relay1 ON)',
            'ops': [(OP_GTWAY, 5), (OP_LIT, 1), (OP_IOW, 5), (OP_HALT, None)],
            'expect': 'OK',
        },
        {
            'name': 'Test 3: GTWAY 5; LIT 0; IOW 5; HALT (relay1 OFF)',
            'ops': [(OP_GTWAY, 5), (OP_LIT, 0), (OP_IOW, 5), (OP_HALT, None)],
            'expect': 'OK',
        },
        {
            'name': 'Test 4: LIT 1; IOW 5; HALT (unauthorized — expect FAULT)',
            'ops': [(OP_LIT, 1), (OP_IOW, 5), (OP_HALT, None)],
            'expect': 'FAULT',
        },
        {
            'name': 'Test 5: GTWAY 5; GTWAY 1; LIT 1; IOW 5; WAIT 500; IOR 1; HALT (full pipeline)',
            'ops': [(OP_GTWAY, 5), (OP_GTWAY, 1), (OP_LIT, 1), (OP_IOW, 5),
                    (OP_WAIT, 500), (OP_IOR, 1), (OP_HALT, None)],
            'expect': 'OK',
        },
    ]

    passed = 0
    failed = 0

    for t in tests:
        print(f"  {t['name']}")
        bc = build_bytecode(t['ops'])
        print(f"    Bytecode ({len(bc)} bytes): {bc.hex()}")

        resp, err = send_and_recv(ser, bc)
        if err:
            print(f"    ERROR: {err}")
            failed += 1
        elif resp['status'] == t['expect']:
            print(f"    PASS — {resp['status']} (raw: {resp['raw']})")
            passed += 1
        else:
            print(f"    FAIL — expected {t['expect']}, got {resp['status']} (raw: {resp['raw']})")
            failed += 1
        print()

    ser.close()

    print(f"Results: {passed}/{passed+failed} passed")
    if failed == 0:
        print("All tests passed! STM32 LVM firmware is working.")
    else:
        print(f"{failed} test(s) failed.")

if __name__ == '__main__':
    main()
