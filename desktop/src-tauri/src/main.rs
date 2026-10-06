#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod backend_launcher;

use backend_launcher::ensure_backend_ready;
use tauri_plugin_dialog::{DialogExt, MessageDialogKind};

fn main() {
    // 1. 确保后端就绪（阻塞）
    if let Err(err) = ensure_backend_ready() {
        eprintln!("[launcher] ERROR: {}", err);

        // 弹系统对话框
        tauri::Builder::default()
            .plugin(tauri_plugin_dialog::init())
            .setup(move |app| {
                let handle = app.handle().clone();
                let msg = format!(
                    "无法启动后端服务:\n\n{}\n\n请确认:\n1. Docker Desktop 已启动\n2. 项目路径正确\n3. docker 命令可用",
                    err
                );

                handle
                    .dialog()
                    .message(msg)
                    .title("后端启动失败")
                    .kind(MessageDialogKind::Error)
                    .show(|_| {
                        std::process::exit(1);
                    });

                Ok(())
            })
            .run(tauri::generate_context!())
            .expect("error while running tauri application");

        return;
    }

    // 2. 后端就绪，正常启动
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}