# backend/app/plugins/judge_plugin/judge_java.py

import shutil
import tempfile
from pathlib import Path
from typing import List, Optional

from app.plugins.judge_plugin.sandbox import (
    run_java_compiled,
    compile_java,
)


def _normalize_output(s: str) -> str:
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
    """判 Java 代码。编译一次，逐个测试点运行。"""
    total = len(test_cases)
    if total == 0:
        return {
            "status": "AC",
            "passed_cases": 0,
            "total_cases": 0,
            "runtime_ms": 0,
            "error_message": None,
        }

    tmpdir = Path(tempfile.mkdtemp(prefix="oj_java_"))
    try:
        code_file = tmpdir / "Main.java"
        code_file.write_text(code, encoding="utf-8")

        # 1. 编译一次
        rc, stderr = compile_java(tmpdir)

        if rc == -1:
            return {
                "status": "TLE",
                "passed_cases": 0,
                "total_cases": total,
                "runtime_ms": 20000,
                "error_message": "Compile timeout",
            }

        if rc != 0:
            return {
                "status": "CE",
                "passed_cases": 0,
                "total_cases": total,
                "runtime_ms": 0,
                "error_message": stderr[:2000],
            }

        # 2. 逐个测试点运行（class 文件已就绪）
        passed = 0
        max_runtime = 0
        first_error: Optional[str] = None
        final_status = "AC"

        for idx, tc in enumerate(test_cases, start=1):
            input_data = tc.get("input_data") or ""
            expected = tc.get("expected_output") or ""

            result = run_java_compiled(tmpdir, input_data, timeout_s=timeout_s)
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

        if passed < total and final_status == "AC":
            final_status = "WA"

        return {
            "status": final_status,
            "passed_cases": passed,
            "total_cases": total,
            "runtime_ms": max_runtime,
            "error_message": first_error,
        }

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)