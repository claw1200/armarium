use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::LazyLock;
use std::time::Duration;

use reqwest::StatusCode;
use reqwest::Url;

#[derive(Debug, PartialEq, Eq)]
pub enum CacheError {
    InvalidPath,
    Missing,
}

impl std::fmt::Display for CacheError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidPath => write!(f, "path must stay inside the cache"),
            Self::Missing => write!(f, "sample is not cached"),
        }
    }
}

impl std::error::Error for CacheError {}

#[derive(Debug)]
pub enum DownloadError {
    InvalidPath,
    Http(String),
    Io(io::Error),
}

impl std::fmt::Display for DownloadError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidPath => write!(f, "{}", CacheError::InvalidPath),
            Self::Http(message) => write!(f, "{message}"),
            Self::Io(error) => write!(f, "{error}"),
        }
    }
}

impl std::error::Error for DownloadError {}

impl From<CacheError> for DownloadError {
    fn from(error: CacheError) -> Self {
        match error {
            CacheError::InvalidPath | CacheError::Missing => Self::InvalidPath,
        }
    }
}

impl From<io::Error> for DownloadError {
    fn from(error: io::Error) -> Self {
        Self::Io(error)
    }
}

pub fn cache_root(home: &Path) -> PathBuf {
    home.join("Armarium").join("cache")
}

pub fn relative_cache_path(relative: &str) -> Result<PathBuf, CacheError> {
    let mut path = PathBuf::new();
    for part in relative.split(['/', '\\']) {
        match part {
            "" | "." => continue,
            ".." => return Err(CacheError::InvalidPath),
            name => path.push(name),
        }
    }
    if path.as_os_str().is_empty() {
        return Err(CacheError::InvalidPath);
    }
    Ok(path)
}

pub fn cached_file_path(cache_root: &Path, relative: &str) -> Result<PathBuf, CacheError> {
    Ok(cache_root.join(relative_cache_path(relative)?))
}

pub fn complete_file(cache_root: &Path, relative: &str) -> Result<PathBuf, CacheError> {
    let dest = cached_file_path(cache_root, relative)?;
    reject_symlinks_under(cache_root, &dest)?;
    match fs::symlink_metadata(&dest) {
        Ok(meta) if meta.is_file() && meta.len() > 0 => Ok(dest),
        Ok(meta) if meta.file_type().is_symlink() => Err(CacheError::InvalidPath),
        _ => Err(CacheError::Missing),
    }
}

pub fn audio_url(api_base: &str, relative: &str) -> Result<Url, DownloadError> {
    let parts = relative_cache_path(relative)?;
    let base = api_base.trim().trim_end_matches('/');
    let mut url = Url::parse(&format!("{base}/audio"))
        .map_err(|error| DownloadError::Http(error.to_string()))?;
    url.path_segments_mut()
        .map_err(|()| DownloadError::InvalidPath)?
        .extend(parts.iter().filter_map(|part| part.to_str()));
    Ok(url)
}

fn reject_symlinks_under(root: &Path, dest: &Path) -> Result<(), CacheError> {
    let relative = dest
        .strip_prefix(root)
        .map_err(|_| CacheError::InvalidPath)?;
    let mut current = root.to_path_buf();
    for component in relative.components() {
        current.push(component);
        match fs::symlink_metadata(&current) {
            Err(error) if error.kind() == io::ErrorKind::NotFound => return Ok(()),
            Err(_) => return Err(CacheError::InvalidPath),
            Ok(meta) if meta.file_type().is_symlink() => return Err(CacheError::InvalidPath),
            Ok(_) => {}
        }
    }
    Ok(())
}

fn replace_with_reader<R: io::Read>(dest: &Path, reader: &mut R) -> io::Result<()> {
    let parent = dest.parent().ok_or_else(|| {
        io::Error::new(
            io::ErrorKind::InvalidInput,
            CacheError::InvalidPath.to_string(),
        )
    })?;
    fs::create_dir_all(parent)?;
    let mut tmp = tempfile::NamedTempFile::new_in(parent)?;
    io::copy(reader, tmp.as_file_mut())?;
    tmp.as_file_mut().sync_all()?;
    tmp.persist(dest).map_err(|error| error.error)?;
    Ok(())
}

