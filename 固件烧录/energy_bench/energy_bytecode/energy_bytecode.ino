/*
 * P0-2 Energy benchmark - GROUP 1: compact bytecode LVM
 *
 * Measures PURE INTERPRETATION overhead of the compact bytecode representation.
 * The benchmark task (closed-loop V3_006: require cap; retry 3 { set relay1=0;
 * readback relay1 expect 0 }; halt) is hard-coded as bytecode and executed in a
 * tight loop WITHOUT wait()/delay and WITHOUT driving real relays, so that the
 * UM25C reading reflects CPU work spent decoding+interpreting, not IO/idle time.
 *
 * Protocol over USB serial (115200):
 *   On boot prints one banner line:  "BANNER bytecode v3_006 bytes=<n> reps=<R>"
 *   Every REPORT_EVERY reps prints:  "TICK <reps_done> <micros_elapsed> <last_result> <last_fault>"
 *   The host energy script aligns these timestamps with UM25C power samples.
 *
 * VM core (opcodes, varint decode, guards) is copied verbatim from
 * mvm_esp8266_e2_guarded.ino so interpretation cost matches the paper's VM.
 */

#include <Arduino.h>

// ---- Benchmark task: V3_006 compiled bytecode (37 bytes) ----
static const uint8_t TASK_CODE[] = {
  0x50,0x05,0x1e,0x06,0x40,0x65,0x1e,0x1e,0x00,0x46,0x05,0x47,0x05,0x1e,0x00,0x2c,
  0x65,0x02,0x64,0x0a,0x1e,0x02,0x33,0x40,0x65,0x08,0x64,0x1b,0x41,0x1e,0x02,0x64,
  0x04,0x41,0x1e,0x00,0x52
};
static const int TASK_CODE_LEN = (int)sizeof(TASK_CODE);

// Report cadence: print a TICK line every this many task executions.
static const uint32_t REPORT_EVERY = 50000;

// ---- Opcodes (subset; identical to mvm_esp8266_e2_guarded.ino) ----
static const uint32_t OP_B=10, OP_E=11, OP_FN=15, OP_RT=16, OP_CL=17;
static const uint32_t OP_LIT=30, OP_V=31, OP_LET=32, OP_SET=33;
static const uint32_t OP_LT=40, OP_GT=41, OP_LE=42, OP_GE=43, OP_EQ=44;
static const uint32_t OP_ADD=50, OP_SUB=51, OP_MUL=52, OP_DIV=53;
static const uint32_t OP_DUP=64, OP_DRP=65;
static const uint32_t OP_IOW=70, OP_IOR=71;
static const uint32_t OP_GTWAY=80, OP_WAIT=81, OP_HALT=82;
static const uint32_t OP_JMP=100, OP_JZ=101, OP_JNZ=102;
static const uint32_t OP_MOD=110, OP_NEQ=113;

enum FaultCode {
  FAULT_NONE=0, FAULT_STACK_OVERFLOW=1, FAULT_STACK_UNDERFLOW=2,
  FAULT_LOCALS_OOB=5, FAULT_PC_OOB=7, FAULT_DIV_BY_ZERO=8, FAULT_MOD_BY_ZERO=9,
  FAULT_UNKNOWN_OP=10, FAULT_STEP_LIMIT=11, FAULT_BAD_ENCODING=13,
  FAULT_UNAUTHORIZED=14
};

static const int STACK_SIZE=256;
static const int CODE_MAX=1024;
static const uint32_t STEP_LIMIT=20000;
static const int LOCALS_SIZE=64;

static uint8_t code_buf[CODE_MAX];
static int code_len=0;
static int pc=0;
static int64_t stack[STACK_SIZE];
static int sp=-1;
static int64_t locals[LOCALS_SIZE];
static uint8_t caps[32];
static uint32_t steps=0;
static FaultCode fault=FAULT_NONE;
static int token_offsets[CODE_MAX];
static int byte_to_token[CODE_MAX];
static int token_count=0;
static int last_op_index=-1;

// Simulated relay state (NOT driven to real pins, to isolate interpretation cost)
static int sim_relay[8] = {0,0,0,0,0,0,0,0};

static void caps_clear(){ memset(caps,0,sizeof(caps)); }
static void caps_add(uint32_t id){ if(id>255)return; caps[id>>3]|=(1u<<(id&7)); }
static bool caps_has(uint32_t id){ if(id>255)return false; return (caps[id>>3]&(1u<<(id&7)))!=0; }

