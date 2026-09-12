use std::ffi::OsStr;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};

use crate::cache::{relative_cache_path, CacheError};

#[derive(Debug, PartialEq, Eq)]
pub enum LibraryError {
    InvalidPath,
    Missing,
}

impl std::fmt::Display for LibraryError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidPath => write!(f, "path must stay inside the library"),
            Self::Missing => write!(f, "file not found in the library"),
        }
    }
}

impl std::error::Error for LibraryError {}

impl From<CacheError> for LibraryError {
    fn from(error: CacheError) -> Self {
        match error {
            CacheError::InvalidPath | CacheError::Missing => Self::InvalidPath,
        }
    }
}

pub fn library_root(home: &Path, configured: Option<&OsStr>) -> PathBuf {
    match configured {
        Some(value) if !value.is_empty() => PathBuf::from(value),
        _ => home.join("Music"),
    }
}

pub fn library_file(library_root: &Path, relative: &str) -> Result<PathBuf, LibraryError> {
    let dest = library_root.join(relative_cache_path(relative)?);
    match fs::metadata(&dest) {
        Ok(meta) if meta.is_file() => Ok(dest),
        _ => Err(LibraryError::Missing),
    }
}

pub fn reveal_in_file_manager(path: &Path) -> io::Result<()> {
    let status = reveal_command(path).status()?;
    if status.success() {
        Ok(())
    } else {
        Err(io::Error::new(
            io::ErrorKind::Other,
            format!("could not reveal {}", path.display()),
        ))
    }
}

fn reveal_command(path: &Path) -> std::process::Command {
    #[cfg(target_os = "macos")]
    {
        let mut command = std::process::Command::new("open");
        command.arg("-R").arg(path);
        command
    }
    #[cfg(target_os = "windows")]
    {
        let mut command = std::process::Command::new("explorer");
        command.arg(format!("/select,{}", path.display()));
        command
    }
    #[cfg(not(any(target_os = "macos", target_os = "windows")))]
    {
        let mut command = std::process::Command::new("xdg-open");
        command.arg(path.parent().unwrap_or(path));
        command
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn library_root_defaults_to_music() {
        assert_eq!(
            library_root(Path::new("/Users/c.wood"), None),
            PathBuf::from("/Users/c.wood/Music")
        );
    }

    #[test]
    fn library_root_uses_the_host_mount() {
        assert_eq!(
            library_root(
                Path::new("/Users/c.wood"),
                Some(OsStr::new("/Volumes/Samples"))
            ),
            PathBuf::from("/Volumes/Samples")
        );
        assert_eq!(
            library_root(Path::new("/Users/c.wood"), Some(OsStr::new(""))),
            PathBuf::from("/Users/c.wood/Music")
        );
    }

    #[test]
    fn library_file_joins_the_catalog_path() {
        let dir = tempfile::tempdir().unwrap();
        let dest = dir.path().join("Drums").join("Kicks").join("kick.wav");
        fs::create_dir_all(dest.parent().unwrap()).unwrap();
        fs::File::create(&dest).unwrap().write_all(b"RIFF").unwrap();
        assert_eq!(
            library_file(dir.path(), "Drums/Kicks/kick.wav").unwrap(),
            dest
        );
    }

    #[test]
    fn library_file_rejects_parent_segments_and_missing_files() {
        let dir = tempfile::tempdir().unwrap();
        assert_eq!(
            library_file(dir.path(), "../secret.wav"),
            Err(LibraryError::InvalidPath)
        );
        assert_eq!(
            library_file(dir.path(), "Drums/Kicks/kick.wav"),
            Err(LibraryError::Missing)
        );
    }

    #[test]
    fn reveal_command_selects_the_file() {
        let path = Path::new("/Volumes/Samples/Drums/Kicks/kick.wav");
        let command = reveal_command(path);
        #[cfg(target_os = "macos")]
        {
            assert_eq!(command.get_program(), "open");
            assert_eq!(
                command.get_args().collect::<Vec<_>>(),
                [OsStr::new("-R"), path.as_os_str()]
            );
        }
        #[cfg(target_os = "windows")]
        {
            let expected = format!("/select,{}", path.display());
            assert_eq!(command.get_program(), "explorer");
            assert_eq!(
                command.get_args().collect::<Vec<_>>(),
                [OsStr::new(&expected)]
            );
        }
        #[cfg(not(any(target_os = "macos", target_os = "windows")))]
        {
            assert_eq!(command.get_program(), "xdg-open");
            assert_eq!(
                command.get_args().collect::<Vec<_>>(),
                [path.parent().unwrap().as_os_str()]
            );
        }
    }
}
