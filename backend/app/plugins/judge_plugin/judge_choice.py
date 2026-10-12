"""选择题判题器。"""
from typing import Optional


def _result(status: str, passed: int, total: int, message: Optional[str] = None) -> dict:
    return {
        "status": status,
        "passed_cases": passed,
        "total_cases": total,
        "runtime_ms": 0,
        "error_message": message,
    }


def judge_choice(answer_data: Optional[dict], options: Optional[list]) -> dict:
    if not options:
        return _result("RE", 0, 0, "Problem has no options")

    if not isinstance(answer_data, dict):
        return _result("WA", 0, 1, "No answer submitted")

    selected = answer_data.get("selected")

    if selected is None or selected == "" or selected == []:
        return _result("WA", 0, 1, "No option selected")

    correct_keys = [
        str(o.get("key"))
        for o in options
        if isinstance(o, dict) and o.get("is_correct")
    ]

    if not correct_keys:
        return _result("RE", 0, 1, "No correct option configured")

    if isinstance(selected, list):
        selected_keys = sorted(str(s) for s in selected)
        correct_sorted = sorted(correct_keys)
        if selected_keys == correct_sorted:
            return _result("AC", 1, 1)
        return _result("WA", 0, 1, "Incorrect selection")

    if str(selected) in correct_keys:
        return _result("AC", 1, 1)

    return _result("WA", 0, 1, "Incorrect option")