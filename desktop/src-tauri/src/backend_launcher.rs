use include_dir::{include_dir, Dir};
use std::fs;
use std::net::{TcpStream, ToSocketAddrs};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::thread;
use std::time::{Duration, Instant};

const BACKEND_HOST: &str = "127.0.0.1";
const BACKEND_PORT: u16 = 8000;
const MAX_WAIT_SECONDS: u64 = 180;
const POLL_INTERVAL_MS: u64 = 1000;

static EMBEDDED: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/assets");

fn app_data_dir() -> PathBuf {
    dirs::data_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("oj-platform")
}

/// TCP 探测：端口可连即视为就绪，不依赖 HTTP、DNS、代理
fn is_backend_running() -> bool {
    let addr_str = format!("{}:{}", BACKEND_HOST, BACKEND_PORT);
    let addr = match addr_str.to_socket_addrs() {
        Ok(mut it) => match it.next() {
            Some(a) => a,
            None => return false,
        },
        Err(_) => return false,
    };

    TcpStream::connect_timeout(&addr, Duration::from_secs(1)).is_ok()
}

fn extract_dir(dir: &Dir, target: &Path) -> Result<(), String> {
    for entry in dir.entries() {
        let entry_path = target.join(entry.path());
        match entry {
            include_dir::DirEntry::Dir(d) => {
                fs::create_dir_all(&entry_path)
                    .map_err(|e| format!("create dir {:?}: {}", entry_path, e))?;
                extract_dir(d, target)?;
            }
            include_dir::DirEntry::File(f) => {
                if let Some(parent) = entry_path.parent() {
                    fs::create_dir_all(parent)
                        .map_err(|e| format!("create parent {:?}: {}", parent, e))?;
                }
                fs::write(&entry_path, f.contents())
                    .map_err(|e| format!("write {:?}: {}", entry_path, e))?;
            }
        }
    }
    Ok(())
}

fn extract_assets_if_needed() -> Result<PathBuf, String> {
    let target = app_data_dir();
    fs::create_dir_all(&target)
        .map_err(|e| format!("create app data dir {:?}: {}", target, e))?;

    let marker = target.join("docker-compose.yml");
    if marker.exists() {
        println!("[launcher] assets already extracted");
        return Ok(target);
    }

    println!("[launcher] extracting assets to {:?}", target);
    extract_dir(&EMBEDDED, &target)?;

    let env_example = target.join(".env.example");
    let env_target = target.join(".env");
    if env_example.exists() && !env_target.exists() {
        let _ = fs::copy(&env_example, &env_target);
        println!("[launcher] created .env from .env.example");
    }

    println!("[launcher] assets extracted");
    Ok(target)
}

fn start_backend_stack(root: &Path) -> Result<(), String> {
    println!("[launcher] running docker compose up -d in {:?}", root);

    let output = Command::new("docker")
        .args(["compose", "up", "-d"])
        .current_dir(root)
        .output()
        .map_err(|e| format!("Failed to spawn docker: {}", e))?;

    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();

    if !output.status.success() {
        return Err(format!(
            "docker compose up -d 退出码 {}:\nSTDOUT:\n{}\nSTDERR:\n{}",
            output.status.code().unwrap_or(-1),
            stdout,
            stderr
        ));
    }

    println!("[launcher] docker compose stdout:\n{}", stdout);
    Ok(())
}

fn wait_for_backend() -> Result<(), String> {
    let start = Instant::now();
    let timeout = Duration::from_secs(MAX_WAIT_SECONDS);
    let mut last_log = Instant::now();

    while start.elapsed() < timeout {
        if is_backend_running() {
            println!("[launcher] backend ready");
            return Ok(());
        }

        if last_log.elapsed() >= Duration::from_secs(15) {
            println!(
                "[launcher] waiting for {}:{}  ({:.0}s)",
                BACKEND_HOST,
                BACKEND_PORT,
                start.elapsed().as_secs_f64()
            );
            last_log = Instant::now();
        }

        thread::sleep(Duration::from_millis(POLL_INTERVAL_MS));
    }

    Err(format!(
        "端口 {}:{} 在 {} 秒内未就绪",
        BACKEND_HOST, BACKEND_PORT, MAX_WAIT_SECONDS
    ))
}

pub fn ensure_backend_ready() -> Result<(), String> {
    println!("[launcher] initial check...");
    if is_backend_running() {
        println!("[launcher] backend already running");
        return Ok(());
    }

    let root = extract_assets_if_needed()
        .map_err(|e| format!("步骤 1（解压资源）失败：{}", e))?;

    start_backend_stack(&root)
        .map_err(|e| format!("步骤 2（docker compose）失败：{}", e))?;

    wait_for_backend()
        .map_err(|e| format!("步骤 3（等待就绪）失败：{}", e))?;

    println!("[launcher] backend is ready");
    Ok(())
}