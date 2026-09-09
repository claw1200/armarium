use std::path::{Path, PathBuf};

use tauri::{AppHandle, Manager};

pub const WAV_RELATIVE_PATH: &str = "resources/kick.wav";

#[derive(Debug, PartialEq, Eq)]
pub enum FixtureError {
    Missing(PathBuf),
}

impl std::fmt::Display for FixtureError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Missing(path) => write!(f, "file not found: {}", path.display()),
        }
    }
}

impl std::error::Error for FixtureError {}

#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct FixtureSample {
    pub name: String,
    pub path: String,
}

pub fn wav_path_in(resource_dir: &Path) -> PathBuf {
    resource_dir.join(WAV_RELATIVE_PATH)
}

pub fn require_wav(path: PathBuf) -> Result<PathBuf, FixtureError> {
    if path.is_file() {
        Ok(path)
    } else {
        Err(FixtureError::Missing(path))
    }
}

fn resource_dirs(app: &AppHandle) -> Vec<PathBuf> {
    let mut dirs = Vec::new();
    if let Ok(dir) = app.path().resource_dir() {
        dirs.push(dir);
    }
    dirs.push(PathBuf::from(env!("CARGO_MANIFEST_DIR")));
    dirs
}

pub fn wav_path(app: &AppHandle) -> Result<PathBuf, String> {
    let mut last_missing = PathBuf::from(WAV_RELATIVE_PATH);
    for dir in resource_dirs(app) {
        match require_wav(wav_path_in(&dir)) {
            Ok(path) => return Ok(path),
            Err(FixtureError::Missing(path)) => last_missing = path,
        }
    }
    Err(FixtureError::Missing(last_missing).to_string())
}

pub fn sample(app: &AppHandle) -> Result<FixtureSample, String> {
    let path = wav_path(app)?;
    let name = path
        .file_name()
        .map(|name| name.to_string_lossy().into_owned())
        .ok_or_else(|| format!("file not found: {}", path.display()))?;
    Ok(FixtureSample {
        name,
        path: path.to_string_lossy().into_owned(),
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wav_path_in_mirrors_the_server_style_relative_path() {
        assert_eq!(
            wav_path_in(Path::new("/library")),
            PathBuf::from("/library/resources/kick.wav")
        );
    }

    #[test]
    fn bundled_fixture_is_a_wave_file() {
        let path = wav_path_in(Path::new(env!("CARGO_MANIFEST_DIR")));
        let bytes = std::fs::read(&path).expect("fixture wav");
        assert_eq!(&bytes[..4], b"RIFF");
        assert_eq!(&bytes[8..12], b"WAVE");
        assert_eq!(require_wav(path.clone()), Ok(path));
    }

    #[test]
    fn require_wav_rejects_a_missing_file() {
        let path = PathBuf::from("missing.wav");
        assert_eq!(require_wav(path.clone()), Err(FixtureError::Missing(path)));
    }
}
