# backend/tests/test_judge_python.py

import pytest

from app.plugins.judge_plugin.judge_python import judge_python


def test_ac_simple():
    code = "a, b = map(int, input().split())\nprint(a + b)\n"
    cases = [{"input_data": "1 2\n", "expected_output": "3\n"}]
    result = judge_python(code, cases, timeout_s=10)
    assert result["status"] == "AC"
    assert result["passed_cases"] == 1
    assert result["total_cases"] == 1


def test_wa_simple():
    code = "print(999)\n"
    cases = [{"input_data": "", "expected_output": "3\n"}]
    result = judge_python(code, cases, timeout_s=10)
    assert result["status"] == "WA"
    assert result["passed_cases"] == 0


def test_ce_syntax_error():
    code = "print('unclosed\n"
    cases = [{"input_data": "", "expected_output": ""}]
    result = judge_python(code, cases, timeout_s=10)
    assert result["status"] == "CE"


def test_re_runtime_error():
    code = "print(1/0)\n"
    cases = [{"input_data": "", "expected_output": ""}]
    result = judge_python(code, cases, timeout_s=10)
    assert result["status"] == "RE"


def test_tle_infinite_loop():
    code = "while True:\n    pass\n"
    cases = [{"input_data": "", "expected_output": ""}]
    result = judge_python(code, cases, timeout_s=2)
    assert result["status"] == "TLE"


def test_multi_case_partial():
    code = "print(1)\n"
    cases = [
        {"input_data": "", "expected_output": "1\n"},
        {"input_data": "", "expected_output": "2\n"},
    ]
    result = judge_python(code, cases, timeout_s=10)
    assert result["status"] == "WA"
    assert result["passed_cases"] == 1
    assert result["total_cases"] == 2