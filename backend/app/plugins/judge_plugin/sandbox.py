import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


SANDBOX_IMAGE_PYTHON = "judge-python:latest"
DEFAULT_TIMEOUT_S = 5
DEFAULT_MEMORY = "256m"
DEFAULT_CPUS = "1"
DEFAULT_PIDS = "64"


@dataclass
class SandboxResult:
    status: str  # "OK" | "TLE" | "MLE" | "RE"
    stdout: str
    stderr: str
    exit_code: Optional[int]
    runtime_ms: int


def _to_docker_path(p: Path) -> str:
    """把 Windows 路径转成 Docker Desktop 可识别的 POSIX 路径。

    E:\\github_project\\...\\main.py -> /e/github_project/.../main.py
    /home/user/.../main.py -> /home/user/.../main.py（Linux 不变）
    """
    s = p.resolve().as_posix()
    if len(s) >= 2 and s[1] == ":":
        s = f"/{s[0].lower()}{s[2:]}"
    return s


def run_python_in_sandbox(
    code: str,
    input_data: str = "",
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> SandboxResult:
    """在 Docker 沙箱中运行 Python 代码。

    返回 SandboxResult（status 与判定相关）。
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="oj_sandbox_"))
    try:
        code_file = tmpdir / "main.py"
        code_file.write_text(code, encoding="utf-8")

        docker_code_path = _to_docker_path(code_file)

        cmd = [
            "docker", "run", "--rm",
            "-i",
            "--read-only",
            "--network", "none",
            "--memory", DEFAULT_MEMORY,
            "--cpus", DEFAULT_CPUS,
            "--pids-limit", DEFAULT_PIDS,
            "--security-opt", "no-new-privileges",
            "-v", f"{docker_code_path}:/workspace/main.py:ro",
            SANDBOX_IMAGE_PYTHON,
            "python", "/workspace/main.py",
        ]

        start = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                input=input_data.encode("utf-8"),
                capture_output=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired as e:
            runtime_ms = int((time.perf_counter() - start) * 1000)
            stdout = (e.stdout or b"").decode("utf-8", errors="replace")
            stderr = (e.stderr or b"").decode("utf-8", errors="replace")
            return SandboxResult(
                status="TLE",
                stdout=stdout,
                stderr=stderr,
                exit_code=None,
                runtime_ms=runtime_ms,
            )

        runtime_ms = int((time.perf_counter() - start) * 1000)
        stdout = proc.stdout.decode("utf-8", errors="replace")
        stderr = proc.stderr.decode("utf-8", errors="replace")

        # 内存超限时，docker 会 kill 容器，stderr 含 "Killed" 或 exit code 137
        if proc.returncode == 137:
            return SandboxResult(
                status="MLE",
                stdout=stdout,
                stderr=stderr,
                exit_code=proc.returncode,
                runtime_ms=runtime_ms,
            )

        if proc.returncode != 0:
            return SandboxResult(
                status="RE",
                stdout=stdout,
                stderr=stderr,
                exit_code=proc.returncode,
                runtime_ms=runtime_ms,
            )

        return SandboxResult(
            status="OK",
            stdout=stdout,
            stderr=stderr,
            exit_code=0,
            runtime_ms=runtime_ms,
        )

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def check_python_syntax(code: str) -> Optional[str]:
    """检查 Python 语法。返回错误信息或 None（无错误）。

    用 docker 沙箱跑 ast.parse，不写任何文件，避免 --read-only 报错。
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="oj_sandbox_"))
    try:
        code_file = tmpdir / "main.py"
        code_file.write_text(code, encoding="utf-8")

        docker_code_path = _to_docker_path(code_file)

        cmd = [
            "docker", "run", "--rm",
            "--read-only",
            "--network", "none",
            "--memory", DEFAULT_MEMORY,
            "-v", f"{docker_code_path}:/workspace/main.py:ro",
            SANDBOX_IMAGE_PYTHON,
            "python", "-c",
            "import ast, sys; ast.parse(open('/workspace/main.py', encoding='utf-8').read())",
        ]

        try:
            proc = subprocess.run(cmd, capture_output=True, timeout=10)
        except subprocess.TimeoutExpired:
            return "Syntax check timed out"

        if proc.returncode != 0:
            return proc.stderr.decode("utf-8", errors="replace")
        return None

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

# ============ Java ============

SANDBOX_IMAGE_JAVA = "judge-java:latest"


