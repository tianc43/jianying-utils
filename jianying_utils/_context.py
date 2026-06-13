"""内部上下文管理器 — ScriptFile 的加载/保存/序列化桥接层

所有工具类通过此模块与 pyjianyingdraft 的 ScriptFile 交互。

两种使用模式:
1. **会话模式** (推荐): 通过 get_script/commit_script 在同一进程中链式操作，
   避免 save/reload 开销，适合 Dify 单代码节点内完成所有操作。
2. **文件模式**: 通过 load_script/save_script 在磁盘上持久化，
   适合跨进程或跨节点的独立调用。
"""

import os
import json
from typing import Optional, Dict, Any, Tuple

from pyJianYingDraft import DraftFolder, ScriptFile


# ---------------------------------------------------------------------------
# 会话管理器 — 在同一进程中保持 ScriptFile 状态
# ---------------------------------------------------------------------------

_sessions: Dict[str, ScriptFile] = {}


def _session_key(folder_path: str, draft_name: str) -> str:
    return os.path.normpath(os.path.join(folder_path, draft_name))


def get_script(folder_path: str, draft_name: str) -> ScriptFile:
    """获取 ScriptFile: 优先从会话缓存获取，否则从磁盘加载

    用于工具类的链式调用，避免重复的 save/reload。
    """
    key = _session_key(folder_path, draft_name)
    if key in _sessions:
        return _sessions[key]
    return load_script(folder_path, draft_name)


def commit_script(script: ScriptFile, folder_path: str, draft_name: str) -> None:
    """将修改后的 ScriptFile 存入会话缓存（不写磁盘）

    搭配 get_script 使用，在所有操作完成后统一 save。
    """
    key = _session_key(folder_path, draft_name)
    _sessions[key] = script


def flush_session(folder_path: str, draft_name: str) -> str:
    """将会话中的 ScriptFile 写入磁盘并清除缓存

    Returns:
        str: 保存的文件路径
    """
    key = _session_key(folder_path, draft_name)
    script = _sessions.pop(key, None)
    if script is not None:
        script.save()
        return script.save_path
    return ""


def clear_session(folder_path: str, draft_name: str) -> None:
    """清除会话缓存（不写磁盘）"""
    key = _session_key(folder_path, draft_name)
    _sessions.pop(key, None)


# ---------------------------------------------------------------------------
# 核心加载/保存函数（文件模式）
# ---------------------------------------------------------------------------

def load_script(folder_path: str, draft_name: str) -> ScriptFile:
    """从磁盘加载草稿的 ScriptFile 对象（优先使用会话缓存）

    Args:
        folder_path: 草稿根文件夹路径
        draft_name: 草稿名称

    Returns:
        ScriptFile 对象
    """
    key = _session_key(folder_path, draft_name)
    if key in _sessions:
        return _sessions[key]

    folder = DraftFolder(folder_path)
    script = folder.load_template(draft_name)

    # 将 imported_tracks 重建为 tracks（保留可编辑性）
    _rebuild_tracks_from_imported(script)

    # 存入会话缓存
    _sessions[key] = script
    return script


def save_script(script: ScriptFile) -> str:
    """保存 ScriptFile 到磁盘，同时更新会话缓存"""
    script.save()
    # 根据 save_path 推断 (folder, draft_name) 并更新会话
    _cache_by_save_path(script)
    return script.save_path


def _cache_by_save_path(script: ScriptFile) -> None:
    """通过 save_path 反推 (folder_path, draft_name) 并更新会话"""
    if not script.save_path:
        return
    norm = os.path.normpath(script.save_path)
    draft_dir = os.path.dirname(norm)
    draft_name = os.path.basename(draft_dir)
    folder_path = os.path.dirname(draft_dir)
    key = _session_key(folder_path, draft_name)
    _sessions[key] = script


def _rebuild_tracks_from_imported(script: ScriptFile) -> None:
    """从 imported_tracks 重建 tracks dict，使加载的草稿轨道可编辑"""
    from pyJianYingDraft import TrackType
    from pyJianYingDraft.track import Track

    if not script.imported_tracks:
        return

    for imp_track in script.imported_tracks:
        tt = imp_track.track_type
        if tt == TrackType.adjust:
            continue
        track = Track(tt, imp_track.name, imp_track.render_index, False)
        script.tracks[imp_track.name] = track


def create_script(folder_path: str, draft_name: str,
                  width: int = 1920, height: int = 1080, fps: int = 30,
                  maintrack_adsorb: bool = True,
                  allow_replace: bool = False) -> ScriptFile:
    """创建新草稿并返回 ScriptFile 对象

    Args:
        folder_path: 草稿根文件夹路径
        draft_name: 草稿名称
        width: 视频宽度（像素）
        height: 视频高度（像素）
        fps: 帧率
        maintrack_adsorb: 是否启用主轨道吸附
        allow_replace: 是否允许覆盖同名草稿

    Returns:
        ScriptFile 对象
    """
    folder = DraftFolder(folder_path)
    script = folder.create_draft(draft_name, width, height, fps,
                                 maintrack_adsorb=maintrack_adsorb,
                                 allow_replace=allow_replace)
    # 存入会话缓存
    key = _session_key(folder_path, draft_name)
    _sessions[key] = script
    return script


def get_draft_path(folder_path: str, draft_name: str) -> str:
    """获取草稿文件夹路径

    Returns:
        草稿文件夹完整路径
    """
    return os.path.join(folder_path, draft_name)


def get_script_path(folder_path: str, draft_name: str) -> str:
    """获取 draft_content.json 的完整路径

    Returns:
        draft_content.json 文件路径
    """
    return os.path.join(folder_path, draft_name, "draft_content.json")


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def parse_clip_settings(clip_settings: Optional[Dict[str, Any]]):
    """将字典转换为 ClipSettings 对象，若为 None 则返回 None"""
    if clip_settings is None:
        return None
    from pyJianYingDraft import ClipSettings
    return ClipSettings(**clip_settings)


def parse_text_style(style: Optional[Dict[str, Any]]):
    """将字典转换为 TextStyle 对象，若为 None 则返回默认值"""
    if style is None:
        return None
    from pyJianYingDraft import TextStyle
    return TextStyle(**style)


def parse_text_border(border: Optional[Dict[str, Any]]):
    """将字典转换为 TextBorder 对象"""
    if border is None:
        return None
    from pyJianYingDraft import TextBorder
    return TextBorder(**border)


def parse_text_background(background: Optional[Dict[str, Any]]):
    """将字典转换为 TextBackground 对象"""
    if background is None:
        return None
    from pyJianYingDraft import TextBackground
    return TextBackground(**background)


def parse_text_shadow(shadow: Optional[Dict[str, Any]]):
    """将字典转换为 TextShadow 对象"""
    if shadow is None:
        return None
    from pyJianYingDraft import TextShadow
    return TextShadow(**shadow)


def hex_color_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """将十六进制颜色 (#RRGGBB 或 #RRGGBBAA) 转换为 RGB 三元组 (0~1)"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    return (r, g, b)


def make_result(success: bool, message: str = "", **kwargs) -> Dict[str, Any]:
    """构造统一的返回结果字典"""
    result = {"success": success, "message": message}
    result.update(kwargs)
    return result
