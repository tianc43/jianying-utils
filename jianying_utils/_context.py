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
        return save_script(script)
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

    load_template 会将 JSON 中已有的轨道/片段放入 imported_tracks。
    单次会话内缓存命中时 imported_tracks 为空，script.tracks 包含所有
    可编辑轨道。跨会话加载时 imported_tracks 包含历史片段，API 需通过
    add_track 创建同名轨道后继续添加新片段，save_script 会自动合并。

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

    # 不再调用 _rebuild_tracks_from_imported：
    # save_script 会将 script.tracks 新片段合并进 imported_tracks，
    # 仅创建空壳没有意义（历史片段仍在 imported_tracks 中）。

    # 存入会话缓存
    _sessions[key] = script
    return script


def save_script(script: ScriptFile) -> str:
    """保存 ScriptFile 到磁盘（幂等），同时更新会话缓存

    核心策略：将 script.tracks 中的新片段合并到 imported_tracks 中，
    然后清空 script.tracks。这样无论缓存是否命中，dumps() 都只导出
    imported_tracks，从根本上避免轨道重复。

    同时修复 pyJianYingDraft 库的两处缺陷：
    1. TextSegment speed 未加入 materials.speeds
    2. add_animation 后动画素材未加入 materials.animations（由 animation_tool 自行处理）
    """
    from uuid import uuid4
    from pyJianYingDraft import TextSegment
    from pyJianYingDraft.template_mode import (
        import_track, ImportedMediaSegment, ImportedSegment,
        ImportedMediaTrack, ImportedTextTrack, EditableTrack,
    )

    # --- 修复 1: 文本片段 speed 素材补全（库缺陷 workaround） ---
    existing_speed_ids = {s.global_id for s in script.materials.speeds}
    for track in script.tracks.values():
        for seg in track.segments:
            if isinstance(seg, TextSegment):
                sid = seg.speed.global_id
                if sid not in existing_speed_ids:
                    script.materials.speeds.append(seg.speed)
                    existing_speed_ids.add(sid)

    # --- 核心: 将 script.tracks 新片段合并到 imported_tracks ---
    for track_name, track in script.tracks.items():
        if not track.segments:
            continue  # 空轨道不参与合并

        # 导出片段 dict，并补全 ImportedTrack 构造函数要求的字段
        new_segs_json = []
        for seg in track.segments:
            seg_dict = seg.export_json()
            if "render_index" not in seg_dict:
                seg_dict["render_index"] = seg_dict.get("track_render_index", 0)
            new_segs_json.append(seg_dict)

        # 查找同名的 imported track，追加片段
        found = False
        for imp_track in script.imported_tracks:
            if imp_track.name == track_name:
                # 更新 raw_data（ImportedTrack.export_json 使用它）
                imp_track.raw_data.setdefault("segments", []).extend(new_segs_json)
                # 同时更新 self.segments（EditableTrack.export_json 会覆盖 raw_data）
                if isinstance(imp_track, ImportedMediaTrack):
                    imp_track.segments.extend(
                        ImportedMediaSegment(s) for s in new_segs_json
                    )
                elif isinstance(imp_track, ImportedTextTrack):
                    imp_track.segments.extend(
                        ImportedSegment(s) for s in new_segs_json
                    )
                found = True
                break

        if not found:
            # 新建一条 imported track（首次保存或 API 新增了全新轨道）
            raw_data = {
                "attribute": 0,
                "flag": 0,
                "id": uuid4().hex,
                "is_default_name": False,
                "name": track_name,
                "segments": new_segs_json,
                "type": track.track_type.name,
            }
            imp_track = import_track(raw_data)
            script.imported_tracks.append(imp_track)

        # 合并后清除片段（内容已迁移到 imported_tracks），
        # 轨道壳保留供后续 add_segment 使用
        track.segments.clear()

    # 已合并到 imported_tracks 的轨道：清除片段后暂移出 script.tracks
    # （避免 dumps() 合并时重复），保存后再恢复空壳供后续 API 调用使用。
    imported_names = {t.name for t in script.imported_tracks}
    saved_tracks = {}
    for name in imported_names & set(script.tracks.keys()):
        saved_tracks[name] = script.tracks.pop(name)

    # ------------------------------------------------------------------
    # 将素材文件复制到草稿文件夹内，路径改为纯文件名
    # 确保草稿文件夹自包含，剪映打开时不会"媒体丢失"
    # ------------------------------------------------------------------
    draft_dir = os.path.dirname(script.save_path)
    _relocate_media_to_draft(draft_dir, script.materials.audios, "audio")
    _relocate_media_to_draft(draft_dir, script.materials.videos, "video")
    # imported_materials 也会被 dumps() 导出
    for mat_key in ("audios", "videos"):
        for mat_dict in script.imported_materials.get(mat_key, []):
            _relocate_media_dict_to_draft(draft_dir, mat_dict)

    script.save()
    # 根据 save_path 推断 (folder, draft_name) 并更新会话
    _cache_by_save_path(script)

    # 恢复轨道空壳，供后续 add_segment 使用
    script.tracks.update(saved_tracks)

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
    """从 imported_tracks 重建 tracks dict，使加载的草稿轨道可编辑

    注意：只创建尚不存在的轨道，避免覆盖已有（含片段）的轨道。
    """
    from pyJianYingDraft import TrackType
    from pyJianYingDraft.track import Track

    if not script.imported_tracks:
        return

    for imp_track in script.imported_tracks:
        tt = imp_track.track_type
        if tt == TrackType.adjust:
            continue
        # 不覆盖已存在的同名轨道（可能已包含新添加的片段）
        if imp_track.name not in script.tracks:
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