@dataclass
class JavaSandboxResult:
    status: str  # "OK" | "CE" | "TLE" | "MLE" | "RE"
    stdout: str
    stderr: str
    exit_code: Optional[int]
    runtime_ms: int
    compile_error: Optional[str] = None


def _run_java_compile(
    code_file: Path,
    workspace_dir: Path,
    timeout_s: int = 15,
) -> tuple[int, str, str]:
    """只编译。返回 (exit_code, stdout, stderr)。"""
    workspace_docker_path = _to_docker_path(workspace_dir)

    cmd = [
        "docker", "run", "--rm",
        "--read-only",
        "--network", "none",
        "--memory", DEFAULT_MEMORY,
        "--cpus", DEFAULT_CPUS,
        "--pids-limit", DEFAULT_PIDS,
        "--security-opt", "no-new-privileges",
        "-v", f"{workspace_docker_path}:/workspace:rw",
        "-w", "/workspace",
        SANDBOX_IMAGE_JAVA,
        "javac", "Main.java",
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as e:
        return (
            -1,
            (e.stdout or b"").decode("utf-8", errors="replace"),
            (e.stderr or b"").decode("utf-8", errors="replace"),
        )

    return (
        proc.returncode,
        proc.stdout.decode("utf-8", errors="replace"),
        proc.stderr.decode("utf-8", errors="replace"),
    )


def run_java_in_sandbox(
    code: str,
    input_data: str = "",
    timeout_s: int = DEFAULT_TIMEOUT_S,
) -> JavaSandboxResult:
    """在 Docker 沙箱中编译并运行 Java 代码。

    流程：
    1. javac Main.java → 失败即 CE
    2. java -cp /workspace Main → 运行
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="oj_java_"))
    try:
        code_file = tmpdir / "Main.java"
        code_file.write_text(code, encoding="utf-8")

        # 1. 编译
        rc, _, stderr = _run_java_compile(code_file, tmpdir, timeout_s=20)

        if rc == -1:
            return JavaSandboxResult(
                status="TLE",
                stdout="",
                stderr=stderr,
                exit_code=None,
                runtime_ms=20000,
                compile_error="Compile timeout",
            )

        if rc != 0:
            return JavaSandboxResult(
                status="CE",
                stdout="",
                stderr=stderr,
                exit_code=rc,
                runtime_ms=0,
                compile_error=stderr[:2000],
            )

        # 2. 运行（.class 已写在 tmpdir）
        workspace_docker_path = _to_docker_path(tmpdir)

        run_cmd = [
            "docker", "run", "--rm",
            "-i",
            "--read-only",
            "--network", "none",
            "--memory", DEFAULT_MEMORY,
            "--cpus", DEFAULT_CPUS,
            "--pids-limit", DEFAULT_PIDS,
            "--security-opt", "no-new-privileges",
            "-v", f"{workspace_docker_path}:/workspace:ro",
            "-w", "/workspace",
            SANDBOX_IMAGE_JAVA,
            "java", "-cp", "/workspace", "Main",
        ]

        start = time.perf_counter()
        try:
            proc = subprocess.run(
                run_cmd,
                input=input_data.encode("utf-8"),
                capture_output=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired as e:
            runtime_ms = int((time.perf_counter() - start) * 1000)
            return JavaSandboxResult(
                status="TLE",
                stdout=(e.stdout or b"").decode("utf-8", errors="replace"),
                stderr=(e.stderr or b"").decode("utf-8", errors="replace"),
                exit_code=None,
                runtime_ms=runtime_ms,
            )

        runtime_ms = int((time.perf_counter() - start) * 1000)
        stdout = proc.stdout.decode("utf-8", errors="replace")
        stderr_out = proc.stderr.decode("utf-8", errors="replace")

        if proc.returncode == 137:
            return JavaSandboxResult(
                status="MLE",
                stdout=stdout,
                stderr=stderr_out,
                exit_code=proc.returncode,
                runtime_ms=runtime_ms,
            )

        if proc.returncode != 0:
            return JavaSandboxResult(
                status="RE",
                stdout=stdout,
                stderr=stderr_out,
                exit_code=proc.returncode,
                runtime_ms=runtime_ms,
            )

        return JavaSandboxResult(
            status="OK",
            stdout=stdout,
            stderr=stderr_out,
            exit_code=0,
            runtime_ms=runtime_ms,
        )

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)