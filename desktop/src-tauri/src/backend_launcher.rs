use std::process::Command;
use std::thread;
use std::time::{Duration, Instant};

const HEALTH_URL: &str = "http://localhost:8000/health";
const MAX_WAIT_SECONDS: u64 = 60;
const POLL_INTERVAL_MS: u64 = 1000;

/// 获取项目根目录。
/// 优先从环境变量 OJ_PROJECT_ROOT 读，否则用硬编码路径。
fn project_root() -> String {
    std::env::var("OJ_PROJECT_ROOT")
        .unwrap_or_else(|_| String::from("E:\\github_project\\oj-platform"))
}

/// 检查后端是否响应。
fn is_backend_running() -> bool {
    let client = match reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(2))
        .build()
    {
        Ok(c) => c,
        Err(_) => return false,
    };

    match client.get(HEALTH_URL).send() {
        Ok(resp) => resp.status().is_success(),
        Err(_) => false,
    }
}

/// 在项目根目录执行 docker compose up -d。
fn start_backend_stack() -> Result<(), String> {
    let root = project_root();

    println!("[launcher] starting backend at: {}", root);

    let output = Command::new("docker")
        .args(["compose", "up", "-d"])
        .current_dir(&root)
        .output()
        .map_err(|e| format!("Failed to run docker compose: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("docker compose up -d failed:\n{}", stderr));
    }

    println!("[launcher] docker compose up -d done");
    Ok(())
}

/// 轮询等待后端就绪。
fn wait_for_backend() -> bool {
    let start = Instant::now();
    let timeout = Duration::from_secs(MAX_WAIT_SECONDS);

    while start.elapsed() < timeout {
        if is_backend_running() {
            println!("[launcher] backend ready");
            return true;
        }
        thread::sleep(Duration::from_millis(POLL_INTERVAL_MS));
    }

    false
}

/// 主流程：检查 → 拉起 → 等待。
pub fn ensure_backend_ready() -> Result<(), String> {
    if is_backend_running() {
        println!("[launcher] backend already running");
        return Ok(());
    }

    println!("[launcher] backend not running, starting...");
    start_backend_stack()?;

    println!("[launcher] waiting for backend to become ready...");
    if wait_for_backend() {
        Ok(())
    } else {
        Err(format!(
            "Backend did not become ready within {} seconds",
            MAX_WAIT_SECONDS
        ))
    }
}