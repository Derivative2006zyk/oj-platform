#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod backend_launcher;

use backend_launcher::ensure_backend_ready;
use tauri::{
    menu::{Menu, MenuItem, PredefinedMenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    AppHandle, Manager, WindowEvent,
};
use tauri_plugin_dialog::{DialogExt, MessageDialogKind};

fn main() {
    // 1. 确保后端就绪
    if let Err(err) = ensure_backend_ready() {
        eprintln!("[launcher] ERROR: {}", err);

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

    // 2. 正常启动 + 托盘
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            build_tray(app)?;

            // 监听窗口关闭 → 隐藏
            if let Some(window) = app.get_webview_window("main") {
                let window_clone = window.clone();
                window.on_window_event(move |event| {
                    if let WindowEvent::CloseRequested { api, .. } = event {
                        api.prevent_close();
                        let _ = window_clone.hide();
                    }
                });
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

/// 显示主窗口（最小化也能恢复）
fn show_main_window(app: &AppHandle) {
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.unminimize();
        let _ = w.show();
        let _ = w.set_focus();
    }
}

/// 显示主窗口并跳转到指定路由
fn navigate_to(app: &AppHandle, path: &str) {
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.unminimize();
        let _ = w.show();
        let _ = w.set_focus();

        // 用 location.href 触发整页导航，Vue Router 会接管
        let js = format!(
            "window.location.href = '{}';",
            path
        );
        let _ = w.eval(&js);
    }
}

/// 创建系统托盘
fn build_tray(app: &mut tauri::App) -> Result<(), Box<dyn std::error::Error>> {
    let show_item = MenuItem::with_id(app, "show", "显示窗口", true, None::<&str>)?;
    let hide_item = MenuItem::with_id(app, "hide", "隐藏窗口", true, None::<&str>)?;
    let sep1 = PredefinedMenuItem::separator(app)?;
    let subs_item = MenuItem::with_id(app, "subs", "提交历史", true, None::<&str>)?;
    let stats_item = MenuItem::with_id(app, "stats", "统计", true, None::<&str>)?;
    let sep2 = PredefinedMenuItem::separator(app)?;
    let quit_item = MenuItem::with_id(app, "quit", "退出", true, None::<&str>)?;

    let menu = Menu::with_items(
        app,
        &[
            &show_item,
            &hide_item,
            &sep1,
            &subs_item,
            &stats_item,
            &sep2,
            &quit_item,
        ],
    )?;

    let _tray = TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .menu(&menu)
        .show_menu_on_left_click(false)
        .tooltip("OJ Platform")
        .on_menu_event(|app, event| {
            match event.id.as_ref() {
                "show" => show_main_window(app),
                "hide" => {
                    if let Some(w) = app.get_webview_window("main") {
                        let _ = w.hide();
                    }
                }
                "subs" => navigate_to(app, "/submissions"),
                "stats" => navigate_to(app, "/admin/stats"),
                "quit" => app.exit(0),
                _ => {}
            }
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::Click {
                button: MouseButton::Left,
                button_state: MouseButtonState::Up,
                ..
            } = event
            {
                let app = tray.app_handle();
                if let Some(w) = app.get_webview_window("main") {
                    let visible = w.is_visible().unwrap_or(false);
                    let minimized = w.is_minimized().unwrap_or(false);

                    // 窗口不可见 或 已最小化 → 恢复
                    if !visible || minimized {
                        let _ = w.unminimize();
                        let _ = w.show();
                        let _ = w.set_focus();
                    } else {
                        // 窗口正常显示 → 隐藏
                        let _ = w.hide();
                    }
                }
            }
        })
        .build(app)?;

    Ok(())
}