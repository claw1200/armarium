use tauri::Manager;

mod cache;
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

#[tauri::command]
async fn cache_sample(
    app: tauri::AppHandle,
    relative_path: String,
    api_base: String,
) -> Result<String, String> {
    let home = app.path().home_dir().map_err(|error| error.to_string())?;
    let root = cache::cache_root(&home);
    tauri::async_runtime::spawn_blocking(move || {
        cache::download(&root, &relative_path, &api_base)
            .map(|path| path.to_string_lossy().into_owned())
            .map_err(|error| error.to_string())
    })
    .await
    .map_err(|error| error.to_string())?
}

#[derive(serde::Serialize)]
#[serde(tag = "status", rename_all = "camelCase")]
enum CachedDrag {
    Started { path: String },
    NeedsDownload,
}

#[tauri::command]
fn start_cached_drag(
    app: tauri::AppHandle,
    window: tauri::WebviewWindow,
    relative_path: String,
) -> Result<CachedDrag, String> {
    let home = app.path().home_dir().map_err(|error| error.to_string())?;
    let root = cache::cache_root(&home);
    match cache::complete_file(&root, &relative_path) {
        Ok(dest) => {
            let dest = file_drag::inside_cache(&root, &dest).map_err(|error| error.to_string())?;
            file_drag::start(&window, std::slice::from_ref(&dest))?;
            Ok(CachedDrag::Started {
                path: dest.to_string_lossy().into_owned(),
            })
        }
        Err(cache::CacheError::Missing) => Ok(CachedDrag::NeedsDownload),
        Err(error) => Err(error.to_string()),
    }
}

#[tauri::command]
fn cached_paths(app: tauri::AppHandle, relative_paths: Vec<String>) -> Result<Vec<String>, String> {
    let home = app.path().home_dir().map_err(|error| error.to_string())?;
    let root = cache::cache_root(&home);
    Ok(cache::cached_relatives(&root, &relative_paths))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            fixture_sample,
            start_fixture_drag,
            cache_sample,
            start_cached_drag,
            cached_paths
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