static bool decode_uvarint(const uint8_t* buf,int len,int* p,uint64_t* out){
  uint64_t res=0; int shift=0; int i=*p;
  while(i<len){ uint8_t b=buf[i++]; res|=(uint64_t)(b&0x7F)<<shift;
    if((b&0x80)==0){ *p=i; *out=res; return true; }
    shift+=7; if(shift>=64) return false; }
  return false;
}
static int64_t decode_zigzag64(uint64_t n){ return (int64_t)((n>>1)^(uint64_t)-(int64_t)(n&1)); }
static int32_t decode_zigzag32(uint32_t n){ return (int32_t)((n>>1)^-(int32_t)(n&1)); }
static bool decode_uvarint32(const uint8_t* buf,int len,int* p,uint32_t* out){
  uint32_t res=0; int shift=0; int i=*p;
  while(i<len){ uint8_t b=buf[i++]; res|=(uint32_t)(b&0x7F)<<shift;
    if((b&0x80)==0){ *p=i; *out=res; return true; }
    shift+=7; if(shift>=32) return false; }
  return false;
}
static bool decode_svarint32(const uint8_t* buf,int len,int* p,int32_t* out){
  uint32_t u=0; if(!decode_uvarint32(buf,len,p,&u)) return false; *out=decode_zigzag32(u); return true;
}
static void push(int64_t v){ if(sp+1>=STACK_SIZE){fault=FAULT_STACK_OVERFLOW;return;} stack[++sp]=v; }
static int64_t pop(){ if(sp<0){fault=FAULT_STACK_UNDERFLOW;return 0;} return stack[sp--]; }

