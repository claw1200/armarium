use std::path::{Path, PathBuf};

#[derive(Debug, PartialEq, Eq)]
pub enum FileDragError {
    Missing(PathBuf),
    Outside(PathBuf),
}

impl std::fmt::Display for FileDragError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Missing(path) => write!(f, "file not found: {}", path.display()),
            Self::Outside(_) => write!(f, "path must stay inside the cache"),
        }
    }
}

impl std::error::Error for FileDragError {}

pub fn existing_files(paths: &[PathBuf]) -> Result<Vec<PathBuf>, FileDragError> {
    paths
        .iter()
        .map(|path| {
            if path.is_file() {
                Ok(path.clone())
            } else {
                Err(FileDragError::Missing(path.clone()))
            }
        })
        .collect()
}

pub fn inside_cache(cache_root: &Path, dest: &Path) -> Result<PathBuf, FileDragError> {
    let dest = dest.to_path_buf();
    let files = existing_files(std::slice::from_ref(&dest))?;
    let canonical = files[0]
        .canonicalize()
        .map_err(|_| FileDragError::Missing(dest.clone()))?;
    let root = cache_root
        .canonicalize()
        .map_err(|_| FileDragError::Missing(cache_root.to_path_buf()))?;
    if !canonical.starts_with(&root) {
        return Err(FileDragError::Outside(canonical));
    }
    Ok(canonical)
}

pub fn start(window: &tauri::WebviewWindow, paths: &[PathBuf]) -> Result<(), String> {
    let files = existing_files(paths).map_err(|error| error.to_string())?;
    let canonical: Vec<PathBuf> = files
        .iter()
        .map(|path| path.canonicalize())
        .collect::<Result<_, _>>()
        .map_err(|error| error.to_string())?;

    drag::start_drag(
        #[cfg(target_os = "linux")]
        &window.gtk_window().map_err(|error| error.to_string())?,
        #[cfg(not(target_os = "linux"))]
        window,
        drag::DragItem::Files(canonical),
        drag::Image::Raw(include_bytes!("../icons/32x32.png").to_vec()),
        |_, _| {},
        drag::Options::default(),
    )
    .map_err(|error| error.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::fixture;
    use std::path::Path;

    #[test]
    fn existing_files_rejects_a_missing_path() {
        let path = PathBuf::from("no-such-file.wav");
        assert_eq!(
            existing_files(std::slice::from_ref(&path)),
            Err(FileDragError::Missing(path))
        );
    }

    #[test]
    fn existing_files_accepts_the_bundled_fixture() {
        let path = fixture::wav_path_in(Path::new(env!("CARGO_MANIFEST_DIR")));
        assert_eq!(existing_files(std::slice::from_ref(&path)), Ok(vec![path]));
    }

    #[test]
    fn inside_cache_accepts_a_file_under_the_cache_root() {
        let dir = tempfile::tempdir().unwrap();
        let dest = dir.path().join("Drums").join("Kicks").join("kick.wav");
        std::fs::create_dir_all(dest.parent().unwrap()).unwrap();
        std::fs::write(&dest, b"RIFF").unwrap();
        let cached = inside_cache(dir.path(), &dest).unwrap();
        assert_eq!(cached, dest.canonicalize().unwrap());
    }

    #[test]
    fn inside_cache_rejects_a_file_outside_the_cache_root() {
        let cache = tempfile::tempdir().unwrap();
        let outside = tempfile::tempdir().unwrap();
        let dest = outside.path().join("kick.wav");
        std::fs::write(&dest, b"RIFF").unwrap();
        assert_eq!(
            inside_cache(cache.path(), &dest),
            Err(FileDragError::Outside(dest.canonicalize().unwrap()))
        );
    }
}
