mod file_drag;
mod fixture;

#[tauri::command]
fn fixture_sample(app: tauri::AppHandle) -> Result<fixture::FixtureSample, String> {
    fixture::sample(&app)
}

#[tauri::command]
fn start_fixture_drag(app: tauri::AppHandle, window: tauri::WebviewWindow) -> Result<(), String> {
    let path = fixture::wav_path(&app)?;
    file_drag::start(&window, &[path])
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![fixture_sample, start_fixture_drag])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
