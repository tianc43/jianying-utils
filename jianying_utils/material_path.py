"""Material path resolution shared by audio/video tools."""

from __future__ import annotations

import hashlib
import os
import shutil
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOWNLOAD_DIR = os.environ.get("JIANYING_TTS_DIR", "") or os.path.join(
    os.environ.get("JIANYING_DRAFTS_DIR", os.path.dirname(__file__)), "..", "downloads"
)


def _is_url(path: str) -> bool:
    return path.startswith(("http://", "https://"))


def _safe_project_path(relative_path: str) -> Optional[str]:
    candidate = os.path.abspath(os.path.join(PROJECT_ROOT, relative_path))
    if os.path.commonpath([PROJECT_ROOT, candidate]) != PROJECT_ROOT:
        return None
    return candidate


def _resolve_static_url(source_url: str) -> Optional[str]:
    parsed = urllib.parse.urlparse(source_url)
    if not parsed.scheme or not parsed.netloc:
        return None

    deploy_url = os.environ.get("DEPLOY_URL", "")
    deploy = urllib.parse.urlparse(deploy_url) if deploy_url else None
    if deploy and deploy.netloc and parsed.netloc != deploy.netloc:
        return None

    root_path = os.environ.get("ROOT_PATH", "").rstrip("/")
    path = urllib.parse.unquote(parsed.path)
    if root_path and path.startswith(root_path + "/"):
        path = path[len(root_path):]

    if not path.startswith("/static/"):
        return None

    candidate = _safe_project_path(path[len("/static/"):])
    return candidate if candidate and os.path.isfile(candidate) else None


def _resolve_relative_path(material_path: str) -> Optional[str]:
    normalized = material_path.strip().replace("\\", "/")
    if not normalized:
        return None

    candidates = [normalized]
    if normalized.startswith("./"):
        candidates.append(normalized[2:])
    if normalized.startswith("static/"):
        candidates.append(normalized[len("static/"):])
    else:
        candidates.append(os.path.join("assets", normalized))

    drafts_dir = os.environ.get("JIANYING_DRAFTS_DIR", "")
    if drafts_dir:
        draft_candidate = os.path.abspath(os.path.join(drafts_dir, normalized))
        if os.path.isfile(draft_candidate):
            return draft_candidate

    for candidate in candidates:
        project_candidate = _safe_project_path(candidate)
        if project_candidate and os.path.isfile(project_candidate):
            return project_candidate
    return None


def _download_url(source_url: str, local_path: str, accept: str) -> None:
    parsed = urllib.parse.urlparse(source_url)
    origin = f"{parsed.scheme}://{parsed.netloc}/" if parsed.scheme and parsed.netloc else ""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": accept,
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    if origin:
        headers["Referer"] = origin

    request = urllib.request.Request(source_url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=120) as response, open(local_path, "wb") as output:
            shutil.copyfileobj(response, output)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"下载素材被拒绝: HTTP {e.code} {e.reason} ({source_url})") from e


def resolve_material_path(material_path: str, default_ext: str = ".mp3", accept: str = "*/*") -> str:
    """Resolve absolute paths, relative paths, static URLs, and remote URLs."""
    if not material_path:
        return material_path

    if _is_url(material_path):
        static_path = _resolve_static_url(material_path)
        if static_path:
            return static_path

        url_hash = hashlib.md5(material_path.encode()).hexdigest()[:12]
        ext = os.path.splitext(urllib.parse.urlparse(material_path).path)[1] or default_ext
        local_path = os.path.join(DOWNLOAD_DIR, f"dl_{url_hash}{ext}")
        if os.path.isfile(local_path):
            return local_path

        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        _download_url(material_path, local_path, accept)
        return local_path

    if os.path.isabs(material_path):
        return material_path

    relative_path = _resolve_relative_path(material_path)
    return relative_path or material_path
