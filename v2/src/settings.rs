//! Bounded storeValue dropdown persistence. No result/network cache.
use serde_json::{json, Value};
use std::{
    io::{Read, Write},
    path::Path,
    sync::Mutex,
};
static LANE: Mutex<()> = Mutex::new(());
const LIMIT: u64 = 4096;
fn read(path: &Path) -> Result<Value, String> {
    match std::fs::symlink_metadata(path) {
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => return Ok(json!({})),
        Ok(m) if m.is_file() && !m.file_type().is_symlink() && m.len() <= LIMIT => {}
        _ => return Err("Dropdown storage unavailable or invalid".into()),
    }
    let mut bytes = vec![];
    std::fs::File::open(path)
        .and_then(|f| f.take(LIMIT + 1).read_to_end(&mut bytes))
        .map_err(|_| "Dropdown storage unavailable")?;
    if bytes.len() > LIMIT as usize {
        return Err("Dropdown storage exceeds limit".into());
    }
    let v: Value = serde_json::from_slice(&bytes).map_err(|_| "Dropdown storage corrupt")?;
    let o = v.as_object().ok_or("Dropdown storage corrupt")?;
    if o.len() > 8
        || o.iter().any(|(k, v)| {
            !super::COMMANDS.contains(&k.as_str())
                || !super::choices(k)
                    .is_some_and(|options| options.iter().any(|(id, _)| Some(*id) == v.as_str()))
        })
    {
        return Err("Dropdown storage corrupt".into());
    }
    Ok(v)
}
pub fn load(dir: &Path, command: &str) -> Result<Option<String>, String> {
    let _guard = LANE.lock().map_err(|_| "Dropdown storage busy")?;
    Ok(read(&dir.join("dropdowns.json"))?[command]
        .as_str()
        .map(String::from))
}
pub fn save(dir: &Path, command: &str, value: &str) -> Result<(), String> {
    let _guard = LANE.lock().map_err(|_| "Dropdown storage busy")?;
    let path = dir.join("dropdowns.json");
    let mut state = read(&path)?;
    state[command] = json!(value);
    std::fs::create_dir_all(dir).map_err(|_| "Dropdown storage unavailable")?;
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        std::fs::set_permissions(dir, std::fs::Permissions::from_mode(0o700))
            .map_err(|_| "Dropdown storage permissions failed")?;
    }
    let mut file =
        tempfile::NamedTempFile::new_in(dir).map_err(|_| "Dropdown storage unavailable")?;
    file.write_all(&serde_json::to_vec(&state).map_err(|_| "Dropdown storage invalid")?)
        .and_then(|_| file.as_file().sync_all())
        .map_err(|_| "Dropdown storage write failed")?;
    file.persist(path)
        .map_err(|_| "Dropdown storage replace failed")?;
    #[cfg(unix)]
    std::fs::File::open(dir)
        .and_then(|f| f.sync_all())
        .map_err(|_| "Dropdown storage sync failed")?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn atomic_bounded_corruption_and_concurrent_choices() {
        let dir = tempfile::tempdir().unwrap();
        assert_eq!(load(dir.path(), "ip2long").unwrap(), None);
        save(dir.path(), "ip2long", "IPv6").unwrap();
        assert_eq!(load(dir.path(), "ip2long").unwrap(), Some("IPv6".into()));
        std::thread::scope(|s| {
            for (command, value) in [
                ("long2ip", "IPv6"),
                ("geoLocation", "zh-CN"),
                ("ip2long", "IPv4"),
            ] {
                let dir = dir.path();
                s.spawn(move || save(dir, command, value).unwrap());
            }
        });
        assert_eq!(load(dir.path(), "long2ip").unwrap(), Some("IPv6".into()));
        assert_eq!(
            load(dir.path(), "geoLocation").unwrap(),
            Some("zh-CN".into())
        );
        assert_eq!(load(dir.path(), "ip2long").unwrap(), Some("IPv4".into()));
        let path = dir.path().join("dropdowns.json");
        for bad in [
            b"{broken".to_vec(),
            b"[]".to_vec(),
            b"{\"ip2long\":\"unknown\"}".to_vec(),
            vec![b' '; 4097],
        ] {
            std::fs::write(&path, &bad).unwrap();
            assert!(load(dir.path(), "ip2long").is_err());
            assert!(save(dir.path(), "ip2long", "IPv4").is_err());
            assert_eq!(std::fs::read(&path).unwrap(), bad);
        }
    }
}
