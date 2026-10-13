"""填空题判题器。

answer_data 结构：
    {"blanks": ["3", "4"]}

problem.blanks 结构（来自 problems.blanks）：
    [
        {"blank_index": 1, "correct_answers": ["3", "三"], "match_rule": "exact"},
        {"blank_index": 2, "correct_answers": ["4"], "match_rule": "exact"},
    ]

match_rule 支持：
    exact       - 完全匹配
    ignore_case - 忽略大小写

返回与 judge_choice 一致的 verdict dict。
"""
from typing import Any, List, Optional


def _result(
    status: str,
    passed: int,
    total: int,
    message: Optional[str] = None,
) -> dict:
    return {
        "status": status,
        "passed_cases": passed,
        "total_cases": total,
        "runtime_ms": 0,
        "error_message": message,
    }


def _normalize(value: Any, rule: str) -> str:
    s = "" if value is None else str(value).strip()
    if rule == "ignore_case":
        return s.lower()
    return s


def _match_one(user_answer: Any, correct_answers: List[str], rule: str) -> bool:
    if user_answer is None:
        return False
    ua = _normalize(user_answer, rule)
    if ua == "":
        return False
    for correct in correct_answers or []:
        if _normalize(correct, rule) == ua:
            return True
    return False


def judge_fill_blank(
    answer_data: Optional[dict],
    blanks: Optional[list],
) -> dict:
    if not blanks:
        return _result("RE", 0, 0, "Problem has no blanks")

    if not isinstance(answer_data, dict):
        return _result("WA", 0, len(blanks), "No answer submitted")

    answers = answer_data.get("blanks")
    if not isinstance(answers, list):
        return _result("WA", 0, len(blanks), "No blanks array submitted")

    total = len(blanks)
    passed = 0

    for idx, blank in enumerate(blanks):
        if not isinstance(blank, dict):
            continue
        rule = blank.get("match_rule") or "exact"
        correct_answers = blank.get("correct_answers") or []
        user_answer = answers[idx] if idx < len(answers) else None
        if _match_one(user_answer, correct_answers, rule):
            passed += 1

    if passed == total:
        return _result("AC", passed, total)

    return _result("WA", passed, total, f"{passed}/{total} blanks correct")