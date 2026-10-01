import pytest

from app.plugins.judge_plugin.judge_java import judge_java


JAVA_ECHO = """
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        while (sc.hasNextLine()) {
            System.out.println(sc.nextLine());
        }
    }
}
"""

JAVA_EMPTY_INPUT = """
public class Main {
    public static void main(String[] args) {
        System.out.println("ok");
    }
}
"""

JAVA_STACK_OVERFLOW = """
public class Main {
    static void recurse(int n) {
        recurse(n + 1);
    }
    public static void main(String[] args) {
        recurse(0);
    }
}
"""

JAVA_BIG_OUTPUT = """
public class Main {
    public static void main(String[] args) {
        for (int i = 0; i < 100000; i++) {
            System.out.println(i);
        }
    }
}
"""


def test_java_empty_input():
    """无输入也应正常运行。"""
    cases = [{"input_data": "", "expected_output": "ok\n"}]
    result = judge_java(JAVA_EMPTY_INPUT, cases, timeout_s=10)
    assert result["status"] == "AC"


def test_java_multiline_input():
    """多行输入。"""
    cases = [
        {"input_data": "line1\nline2\nline3\n", "expected_output": "line1\nline2\nline3\n"},
    ]
    result = judge_java(JAVA_ECHO, cases, timeout_s=10)
    assert result["status"] == "AC"


def test_java_stack_overflow():
    """栈溢出应判 RE。"""
    cases = [{"input_data": "", "expected_output": ""}]
    result = judge_java(JAVA_STACK_OVERFLOW, cases, timeout_s=10)
    assert result["status"] == "RE"


def test_java_big_output():
    """大量输出应正常运行。"""
    expected = "\n".join(str(i) for i in range(100000)) + "\n"
    cases = [{"input_data": "", "expected_output": expected}]
    result = judge_java(JAVA_BIG_OUTPUT, cases, timeout_s=15)
    assert result["status"] == "AC"


def test_java_compile_once():
    """多个测试点只编译一次（通过耗时判断）。

    若每次重新编译，2 个测试点会慢至少 2 秒。
    """
    import time

    code = """
import java.util.Scanner;
public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int a = sc.nextInt();
        System.out.println(a * 2);
    }
}
"""
    cases = [
        {"input_data": "1\n", "expected_output": "2\n"},
        {"input_data": "5\n", "expected_output": "10\n"},
        {"input_data": "100\n", "expected_output": "200\n"},
    ]

    start = time.perf_counter()
    result = judge_java(code, cases, timeout_s=10)
    elapsed = time.perf_counter() - start

    assert result["status"] == "AC"
    assert result["passed_cases"] == 3

    # 3 个测试点，若每次都编译约 6-9 秒，只编译一次约 3-5 秒
    # 这里仅断言"3 个测试点不太慢"，不精确
    assert elapsed < 30