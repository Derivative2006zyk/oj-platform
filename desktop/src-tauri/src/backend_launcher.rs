use include_dir::{include_dir, Dir};
use std::fs;
use std::net::{TcpStream, ToSocketAddrs};
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::thread;
use std::time::{Duration, Instant};

const BACKEND_HOST: &str = "127.0.0.1";
const BACKEND_PORT: u16 = 8000;
const MAX_WAIT_SECONDS: u64 = 180;
const POLL_INTERVAL_MS: u64 = 1000;

static EMBEDDED: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/assets");

// ===== 数据目录 =====
fn app_data_dir() -> PathBuf {
    dirs::data_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("oj-platform")
}

// ===== 后端就绪检测（TCP） =====
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

// ===== 资源解压 =====
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

    let compose_target = target.join("docker-compose.yml");
    let env_example_target = target.join(".env.example");
    let env_target = target.join(".env");

    // 1. 每次启动，强制用 exe 内置的最新 compose 文件覆盖本地
    //    这样可以保证软件升级后，基础设施配置跟着自动升级
    if let Some(file) = EMBEDDED.get_file("docker-compose.yml") {
        fs::write(&compose_target, file.contents())
            .map_err(|e| format!("write docker-compose.yml: {}", e))?;
        println!("[launcher] updated docker-compose.yml from embedded assets");
    }

    // 2. 同样更新 .env.example
    if let Some(file) = EMBEDDED.get_file(".env.example") {
        fs::write(&env_example_target, file.contents())
            .map_err(|e| format!("write .env.example: {}", e))?;
    }

    // 3. 如果 .env 不存在，用 example 拷贝一份
    if env_example_target.exists() && !env_target.exists() {
        let _ = fs::copy(&env_example_target, &env_target);
        println!("[launcher] created .env from .env.example");
    }

    // 4. 强制覆盖解压后端代码资源
    //    利用 Docker build 缓存，覆盖源码不会导致重复构建
    println!("[launcher] extracting/updating assets to {:?}", target);
    extract_dir(&EMBEDDED, &target)?;

    Ok(target)
}

// ===== Docker 探测 =====
#[derive(Debug)]
enum DockerCmd {
    Exe(PathBuf),
    CmdFallback,
}

impl DockerCmd {
    fn build(&self) -> Command {
        match self {
            DockerCmd::Exe(p) => Command::new(p),
            DockerCmd::CmdFallback => {
                if cfg!(target_os = "windows") {
                    let mut c = Command::new("cmd");
                    c.arg("/C").arg("docker");
                    c
                } else {
                    let mut c = Command::new("sh");
                    c.arg("-c").arg("docker");
                    c
                }
            }
        }
    }
}

enum DockerStatus {
    NotInstalled,
    DaemonDown,
    NoCompose,
    TooOld(String),
    Ready(DockerCmd),
}

fn collect_candidates() -> Vec<DockerCmd> {
    let mut out = Vec::new();
    
    if cfg!(target_os = "windows") {
        let paths = [
            r"C:\Program Files\Docker\Docker\resources\bin\docker.exe",
            r"C:\Program Files\Docker Toolbox\docker.exe",
        ];
        for p in paths {
            let pb = PathBuf::from(p);
            if pb.exists() {
                out.push(DockerCmd::Exe(pb));
            }
        }
        if let Some(local) = dirs::data_local_dir() {
            let p = local.join("Docker").join("Docker").join("resources").join("bin").join("docker.exe");
            if p.exists() {
                out.push(DockerCmd::Exe(p));
            }
        }
    } else if cfg!(target_os = "linux") {
        let paths = ["/usr/bin/docker", "/usr/local/bin/docker", "/snap/bin/docker"];
        for p in paths {
            let pb = PathBuf::from(p);
            if pb.exists() {
                out.push(DockerCmd::Exe(pb));
            }
        }
    } else if cfg!(target_os = "macos") {
        let paths = [
            "/usr/local/bin/docker",
            "/opt/homebrew/bin/docker",
            "/Applications/Docker.app/Contents/Resources/bin/docker",
        ];
        for p in paths {
            let pb = PathBuf::from(p);
            if pb.exists() {
                out.push(DockerCmd::Exe(pb));
            }
        }
    }

    out.push(DockerCmd::CmdFallback);
    out
}

fn run_cmd(cmd: &DockerCmd, args: &[&str]) -> Result<Output, String> {
    let mut c = cmd.build();
    c.args(args);
    c.output().map_err(|e| e.to_string())
}

fn probe_docker() -> DockerStatus {
    let candidates = collect_candidates();
    let mut found_cmd = None;
    let mut version_str = String::new();

    // 1. 找哪个候选能跑通 `docker --version`
    for cand in candidates {
        if let Ok(out) = run_cmd(&cand, &["--version"]) {
            if out.status.success() {
                version_str = String::from_utf8_lossy(&out.stdout).trim().to_string();
                found_cmd = Some(cand);
                break;
            }
        }
    }

    let cmd = match found_cmd {
        Some(c) => c,
        None => return DockerStatus::NotInstalled,
    };

    // 2. 检查 Daemon 是否在跑（用 ps 命令，它必须连上 Server）
    if let Ok(out) = run_cmd(&cmd, &["ps"]) {
        if !out.status.success() {
            return DockerStatus::DaemonDown;
        }
    } else {
        return DockerStatus::DaemonDown;
    }

    // 3. 检查 Compose 插件
    let _compose_ver = match run_cmd(&cmd, &["compose", "version"]) {
        Ok(out) if out.status.success() => {
            String::from_utf8_lossy(&out.stdout).trim().to_string()
        }
        _ => return DockerStatus::NoCompose,
    };

    // 4. 版本校验（简易）
    if version_str.contains("1.") {
        return DockerStatus::TooOld(version_str);
    }

    DockerStatus::Ready(cmd)
}

