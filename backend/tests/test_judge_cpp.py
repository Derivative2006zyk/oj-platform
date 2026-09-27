import pytest

from app.plugins.judge_plugin.judge_cpp import judge_cpp


CPP_AC = """
#include <iostream>
using namespace std;

int main() {
    int a, b;
    cin >> a >> b;
    cout << a + b << endl;
    return 0;
}
"""

CPP_WA = """
#include <iostream>
int main() {
    std::cout << 999 << std::endl;
    return 0;
}
"""

CPP_CE = """
#include <iostream>
int main() {
    std::cout << "no semicolon"
    return 0;
}
"""

CPP_RE_SEGV = """
#include <iostream>
int main() {
    int *p = nullptr;
    *p = 42;
    return 0;
}
"""

CPP_TLE = """
int main() {
    while (1) {}
    return 0;
}
"""


def test_cpp_ac():
    cases = [{"input_data": "1 2\n", "expected_output": "3\n"}]
    result = judge_cpp(CPP_AC, cases, timeout_s=10)
    assert result["status"] == "AC"
    assert result["passed_cases"] == 1


def test_cpp_wa():
    cases = [{"input_data": "", "expected_output": "3\n"}]
    result = judge_cpp(CPP_WA, cases, timeout_s=10)
    assert result["status"] == "WA"


def test_cpp_ce():
    cases = [{"input_data": "", "expected_output": ""}]
    result = judge_cpp(CPP_CE, cases, timeout_s=10)
    assert result["status"] == "CE"


def test_cpp_re_segv():
    cases = [{"input_data": "", "expected_output": ""}]
    result = judge_cpp(CPP_RE_SEGV, cases, timeout_s=10)
    assert result["status"] == "RE"


def test_cpp_tle():
    cases = [{"input_data": "", "expected_output": ""}]
    result = judge_cpp(CPP_TLE, cases, timeout_s=3)
    assert result["status"] == "TLE"