# LVM — Full Reference Implementation (C)

This directory contains the **complete, general-purpose LVM** referenced in the
paper (Section *Instruction Set and Bounded-Execution Profile*, Table
*tab:full_isa*). It is the host-side C implementation of the virtual machine; the
14-instruction **bounded-execution profile** that is formalized and deployed to
the ESP8266/STM32 firmware is a subset of the instruction set implemented here.

## Scope of this directory vs. the rest of the package

| Component | Where | What it covers |
|---|---|---|
| Full LVM (this dir) | `vm_full/` | General-purpose instruction set (~50 opcodes): functions, loops, arrays, dynamic memory, arithmetic, debugging. Implemented and unit-tested. |
| Bounded profile | `tools/` (Python), `固件烧录/`, `firmware/` | The 14-instruction subset. Formalized in the paper and exercised by **all reported experiments** (compression, fuzzing, energy, task success). |

The paper's formal safety analysis and on-device evaluation concern the **bounded
profile only**. The full VM is provided here so that the breadth claim in the
paper is inspectable; it is *not* the artifact behind the experimental numbers.

## Files

```
vm_full/
├── include/
│   ├── m_vm.h        # opcode table, fault codes, VM state, public API
│   ├── disasm.h      # disassembler interface
│   └── validator.h   # static validator interface
└── src/
    ├── m_vm.c        # VM core: decoder + stack machine + guards
    ├── disasm.c      # bytecode disassembler
    ├── validator.c   # static structural validator
    └── main.c        # test harness / CLI entry point
```

Dependencies: C standard library only (`stdint`, `stdbool`, `string`, `stdio`,
`stdlib`, `stdarg`). No external libraries.

## Build

```sh
cc -std=c11 -Iinclude -Wall -o lvm src/m_vm.c src/disasm.c src/validator.c src/main.c
./lvm
```

(Any C11 compiler works: `gcc`, `clang`, or MSVC `cl`.)

## Opcode naming: source vs. paper

The source uses an `M_` prefix for historical reasons (the project was originally
named *M-Language*). The paper drops the prefix. The mapping is direct:

| Source (`m_vm.h`) | Paper |
|---|---|
| `M_LIT` | `LIT` |
| `M_GTWAY` | `GTWAY` |
| `M_IOW` / `M_IOR` | `IOW` / `IOR` |
| `M_WAIT` / `M_HALT` | `WAIT` / `HALT` |
| `M_EQ`, `M_JZ`, `M_JMP`, `M_DUP`, `M_DRP`, `M_SUB` | `EQ`, `JZ`, `JMP`, `DUP`, `DRP`, `SUB` |
| `M_FN`/`M_CL`/`M_RT`, `M_IF`/`M_WH`/`M_FR`, `M_NEWARR`/`M_ALLOC`, ... | functions, loops, arrays, memory (outside the bounded profile) |

See `include/m_vm.h` for the authoritative, fully commented opcode table.
