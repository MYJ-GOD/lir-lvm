#!/usr/bin/env python3
import unittest

from mir_compiler import MirCompilerError, compile_source, compile_to_plan
from backend_adapter import simulate_subset


class MirCompilerTests(unittest.TestCase):
    def test_compile_relay_on(self):
        source = """
task relay1_on {
  require cap(relay1)
  set relay1 = 1
  halt
}
"""
        _, payload = compile_source(source)
        self.assertEqual(payload.hex(), "50051e02460552")

    def test_compile_relay_on_wait_read(self):
        source = """
task relay_on_wait_read {
  require cap(relay1)
  require cap(water_sensor)
  set relay1 = 1
  wait 500ms
  read water_sensor
  halt
}
"""
        _, payload = compile_source(source)
        self.assertEqual(payload.hex(), "500550011e02460551f403470152")

    def test_missing_capability_fails(self):
        source = """
task invalid_missing_cap {
  set relay1 = 1
  halt
}
"""
        with self.assertRaises(MirCompilerError) as ctx:
            compile_source(source)
        self.assertEqual(ctx.exception.code, "INVALID_CAPABILITY")

    def test_unknown_device_fails(self):
        source = """
task invalid_unknown_device {
  require cap(pump1)
  set pump1 = 1
  halt
}
"""
        with self.assertRaises(MirCompilerError) as ctx:
            compile_source(source)
        self.assertEqual(ctx.exception.code, "UNKNOWN_DEVICE")

    def test_readback_is_lowered(self):
        source = """
task relay1_set_and_check {
  require cap(relay1)
  set relay1 = 1
  readback relay1 expect 1
  halt
}
"""
        _, payload = compile_source(source)
        self.assertTrue(len(payload) > 0)

    def test_compile_to_plan_preserves_readback_and_retry(self):
        source = """
task relay1_retry_check {
  require cap(relay1)
  retry 3 times {
    set relay1 = 1
    readback relay1 expect 1
  }
  halt
}
"""
        plan = compile_to_plan(source)
        self.assertEqual(plan["task_name"], "relay1_retry_check")
        self.assertEqual(plan["requirements"][0]["device"], "relay1")
        self.assertEqual(plan["steps"][0]["kind"], "retry")
        self.assertEqual(plan["steps"][0]["times"], 3)
        self.assertEqual(plan["steps"][0]["body"][0]["kind"], "set")
        self.assertEqual(plan["steps"][0]["body"][1]["kind"], "readback")
        self.assertEqual(plan["steps"][0]["body"][1]["expect"], 1)
        self.assertEqual(plan["steps"][1]["kind"], "halt")

    def test_readback_lowers_to_executable_bytecode(self):
        source = """
task relay1_set_and_check {
  require cap(relay1)
  set relay1 = 1
  readback relay1 expect 1
  halt
}
"""
        _, payload = compile_source(source)
        result = simulate_subset(payload)
        self.assertTrue(result.verify_pass)
        self.assertTrue(result.execution_pass)
        self.assertEqual(result.result_top, 1)
        self.assertEqual(result.relay_state[5], 1)

    def test_retry_success_path(self):
        source = """
task relay1_retry_success {
  require cap(relay1)
  retry 3 times {
    set relay1 = 1
    readback relay1 expect 1
  }
  halt
}
"""
        _, payload = compile_source(source)
        result = simulate_subset(payload)
        self.assertTrue(result.verify_pass)
        self.assertTrue(result.execution_pass)
        self.assertEqual(result.result_top, 1)
        self.assertEqual(result.relay_state[5], 1)

    def test_retry_exhausted_path(self):
        source = """
task relay1_retry_fail {
  require cap(relay1)
  retry 2 times {
    set relay1 = 1
    readback relay1 expect 0
  }
  halt
}
"""
        _, payload = compile_source(source)
        result = simulate_subset(payload)
        self.assertTrue(result.verify_pass)
        self.assertTrue(result.execution_pass)
        self.assertEqual(result.result_top, 0)
        self.assertEqual(result.relay_state[5], 1)


if __name__ == "__main__":
    unittest.main()
