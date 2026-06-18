use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::HashMap;
use std::fs;
use std::io::{self, Cursor};
use std::path::{Component, Path, PathBuf};
use tauri::Manager;
use tempfile::tempdir;
use walkdir::WalkDir;
use zip::ZipArchive;

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct EnvironmentInfo {
    default_drafts_dir: Option<String>,
    detected_placeholder_id: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
struct InstallDraftRequest {
    source: String,
    drafts_dir: String,
    draft_name: Option<String>,
    placeholder_id: Option<String>,
    overwrite: bool,
}

#[derive(Debug, Serialize)]
#[serde(rename_all = "camelCase")]
struct InstallDraftResult {
    target_dir: String,
    placeholder_id: String,
    draft_name: String,
}

#[derive(Debug, thiserror::Error)]
enum InstallError {
    #[error("{0}")]
    Message(String),
    #[error(transparent)]
    Io(#[from] io::Error),
    #[error(transparent)]
    Json(#[from] serde_json::Error),
    #[error(transparent)]
    Zip(#[from] zip::result::ZipError),
    #[error(transparent)]
    Request(#[from] reqwest::Error),
}

type Result<T> = std::result::Result<T, InstallError>;

#[tauri::command]
async fn get_environment_info() -> std::result::Result<EnvironmentInfo, String> {
    tauri::async_runtime::spawn_blocking(|| {
        let default_drafts_dir = find_default_drafts_dir();
        let detected_placeholder_id = default_drafts_dir
            .as_ref()
            .and_then(|path| detect_placeholder_id(Path::new(path)));

        EnvironmentInfo {
            default_drafts_dir,
            detected_placeholder_id,
        }
    })
    .await
    .map_err(|error| error.to_string())
}

#[tauri::command]
async fn install_draft(request: InstallDraftRequest) -> std::result::Result<InstallDraftResult, String> {
    tauri::async_runtime::spawn_blocking(move || {
        install_draft_inner(request).map_err(|error| error.to_string())
    })
    .await
    .map_err(|error| error.to_string())?
}

fn install_draft_inner(request: InstallDraftRequest) -> Result<InstallDraftResult> {
    let drafts_root = PathBuf::from(request.drafts_dir.trim());
    if !drafts_root.is_dir() {
        return Err(InstallError::Message(format!(
            "剪映草稿目录不存在：{}",
            drafts_root.display()
        )));
    }

    let placeholder_id = request
        .placeholder_id
        .filter(|value| !value.trim().is_empty())
        .map(|value| value.trim().to_string())
        .or_else(|| detect_placeholder_id(&drafts_root))
        .ok_or_else(|| {
            InstallError::Message(
                "未能识别本机剪映占位符。请先在剪映创建一个空草稿，或手动填写占位符 ID。".to_string(),
            )
        })?;

    let temp = tempdir()?;
    let zip_bytes = fetch_source(&request.source)?;
    let extract_dir = temp.path().join("extract");
    fs::create_dir_all(&extract_dir)?;
    extract_zip_safe(&zip_bytes, &extract_dir)?;

    let source_root = single_root_or_self(&extract_dir)?;
    let inferred_name = infer_draft_name(&source_root).unwrap_or_else(|| "jy_draft".to_string());
    let draft_name = sanitize_name(
        request
            .draft_name
            .as_deref()
            .filter(|value| !value.trim().is_empty())
            .unwrap_or(&inferred_name),
    );
    let target_dir = choose_target_dir(&drafts_root, &draft_name, request.overwrite)?;
    copy_dir_all(&source_root, &target_dir)?;
    rewrite_draft(&target_dir, &drafts_root, &placeholder_id)?;

    Ok(InstallDraftResult {
        target_dir: target_dir.display().to_string(),
        placeholder_id,
        draft_name: target_dir
            .file_name()
            .and_then(|value| value.to_str())
            .unwrap_or(&draft_name)
            .to_string(),
    })
}

fn fetch_source(source: &str) -> Result<Vec<u8>> {
    let trimmed = source.trim();
    if trimmed.starts_with("http://") || trimmed.starts_with("https://") {
        let response = reqwest::blocking::get(trimmed)?.error_for_status()?;
        return Ok(response.bytes()?.to_vec());
    }
    Ok(fs::read(trimmed)?)
}

fn extract_zip_safe(bytes: &[u8], target_dir: &Path) -> Result<()> {
    let reader = Cursor::new(bytes);
    let mut archive = ZipArchive::new(reader)?;
    let root = target_dir.canonicalize()?;

    for index in 0..archive.len() {
        let mut file = archive.by_index(index)?;
        let enclosed = file
            .enclosed_name()
            .ok_or_else(|| InstallError::Message(format!("ZIP 包含不安全路径：{}", file.name())))?;
        if has_parent_component(&enclosed) {
            return Err(InstallError::Message(format!("ZIP 包含不安全路径：{}", file.name())));
        }
        let out_path = root.join(enclosed);
        if file.is_dir() {
            fs::create_dir_all(&out_path)?;
            continue;
        }
        if let Some(parent) = out_path.parent() {
            fs::create_dir_all(parent)?;
        }
        let mut out_file = fs::File::create(&out_path)?;
        io::copy(&mut file, &mut out_file)?;
    }
    Ok(())
}

fn has_parent_component(path: &Path) -> bool {
    path.components().any(|component| matches!(component, Component::ParentDir))
}

fn single_root_or_self(extract_dir: &Path) -> Result<PathBuf> {
    let entries: Vec<PathBuf> = fs::read_dir(extract_dir)?
        .filter_map(|entry| entry.ok().map(|value| value.path()))
        .filter(|path| path.file_name().and_then(|name| name.to_str()) != Some("__MACOSX"))
        .collect();
    if entries.len() == 1 && entries[0].is_dir() {
        Ok(entries[0].clone())
    } else {
        Ok(extract_dir.to_path_buf())
    }
}

fn infer_draft_name(source_root: &Path) -> Option<String> {
    let content_path = source_root.join("draft_content.json");
    let text = fs::read_to_string(content_path).ok()?;
    let value: Value = serde_json::from_str(&text).ok()?;
    value
        .get("name")
        .and_then(Value::as_str)
        .filter(|name| !name.trim().is_empty())
        .map(sanitize_name)
}

fn sanitize_name(value: &str) -> String {
    let cleaned: String = value
        .chars()
        .map(|ch| match ch {
            '<' | '>' | ':' | '"' | '/' | '\\' | '|' | '?' | '*' => '_',
            ch if ch.is_control() => '_',
            ch => ch,
        })
        .collect::<String>()
        .trim_matches([' ', '.'])
        .to_string();

    if cleaned.is_empty() {
        format!("jy_draft_{}", uuid_like_suffix())
    } else {
        cleaned
    }
}

fn uuid_like_suffix() -> String {
    use std::time::{SystemTime, UNIX_EPOCH};
    let millis = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_millis())
        .unwrap_or(0);
    format!("{:x}", millis)
}

fn choose_target_dir(root: &Path, name: &str, overwrite: bool) -> Result<PathBuf> {
    let target = root.join(name);
    if overwrite {
        if target.exists() {
            fs::remove_dir_all(&target)?;
        }
        return Ok(target);
    }
    if !target.exists() {
        return Ok(target);
    }
    for index in 2..1000 {
        let candidate = root.join(format!("{}_{}", name, index));
        if !candidate.exists() {
            return Ok(candidate);
        }
    }
    Err(InstallError::Message("无法创建唯一草稿目录名。".to_string()))
}

fn copy_dir_all(source: &Path, target: &Path) -> Result<()> {
    fs::create_dir_all(target)?;
    for entry in WalkDir::new(source) {
        let entry = entry.map_err(|error| InstallError::Message(error.to_string()))?;
        let relative = entry
            .path()
            .strip_prefix(source)
            .map_err(|error| InstallError::Message(error.to_string()))?;
        if relative.as_os_str().is_empty() {
            continue;
        }
        let destination = target.join(relative);
        if entry.file_type().is_dir() {
            fs::create_dir_all(&destination)?;
        } else {
            if let Some(parent) = destination.parent() {
                fs::create_dir_all(parent)?;
            }
            fs::copy(entry.path(), destination)?;
        }
    }
    Ok(())
}

fn rewrite_draft(draft_dir: &Path, drafts_root: &Path, placeholder_id: &str) -> Result<()> {
    let draft_name = draft_dir
        .file_name()
        .and_then(|value| value.to_str())
        .unwrap_or("jy_draft")
        .to_string();

    for entry in WalkDir::new(draft_dir) {
        let entry = entry.map_err(|error| InstallError::Message(error.to_string()))?;
        if !entry.file_type().is_file() || !is_json_like_draft_file(entry.path()) {
            continue;
        }
        rewrite_json_file(entry.path(), draft_dir, drafts_root, &draft_name, placeholder_id)?;
    }
    Ok(())
}

fn is_json_like_draft_file(path: &Path) -> bool {
    let name = path.file_name().and_then(|value| value.to_str()).unwrap_or("");
    matches!(
        name,
        "draft_content.json"
            | "draft_info.json"
            | "draft_meta_info.json"
            | "attachment_pc_common.json"
            | "draft_agency_config.json"
    ) || (name.starts_with("template") && name.ends_with(".tmp"))
}

fn rewrite_json_file(
    path: &Path,
    draft_dir: &Path,
    drafts_root: &Path,
    draft_name: &str,
    placeholder_id: &str,
) -> Result<()> {
    let text = fs::read_to_string(path)?;
    let mut value: Value = serde_json::from_str(&text)?;
    rewrite_json_value(&mut value, draft_dir, drafts_root, draft_name, placeholder_id);
    fs::write(path, serde_json::to_string_pretty(&value)?)?;
    Ok(())
}

fn rewrite_json_value(
    value: &mut Value,
    draft_dir: &Path,
    drafts_root: &Path,
    draft_name: &str,
    placeholder_id: &str,
) {
    match value {
        Value::Object(map) => {
            for (key, item) in map.iter_mut() {
                if key == "draft_name" {
                    *item = Value::String(draft_name.to_string());
                } else if key == "draft_fold_path" {
                    *item = Value::String(draft_dir.display().to_string().replace('\\', "/"));
                } else if key == "draft_root_path" {
                    *item = Value::String(drafts_root.display().to_string());
                } else if key == "name" && item.as_str() == Some("") {
                    *item = Value::String(draft_name.to_string());
                } else {
                    rewrite_json_value(item, draft_dir, drafts_root, draft_name, placeholder_id);
                }
            }
        }
        Value::Array(items) => {
            for item in items {
                rewrite_json_value(item, draft_dir, drafts_root, draft_name, placeholder_id);
            }
        }
        Value::String(text) => {
            *text = rewrite_material_path(text, draft_dir, placeholder_id);
        }
        _ => {}
    }
}

fn rewrite_material_path(value: &str, draft_dir: &Path, placeholder_id: &str) -> String {
    let normalized = value.replace('\\', "/");
    if let Some(suffix) = placeholder_suffix(&normalized) {
        return make_placeholder_path(placeholder_id, &suffix);
    }
    if let Some(suffix) = normalized.strip_prefix("__DRAFT_ROOT__/") {
        return make_placeholder_path(placeholder_id, suffix);
    }
    if normalized.starts_with("audio/") || normalized.starts_with("image/") || normalized.starts_with("video/") {
        return make_placeholder_path(placeholder_id, &normalized);
    }

    let path = Path::new(value);
    if path.is_absolute() {
        if let Ok(relative) = path.strip_prefix(draft_dir) {
            return make_placeholder_path(placeholder_id, &relative.to_string_lossy().replace('\\', "/"));
        }
    }
    value.to_string()
}

fn placeholder_suffix(value: &str) -> Option<String> {
    let marker = "##_draftpath_placeholder_";
    if !value.starts_with(marker) {
        return None;
    }
    let suffix_start = value.find("_##/").map(|index| index + 4)?;
    Some(value[suffix_start..].to_string())
}

fn make_placeholder_path(placeholder_id: &str, suffix: &str) -> String {
    format!(
        "##_draftpath_placeholder_{}_##/{}",
        placeholder_id,
        suffix.replace('\\', "/")
    )
}

fn detect_placeholder_id(drafts_root: &Path) -> Option<String> {
    let mut counts: HashMap<String, usize> = HashMap::new();
    let mut draft_dirs: Vec<PathBuf> = fs::read_dir(drafts_root)
        .ok()?
        .filter_map(|entry| entry.ok().map(|value| value.path()))
        .filter(|path| path.is_dir())
        .collect();
    draft_dirs.sort_by_key(|path| fs::metadata(path).and_then(|meta| meta.modified()).ok());
    draft_dirs.reverse();

    for draft_dir in draft_dirs.into_iter().take(100) {
        for filename in ["draft_content.json", "draft_info.json"] {
            let path = draft_dir.join(filename);
            let Ok(text) = fs::read_to_string(path) else {
                continue;
            };
            collect_placeholder_ids(&text, &mut counts);
        }
    }

    counts.into_iter().max_by_key(|(_, count)| *count).map(|(id, _)| id)
}

fn collect_placeholder_ids(text: &str, counts: &mut HashMap<String, usize>) {
    let marker = "##_draftpath_placeholder_";
    let mut rest = text;
    while let Some(start) = rest.find(marker) {
        let after_marker = &rest[start + marker.len()..];
        let Some(end) = after_marker.find("_##") else {
            break;
        };
        let id = &after_marker[..end];
        if !id.is_empty() {
            *counts.entry(id.to_string()).or_default() += 1;
        }
        rest = &after_marker[end + 3..];
    }
}

fn find_default_drafts_dir() -> Option<String> {
    let mut candidates = Vec::new();
    if let Ok(value) = std::env::var("JIANYING_NATIVE_DRAFTS_DIR") {
        candidates.push(PathBuf::from(value));
    }
    if let Ok(value) = std::env::var("JIANYING_DRAFTS_DIR") {
        candidates.push(PathBuf::from(value));
    }
    if let Some(local_data) = dirs::data_local_dir() {
        candidates.push(
            local_data
                .join("JianyingPro")
                .join("User Data")
                .join("Projects")
                .join("com.lveditor.draft"),
        );
    }
    candidates.push(PathBuf::from(r"D:\jianying\JianyingPro Drafts"));

    candidates
        .into_iter()
        .find(|path| path.is_dir())
        .map(|path| path.display().to_string())
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![get_environment_info, install_draft])
        .setup(|app| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.set_title("jy-downloader");
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running jy-downloader");
}
