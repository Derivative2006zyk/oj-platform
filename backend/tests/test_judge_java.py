import pytest

from app.plugins.judge_plugin.judge_java import judge_java


JAVA_AC = """
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int a = sc.nextInt();
        int b = sc.nextInt();
        System.out.println(a + b);
    }
}
"""

JAVA_WA = """
public class Main {
    public static void main(String[] args) {
        System.out.println(999);
    }
}
"""

JAVA_CE = """
public class Main {
    public static void main(String[] args) {
        System.out.println("no semicolon")
    }
}
"""

JAVA_RE = """
public class Main {
    public static void main(String[] args) {
        int x = 1 / 0;
    }
}
"""

JAVA_TLE = """
public class Main {
    public static void main(String[] args) {
        while (true) {}
    }
}
"""


def test_java_ac():
    cases = [{"input_data": "1 2\n", "expected_output": "3\n"}]
    result = judge_java(JAVA_AC, cases, timeout_s=10)
    assert result["status"] == "AC"
    assert result["passed_cases"] == 1
    assert result["total_cases"] == 1


def test_java_wa():
    cases = [{"input_data": "", "expected_output": "3\n"}]
    result = judge_java(JAVA_WA, cases, timeout_s=10)
    assert result["status"] == "WA"


def test_java_ce():
    cases = [{"input_data": "", "expected_output": ""}]
    result = judge_java(JAVA_CE, cases, timeout_s=10)
    assert result["status"] == "CE"


def test_java_re():
    cases = [{"input_data": "", "expected_output": ""}]
    result = judge_java(JAVA_RE, cases, timeout_s=10)
    assert result["status"] == "RE"


def test_java_tle():
    cases = [{"input_data": "", "expected_output": ""}]
    result = judge_java(JAVA_TLE, cases, timeout_s=3)
    assert result["status"] == "TLE"