static bool skip_operands(uint32_t op,int* p){
  switch(op){
    case OP_LIT: case OP_V: case OP_LET: case OP_SET: case OP_GTWAY:
    case OP_WAIT: case OP_IOW: case OP_IOR: { uint64_t v=0; return decode_uvarint(code_buf,code_len,p,&v); }
    case OP_FN: { uint64_t a=0; return decode_uvarint(code_buf,code_len,p,&a); }
    case OP_CL: { uint64_t f=0,a=0; return decode_uvarint(code_buf,code_len,p,&f)&&decode_uvarint(code_buf,code_len,p,&a); }
    case OP_JMP: case OP_JZ: case OP_JNZ: { int32_t o=0; return decode_svarint32(code_buf,code_len,p,&o); }
    default: return true;
  }
}
static bool build_token_map(){
  for(int i=0;i<code_len;i++) byte_to_token[i]=-1;
  token_count=0; int p=0;
  while(p<code_len){ int start=p; uint64_t op=0;
    if(!decode_uvarint(code_buf,code_len,&p,&op)) return false;
    if(token_count>=CODE_MAX) return false;
    token_offsets[token_count]=start; byte_to_token[start]=token_count; token_count++;
    if(!skip_operands((uint32_t)op,&p)) return false; }
  return true;
}
static void run_vm(){
  pc=0; sp=-1; steps=0; fault=FAULT_NONE; caps_clear(); last_op_index=-1;
  if(!build_token_map()){ fault=FAULT_BAD_ENCODING; return; }
  while(pc<code_len && fault==FAULT_NONE){
    if(++steps>STEP_LIMIT){ fault=FAULT_STEP_LIMIT; break; }
    if(pc<0||pc>=code_len){ fault=FAULT_PC_OOB; break; }
    last_op_index=byte_to_token[pc];
    if(last_op_index<0){ fault=FAULT_BAD_ENCODING; break; }
    uint64_t op=0;
    if(!decode_uvarint(code_buf,code_len,&pc,&op)){ fault=FAULT_BAD_ENCODING; break; }
    switch((uint32_t)op){
      case OP_LIT: { uint64_t e=0; if(!decode_uvarint(code_buf,code_len,&pc,&e)){fault=FAULT_BAD_ENCODING;break;} push(decode_zigzag64(e)); break; }
      case OP_ADD: { int64_t b=pop(),a=pop(); push(a+b); break; }
      case OP_SUB: { int64_t b=pop(),a=pop(); push(a-b); break; }
      case OP_MUL: { int64_t b=pop(),a=pop(); push(a*b); break; }
      case OP_DIV: { int64_t b=pop(); if(b==0){fault=FAULT_DIV_BY_ZERO;break;} int64_t a=pop(); push(a/b); break; }
      case OP_MOD: { int64_t b=pop(); if(b==0){fault=FAULT_MOD_BY_ZERO;break;} int64_t a=pop(); push(a%b); break; }
      case OP_GT: { int64_t b=pop(),a=pop(); push(a>b?1:0); break; }
      case OP_LT: { int64_t b=pop(),a=pop(); push(a<b?1:0); break; }
      case OP_EQ: { int64_t b=pop(),a=pop(); push(a==b?1:0); break; }
      case OP_NEQ:{ int64_t b=pop(),a=pop(); push(a!=b?1:0); break; }
      case OP_DUP:{ if(sp<0){fault=FAULT_STACK_UNDERFLOW;break;} push(stack[sp]); break; }
      case OP_DRP:{ (void)pop(); break; }
      case OP_GTWAY:{ uint64_t c=0; if(!decode_uvarint(code_buf,code_len,&pc,&c)){fault=FAULT_BAD_ENCODING;break;} caps_add((uint32_t)c); break; }
      case OP_IOW:{ uint64_t d=0; if(!decode_uvarint(code_buf,code_len,&pc,&d)){fault=FAULT_BAD_ENCODING;break;}
        if(!caps_has((uint32_t)d)){fault=FAULT_UNAUTHORIZED;break;} int64_t v=pop();
        if(d<8) sim_relay[d]=(v!=0)?1:0; break; }
      case OP_IOR:{ uint64_t d=0; if(!decode_uvarint(code_buf,code_len,&pc,&d)){fault=FAULT_BAD_ENCODING;break;}
        if(!caps_has((uint32_t)d)){fault=FAULT_UNAUTHORIZED;break;}
        push((d<8)?sim_relay[d]:0); break; }
      case OP_WAIT:{ uint64_t ms=0; if(!decode_uvarint(code_buf,code_len,&pc,&ms)){fault=FAULT_BAD_ENCODING;break;}
        /* benchmark: skip real delay to isolate interpretation cost */ break; }
      case OP_JMP:{ int32_t rel=0; if(!decode_svarint32(code_buf,code_len,&pc,&rel)){fault=FAULT_BAD_ENCODING;break;}
        int t=last_op_index+1+rel; if(t<0||t>=token_count){fault=FAULT_PC_OOB;break;} pc=token_offsets[t]; break; }
      case OP_JZ:{ int32_t rel=0; if(!decode_svarint32(code_buf,code_len,&pc,&rel)){fault=FAULT_BAD_ENCODING;break;}
        int64_t c=pop(); if(fault!=FAULT_NONE)break;
        if(c==0){ int t=last_op_index+1+rel; if(t<0||t>=token_count){fault=FAULT_PC_OOB;break;} pc=token_offsets[t]; } break; }
      case OP_JNZ:{ int32_t rel=0; if(!decode_svarint32(code_buf,code_len,&pc,&rel)){fault=FAULT_BAD_ENCODING;break;}
        int64_t c=pop(); if(fault!=FAULT_NONE)break;
        if(c!=0){ int t=last_op_index+1+rel; if(t<0||t>=token_count){fault=FAULT_PC_OOB;break;} pc=token_offsets[t]; } break; }
      case OP_HALT: return;
      case OP_B: case OP_E: break;
      default: fault=FAULT_UNKNOWN_OP; break;
    }
  }
}
static uint32_t reps = 0;
static unsigned long t0 = 0;

void setup() {
  Serial.begin(115200);
  memcpy(code_buf, TASK_CODE, TASK_CODE_LEN);
  code_len = TASK_CODE_LEN;
  Serial.print("BANNER bytecode v3_006 bytes=");
  Serial.print(TASK_CODE_LEN);
  Serial.print(" reps=");
  Serial.println(REPORT_EVERY);
  t0 = micros();
}

void loop() {
  run_vm();
  reps++;
  if (reps % REPORT_EVERY == 0) {
    unsigned long elapsed = micros() - t0;
    int64_t top = (sp >= 0 && fault == FAULT_NONE) ? stack[sp] : -1;
    Serial.print("TICK ");
    Serial.print(reps);
    Serial.print(" ");
    Serial.print(elapsed);
    Serial.print(" ");
    Serial.print((long)top);
    Serial.print(" ");
    Serial.println((int)fault);
  }
}