# ---------------------------------------------------------------------------
# 素材文件路径修复 — 保存时将素材复制到草稿文件夹内
# ---------------------------------------------------------------------------


def _relocate_media_to_draft(draft_dir: str, materials, mat_type: str) -> None:
    """将 script.materials 中的素材文件复制到草稿目录，路径改为纯文件名"""
    import shutil
    for mat in materials:
        if not hasattr(mat, "path"):
            continue
        path = mat.path
        if not path or not os.path.isabs(path):
            continue
        # 已在草稿目录内则跳过
        if _path_is_within(path, draft_dir):
            continue
        dest = os.path.join(draft_dir, os.path.basename(path))
        if not os.path.exists(dest):
            try:
                shutil.copy2(path, dest)
            except Exception:
                continue  # 跳过无法复制的文件
        mat.path = os.path.basename(path)
        mat.material_name = os.path.basename(path)


def _relocate_media_dict_to_draft(draft_dir: str, mat_dict: dict) -> None:
    """将 imported_materials 中的素材路径改为纯文件名并复制文件"""
    import shutil
    path = mat_dict.get("path", "")
    if not path or not os.path.isabs(path):
        return
    if _path_is_within(path, draft_dir):
        return
    dest = os.path.join(draft_dir, os.path.basename(path))
    if not os.path.exists(dest):
        try:
            shutil.copy2(path, dest)
        except Exception:
            return
    mat_dict["path"] = os.path.basename(path)
    # 同时更新 name / material_name 字段
    if "name" in mat_dict:
        mat_dict["name"] = os.path.basename(path)
    if "material_name" in mat_dict:
        mat_dict["material_name"] = os.path.basename(path)


def _path_is_within(child: str, parent: str) -> bool:
    """安全判断 child 是否在 parent 目录下（兼容 Windows 跨盘符）"""
    try:
        return os.path.commonpath([parent, child]) == os.path.normpath(parent)
    except ValueError:
        return False  # 跨盘符（如 C: 和 D:）视为不在同一目录


def make_result(success: bool, message: str = "", **kwargs) -> Dict[str, Any]:
    """构造统一的返回结果字典"""
    result = {"success": success, "message": message}
    result.update(kwargs)
    return result