// ===== 启动 compose =====
fn start_compose(cmd: &DockerCmd, root: &Path) -> Result<(), String> {
    let mut c = cmd.build();
    c.args(["compose", "up", "-d"]).current_dir(root);

    let output = c.output().map_err(|e| format!("spawn failed: {}", e))?;
    let stdout = String::from_utf8_lossy(&output.stdout).to_string();
    let stderr = String::from_utf8_lossy(&output.stderr).to_string();

    if !output.status.success() {
        let combined = format!("{}{}", stdout, stderr);
        let lower = combined.to_lowercase();

        // 识别 Docker 引擎未启动的底层报错
        if lower.contains("failed to connect to the docker api")
            || lower.contains("npipe:////./pipe/dockerdesktoplinuxengine")
        {
            return Err(
                "检测到 Docker 后台服务未启动或正在重启。\n\n\
                 【解决方法】\n\
                 1. 在开始菜单找到并打开 Docker Desktop\n\
                 2. 等待任务栏托盘图标由橙色变为绿色（约 30 秒）\n\
                 3. 重新打开本软件".to_string()
            );
        }

        // 识别 Docker Hub 访问超时
        if lower.contains("auth.docker.io")
            || lower.contains("failed to authorize")
            || lower.contains("failed to fetch anonymous token")
            || lower.contains("registry-1.docker.io")
        {
            return Err(format!(
                "无法访问 Docker Hub 拉取镜像。\n\n\
                 【解决方法】\n\
                 1. 打开 Docker Desktop 设置 -> Docker Engine\n\
                 2. 在 JSON 中添加以下配置（注意逗号）：\n\
                 \"registry-mirrors\": [\n\
                   \"https://docker.1ms.run\",\n\
                   \"https://docker.xuanyuan.me\",\n\
                   \"https://docker.m.daocloud.io\"\n\
                 ]\n\
                 3. 点击 Apply & Restart，等 Docker 重启后重新打开本软件\n\n\
                 === 原始错误 ===\n{}", combined
            ));
        }

        return Err(format!("docker compose 启动失败:\n{}", combined));
    }
    Ok(())
}

// ===== 等待后端 =====
fn wait_for_backend() -> Result<(), String> {
    let start = Instant::now();
    let timeout = Duration::from_secs(MAX_WAIT_SECONDS);

    while start.elapsed() < timeout {
        if is_backend_running() {
            return Ok(());
        }
        thread::sleep(Duration::from_millis(POLL_INTERVAL_MS));
    }

    Err("端口 8000 在 180 秒内未就绪。可能是后端启动报错，请检查日志。".to_string())
}

// ===== 主入口 =====
pub fn ensure_backend_ready() -> Result<(), String> {
    if is_backend_running() {
        return Ok(());
    }

    let root = extract_assets_if_needed().map_err(|e| format!("解压资源失败：{}", e))?;

    // 探测并引导
    let docker = match probe_docker() {
        DockerStatus::Ready(cmd) => cmd,
        DockerStatus::NotInstalled => {
            return Err(
                "未检测到 Docker Desktop。\n\n\
                 【解决方法】\n\
                 1. 前往官网下载：https://www.docker.com/products/docker-desktop/\n\
                 2. 安装时勾选 \"Use WSL 2 instead of Hyper-V\"\n\
                 3. 安装完成后重启电脑\n\
                 4. 启动 Docker Desktop，等待任务栏图标变绿\n\
                 5. 重新打开本软件".to_string()
            );
        }
        DockerStatus::DaemonDown => {
            return Err(
                "检测到 Docker 已安装，但后台服务未启动。\n\n\
                 【解决方法】\n\
                 1. 在开始菜单找到并打开 Docker Desktop\n\
                 2. 等待任务栏托盘图标由橙色变为绿色（约 30 秒）\n\
                 3. 重新打开本软件".to_string()
            );
        }
        DockerStatus::NoCompose => {
            return Err(
                "检测到 Docker 安装不完整或版本过旧（缺少 Compose 插件）。\n\n\
                 【解决方法】\n\
                 请前往 Docker 官网下载最新版 Docker Desktop 进行覆盖安装。\n\
                 https://www.docker.com/products/docker-desktop/".to_string()
            );
        }
        DockerStatus::TooOld(ver) => {
            return Err(format!(
                "当前 Docker 版本过旧：{}\n\n\
                 【解决方法】\n\
                 本软件要求 Docker 20.10 及以上版本。\n\
                 请前往官网下载最新版进行覆盖安装：\n\
                 https://www.docker.com/products/docker-desktop/", ver
            ));
        }
    };

    println!("[launcher] starting docker compose...");
    start_compose(&docker, &root).map_err(|e| format!("启动失败：{}", e))?;

    println!("[launcher] waiting for backend...");
    wait_for_backend()?;

    Ok(())
}