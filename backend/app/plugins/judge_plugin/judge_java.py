from typing import List, Optional

from app.plugins.judge_plugin.sandbox import run_java_in_sandbox


def _normalize_output(s: str) -> str:
    """去除每行末尾空白、去除末尾空行。"""
    lines = s.replace("\r\n", "\n").split("\n")
    lines = [line.rstrip() for line in lines]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def judge_java(
    code: str,
    test_cases: List[dict],
    timeout_s: int = 5,
) -> dict:
    """判 Java 代码。

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

    # 用第一个测试点跑一次，检测 CE
    # （编译失败与测试点无关，只跑一次即可）
    first_input = test_cases[0].get("input_data") or ""
    first_result = run_java_in_sandbox(code, first_input, timeout_s=timeout_s)

    if first_result.status == "CE":
        return {
            "status": "CE",
            "passed_cases": 0,
            "total_cases": total,
            "runtime_ms": 0,
            "error_message": (first_result.compile_error or "")[:2000],
        }

    # 第一个测试点的判定
    passed = 0
    max_runtime = first_result.runtime_ms
    first_error: Optional[str] = None
    final_status = "AC"

    def check_one(idx: int, result) -> bool:
        """检查单个测试点，返回是否 AC。同时设置 final_status / first_error。"""
        nonlocal max_runtime, first_error, final_status

        max_runtime = max(max_runtime, result.runtime_ms)

        if result.status == "TLE":
            final_status = "TLE"
            first_error = f"Test case #{idx}: Time Limit Exceeded"
            return False
        if result.status == "MLE":
            final_status = "MLE"
            first_error = f"Test case #{idx}: Memory Limit Exceeded"
            return False
        if result.status == "RE":
            final_status = "RE"
            first_error = (
                f"Test case #{idx}: Runtime Error\n"
                f"exit_code={result.exit_code}\n"
                f"stderr:\n{result.stderr[:1000]}"
            )
            return False
        # OK → 比对
        actual = _normalize_output(result.stdout)
        exp = _normalize_output(test_cases[idx - 1].get("expected_output") or "")
        if actual == exp:
            return True
        final_status = "WA"
        first_error = (
            f"Test case #{idx}: Wrong Answer\n"
            f"expected:\n{exp[:500]}\n"
            f"actual:\n{actual[:500]}"
        )
        return False

    # 第一个测试点（复用第一次运行结果，避免重复执行）
    if check_one(1, first_result):
        passed += 1
    elif final_status in ("TLE", "MLE", "RE"):
        # 严重错误，直接返回
        return {
            "status": final_status,
            "passed_cases": passed,
            "total_cases": total,
            "runtime_ms": max_runtime,
            "error_message": first_error,
        }

    # 后续测试点
    for idx in range(2, total + 1):
        tc = test_cases[idx - 1]
        result = run_java_in_sandbox(
            code, tc.get("input_data") or "", timeout_s=timeout_s
        )

        if check_one(idx, result):
            passed += 1
        elif final_status in ("TLE", "MLE", "RE"):
            break

    if passed < total and final_status == "AC":
        final_status = "WA"

    return {
        "status": final_status,
        "passed_cases": passed,
        "total_cases": total,
        "runtime_ms": max_runtime,
        "error_message": first_error,
    }