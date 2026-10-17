import os
import shutil
import subprocess
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Tuple


def _is_in_docker() -> bool:
    return os.environ.get("IN_DOCKER") == "1"


def _to_docker_path(p: Path) -> str:
    s = p.resolve().as_posix()
    if len(s) >= 2 and s[1] == ":":
        s = f"/{s[0].lower()}{s[2:]}"
    return s


@contextmanager
def sandbox_workspace():
    """生成一个用于判题的临时目录，并自动清理。"""
    if _is_in_docker():
        sandbox_uuid = uuid.uuid4().hex
        ws = Path("/sandbox") / sandbox_uuid
        ws.mkdir(parents=True, exist_ok=True)
        try:
            yield ws
        finally:
            shutil.rmtree(ws, ignore_errors=True)
    else:
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)


def _get_docker_mount(workspace: Path) -> Tuple[str, str]:
    """返回 (docker -v 挂载参数, 容器内工作路径)"""
    if _is_in_docker():
        volume_name = os.environ.get("SANDBOX_VOLUME_NAME", "oj-platform_sandbox_data")
        mount_arg = f"{volume_name}:/workspace"
        inner_path = f"/workspace/{workspace.name}"
        return mount_arg, inner_path
    else:
        docker_path = _to_docker_path(workspace)
        mount_arg = f"{docker_path}:/workspace"
        inner_path = "/workspace"
        return mount_arg, inner_path


# ===== Python =====

class SandboxResult:
    def __init__(self, status: str, stdout: str, stderr: str, exit_code: int, runtime_ms: int = 0):
        self.status = status
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.runtime_ms = runtime_ms


def run_python_in_sandbox(code: str, input_data: str = "", timeout_s: int = 5) -> SandboxResult:
    with sandbox_workspace() as workspace:
        (workspace / "main.py").write_text(code)
        mount_arg, inner_path = _get_docker_mount(workspace)

        cmd = [
            "docker", "run", "--rm", "-i",
            "--read-only",
            "--network", "none",
            "--memory=256m", "--cpus=1", "--pids-limit=64",
            "--security-opt", "no-new-privileges",
            "-v", mount_arg,
            "judge-python:latest",
            "python", f"{inner_path}/main.py",
        ]

        try:
            start_t = time.perf_counter()
            proc = subprocess.run(
                cmd,
                input=input_data,
                text=True,
                capture_output=True,
                timeout=timeout_s,
            )
            runtime_ms = int((time.perf_counter() - start_t) * 1000)
            
            status = "OK" if proc.returncode == 0 else "RE"
            return SandboxResult(status, proc.stdout, proc.stderr, proc.returncode, runtime_ms)
        except subprocess.TimeoutExpired:
            return SandboxResult("TLE", "", "", -1, timeout_s * 1000)


def check_python_syntax(code: str) -> Optional[str]:
    """用 ast.parse 检查语法（在 Python 环境内直接执行，不启 Docker）"""
    import ast
    try:
        ast.parse(code)
        return None
    except SyntaxError as e:
        return str(e)


# ===== Java =====

class JavaRunResult:
    def __init__(self, status: str, stdout: str, stderr: str, exit_code: int, runtime_ms: int = 0):
        self.status = status
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.runtime_ms = runtime_ms


def compile_java(workspace_dir: Path, timeout_s: int = 20) -> Tuple[int, str]:
    mount_arg, inner_path = _get_docker_mount(workspace_dir)

    cmd = [
        "docker", "run", "--rm",
        "--read-only",
        "-v", mount_arg,
        "judge-java:latest",
        "javac", f"{inner_path}/Main.java",
    ]
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout_s)
        return proc.returncode, proc.stderr
    except subprocess.TimeoutExpired:
        return -1, "Compile Timeout"


def run_java_compiled(workspace_dir: Path, input_data: str = "", timeout_s: int = 5) -> JavaRunResult:
    mount_arg, inner_path = _get_docker_mount(workspace_dir)

    java_opts = [
        "-Xmx200m", "-Xms200m", "-Xss8m",
        "-XX:+UseSerialGC", "-XX:MaxMetaspaceSize=64m",
    ]

    cmd = [
        "docker", "run", "--rm", "-i",
        "--read-only",
        "--network", "none",
        "--memory=256m", "--cpus=1", "--pids-limit=64",
        "--security-opt", "no-new-privileges",
        "-v", mount_arg,
        "judge-java:latest",
        "java", *java_opts, "-cp", inner_path, "Main",
    ]

    try:
        start_t = time.perf_counter()
        proc = subprocess.run(
            cmd, input=input_data, text=True, capture_output=True, timeout=timeout_s
        )
        runtime_ms = int((time.perf_counter() - start_t) * 1000)
        
        return JavaRunResult(
            "OK" if proc.returncode == 0 else "RE", 
            proc.stdout, 
            proc.stderr, 
            proc.returncode,
            runtime_ms
        )
    except subprocess.TimeoutExpired:
        return JavaRunResult("TLE", "", "", -1, timeout_s * 1000)


# ===== C++ =====

class CppSandboxResult:
    def __init__(self, status: str, stdout: str, stderr: str, exit_code: int, runtime_ms: int = 0):
        self.status = status
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.runtime_ms = runtime_ms


def run_cpp_in_sandbox(code: str, input_data: str = "", timeout_s: int = 5) -> CppSandboxResult:
    with sandbox_workspace() as workspace:
        (workspace / "main.cpp").write_text(code)
        mount_arg, inner_path = _get_docker_mount(workspace)

        cmd = [
            "docker", "run", "--rm", "-i",
            "--read-only",
            "--network", "none",
            "--memory=256m", "--cpus=1", "--pids-limit=64",
            "--security-opt", "no-new-privileges",
            "-v", mount_arg,
            "judge-cpp:latest",
            "sh", "-c", f"g++ -O2 -std=c++17 -o {inner_path}/main {inner_path}/main.cpp && {inner_path}/main",
        ]

        try:
            start_t = time.perf_counter()
            proc = subprocess.run(
                cmd,
                input=input_data,
                text=True,
                capture_output=True,
                timeout=timeout_s,
            )
            runtime_ms = int((time.perf_counter() - start_t) * 1000)
            
            status = "OK" if proc.returncode == 0 else "RE"
            return CppSandboxResult(status, proc.stdout, proc.stderr, proc.returncode, runtime_ms)
        except subprocess.TimeoutExpired:
            return CppSandboxResult("TLE", "", "", -1, timeout_s * 1000)