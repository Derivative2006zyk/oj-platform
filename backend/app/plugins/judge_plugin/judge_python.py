from typing import List, Optional

from app.plugins.judge_plugin.sandbox import (
    run_python_in_sandbox,
    check_python_syntax,
)


def _normalize_output(s: str) -> str:
    """去除每行末尾空白、去除末尾空行。"""
    lines = s.replace("\r\n", "\n").split("\n")
    lines = [line.rstrip() for line in lines]
    # 去掉末尾空行
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def judge_python(
    code: str,
    test_cases: List[dict],
    timeout_s: int = 5,
) -> dict:
    """判 Python 代码。

    test_cases: [{"input_data": str, "expected_output": str, "is_example": bool}]
    返回: {
        "status": "AC"|"WA"|"TLE"|"MLE"|"RE"|"CE",
        "passed_cases": int,
        "total_cases": int,
        "runtime_ms": int,
        "error_message": Optional[str]
    }
    """
    total = len(test_cases)
    if total == 0:
        return {
            "status": "AC",
            "passed_cases": 0,
            "total_cases": 0,
            "runtime_ms": 0,
            "error_message": None,
        }

    # 1. 语法检查
    syntax_err = check_python_syntax(code)
    if syntax_err is not None:
        return {
            "status": "CE",
            "passed_cases": 0,
            "total_cases": total,
            "runtime_ms": 0,
            "error_message": syntax_err[:2000],
        }

    # 2. 逐个测试点
    passed = 0
    max_runtime = 0
    first_error: Optional[str] = None
    final_status = "AC"

    for idx, tc in enumerate(test_cases, start=1):
        input_data = tc.get("input_data") or ""
        expected = tc.get("expected_output") or ""

        result = run_python_in_sandbox(code, input_data, timeout_s=timeout_s)
        max_runtime = max(max_runtime, result.runtime_ms)

        if result.status == "TLE":
            final_status = "TLE"
            first_error = f"Test case #{idx}: Time Limit Exceeded"
            break

        if result.status == "MLE":
            final_status = "MLE"
            first_error = f"Test case #{idx}: Memory Limit Exceeded"
            break

        if result.status == "RE":
            final_status = "RE"
            first_error = (
                f"Test case #{idx}: Runtime Error\n"
                f"exit_code={result.exit_code}\n"
                f"stderr:\n{result.stderr[:1000]}"
            )
            break

        # status == OK，比对输出
        actual = _normalize_output(result.stdout)
        exp = _normalize_output(expected)

        if actual == exp:
            passed += 1
        else:
            final_status = "WA"
            first_error = (
                f"Test case #{idx}: Wrong Answer\n"
                f"expected:\n{exp[:500]}\n"
                f"actual:\n{actual[:500]}"
            )
            # 不 break，继续跑其他点，累计 passed
            # 但若后续点又出 TLE/RE，优先标记
            continue

    # 若全程没有错误但 passed < total，是 WA
    if passed < total and final_status == "AC":
        final_status = "WA"

    return {
        "status": final_status,
        "passed_cases": passed,
        "total_cases": total,
        "runtime_ms": max_runtime,
        "error_message": first_error,
    }