fn http_client() -> &'static reqwest::blocking::Client {
    static CLIENT: LazyLock<reqwest::blocking::Client> = LazyLock::new(|| {
        reqwest::blocking::Client::builder()
            .connect_timeout(Duration::from_secs(10))
            .timeout(Duration::from_secs(300))
            .build()
            .expect("http client")
    });
    &CLIENT
}

pub fn download(
    cache_root: &Path,
    relative: &str,
    api_base: &str,
) -> Result<PathBuf, DownloadError> {
    let dest = match complete_file(cache_root, relative) {
        Ok(dest) => return Ok(dest),
        Err(CacheError::Missing) => cached_file_path(cache_root, relative)?,
        Err(error) => return Err(error.into()),
    };
    let url = audio_url(api_base, relative)?;
    let mut response = http_client()
        .get(url)
        .send()
        .map_err(|error| DownloadError::Http(error.to_string()))?;
    let status = response.status();
    if status != StatusCode::OK {
        return Err(DownloadError::Http(format!("download failed ({status})")));
    }
    replace_with_reader(&dest, &mut response)?;
    Ok(dest)
}

pub fn cached_relatives(cache_root: &Path, relatives: &[String]) -> Vec<String> {
    relatives
        .iter()
        .filter(|relative| complete_file(cache_root, relative).is_ok())
        .cloned()
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{Read, Write};
    use std::net::TcpListener;
    use std::thread;

    fn write_complete_file(dest: &Path, bytes: &[u8]) -> io::Result<()> {
        replace_with_reader(dest, &mut &*bytes)
    }

    #[test]
    fn cache_root_mirrors_the_project_layout() {
        assert_eq!(
            cache_root(Path::new("/Users/c.wood")),
            PathBuf::from("/Users/c.wood/Armarium/cache")
        );
    }

    #[test]
    fn cached_file_path_keeps_the_server_relative_path() {
        let root = Path::new("/tmp/Armarium/cache");
        assert_eq!(
            cached_file_path(root, "Drums/Kicks/kick.wav").unwrap(),
            root.join("Drums").join("Kicks").join("kick.wav")
        );
    }

    #[test]
    fn same_filename_in_different_folders_do_not_collide() {
        let root = Path::new("/tmp/Armarium/cache");
        let kicks = cached_file_path(root, "Drums/Kicks/kick.wav").unwrap();
        let loops = cached_file_path(root, "Loops/Kicks/kick.wav").unwrap();
        assert_ne!(kicks, loops);
    }

    #[test]
    fn relative_cache_path_rejects_parent_segments() {
        assert_eq!(
            relative_cache_path("../secret.wav"),
            Err(CacheError::InvalidPath)
        );
        assert_eq!(relative_cache_path(""), Err(CacheError::InvalidPath));
    }

    #[test]
    fn cached_relatives_returns_only_complete_hits() {
        let dir = tempfile::tempdir().unwrap();
        let kick = cached_file_path(dir.path(), "Drums/Kicks/kick.wav").unwrap();
        write_complete_file(&kick, b"RIFF").unwrap();
        assert_eq!(
            cached_relatives(
                dir.path(),
                &[
                    "Drums/Kicks/kick.wav".into(),
                    "Drums/Snares/snare.wav".into(),
                    "../escape.wav".into(),
                ]
            ),
            ["Drums/Kicks/kick.wav"]
        );
    }

    #[test]
    fn complete_file_requires_a_non_empty_cache_hit() {
        let dir = tempfile::tempdir().unwrap();
        assert_eq!(
            complete_file(dir.path(), "Drums/Kicks/kick.wav"),
            Err(CacheError::Missing)
        );
        let dest = cached_file_path(dir.path(), "Drums/Kicks/kick.wav").unwrap();
        write_complete_file(&dest, b"RIFF").unwrap();
        assert_eq!(
            complete_file(dir.path(), "Drums/Kicks/kick.wav").unwrap(),
            dest
        );
    }

    #[test]
    fn audio_url_encodes_path_segments() {
        assert_eq!(
            audio_url("http://127.0.0.1:8000/", "Pack/kick 01.wav")
                .unwrap()
                .as_str(),
            "http://127.0.0.1:8000/audio/Pack/kick%2001.wav"
        );
    }

    #[test]
    fn write_complete_file_does_not_leave_a_partial() {
        let dir = tempfile::tempdir().unwrap();
        let dest = dir.path().join("Drums").join("Kicks").join("kick.wav");
        write_complete_file(&dest, b"RIFF").unwrap();
        assert_eq!(fs::read(&dest).unwrap(), b"RIFF");
        let names: Vec<_> = fs::read_dir(dest.parent().unwrap())
            .unwrap()
            .map(|entry| entry.unwrap().file_name())
            .collect();
        assert_eq!(names, [std::ffi::OsString::from("kick.wav")]);
    }

    #[test]
    fn download_lands_at_the_mirrored_path() {
        let dir = tempfile::tempdir().unwrap();
        let (base, server) = spawn_audio_server(200, b"RIFFWAVE");
        let dest = download(dir.path(), "Drums/Kicks/kick.wav", &base).unwrap();
        server.join().unwrap();
        assert_eq!(
            dest,
            dir.path().join("Drums").join("Kicks").join("kick.wav")
        );
        assert_eq!(fs::read(&dest).unwrap(), b"RIFFWAVE");
    }

    #[test]
    fn download_rejects_a_partial_response() {
        let dir = tempfile::tempdir().unwrap();
        let (base, server) = spawn_audio_server(206, b"RIFF");
        let error = download(dir.path(), "Drums/Kicks/kick.wav", &base).unwrap_err();
        server.join().unwrap();
        assert!(matches!(error, DownloadError::Http(message) if message.contains("206")));
        assert!(!dir
            .path()
            .join("Drums")
            .join("Kicks")
            .join("kick.wav")
            .exists());
    }

    #[test]
    fn download_does_not_overwrite_a_complete_file() {
        let dir = tempfile::tempdir().unwrap();
        let dest = cached_file_path(dir.path(), "Drums/Kicks/kick.wav").unwrap();
        write_complete_file(&dest, b"already").unwrap();
        let result = download(dir.path(), "Drums/Kicks/kick.wav", "http://127.0.0.1:1").unwrap();
        assert_eq!(result, dest);
        assert_eq!(fs::read(&dest).unwrap(), b"already");
    }

    #[test]
    fn download_keeps_two_kick_wavs_apart() {
        let dir = tempfile::tempdir().unwrap();
        write_complete_file(
            &cached_file_path(dir.path(), "Drums/Kicks/kick.wav").unwrap(),
            b"drums",
        )
        .unwrap();
        write_complete_file(
            &cached_file_path(dir.path(), "Loops/Kicks/kick.wav").unwrap(),
            b"loops",
        )
        .unwrap();
        assert_eq!(
            fs::read(dir.path().join("Drums").join("Kicks").join("kick.wav")).unwrap(),
            b"drums"
        );
        assert_eq!(
            fs::read(dir.path().join("Loops").join("Kicks").join("kick.wav")).unwrap(),
            b"loops"
        );
    }

    #[cfg(unix)]
    #[test]
    fn download_rejects_a_symlink_in_the_cache_path() {
        let dir = tempfile::tempdir().unwrap();
        let outside = tempfile::tempdir().unwrap();
        std::os::unix::fs::symlink(outside.path(), dir.path().join("Drums")).unwrap();
        let error = download(dir.path(), "Drums/Kicks/kick.wav", "http://127.0.0.1:1").unwrap_err();
        assert!(matches!(error, DownloadError::InvalidPath));
        assert!(outside.path().read_dir().unwrap().next().is_none());
    }

    fn spawn_audio_server(status: u16, body: &'static [u8]) -> (String, thread::JoinHandle<()>) {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        let addr = listener.local_addr().unwrap();
        let handle = thread::spawn(move || {
            let (mut stream, _) = listener.accept().unwrap();
            let mut buf = [0u8; 4096];
            let mut request = Vec::new();
            loop {
                let n = stream.read(&mut buf).unwrap();
                request.extend_from_slice(&buf[..n]);
                if request.windows(4).any(|window| window == b"\r\n\r\n") || n == 0 {
                    break;
                }
            }
            let request = String::from_utf8_lossy(&request);
            assert!(request.contains("GET /audio/Drums/Kicks/kick.wav"));
            let reason = if status == 200 {
                "OK"
            } else {
                "Partial Content"
            };
            let header = format!(
                "HTTP/1.1 {status} {reason}\r\nContent-Length: {}\r\nConnection: close\r\n\r\n",
                body.len()
            );
            stream.write_all(header.as_bytes()).unwrap();
            stream.write_all(body).unwrap();
        });
        (format!("http://{addr}"), handle)
    }
}
