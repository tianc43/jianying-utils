"""动画工具 — 视频/文本的入场、出场、组合/循环动画

适用于 Dify 工作流的代码节点。
"""

from typing import Optional, Dict, Any, Union
from uuid import uuid4

from pyJianYingDraft import (
    IntroType, OutroType, GroupAnimationType,
    TextIntro, TextOutro, TextLoopAnim
)

from pyJianYingDraft.animation import SegmentAnimations, VideoAnimation, Text_animation

from . import _context


class AnimationTool:
    """动画工具类"""

    # -------------------------------------------------------------------
    # 视频动画
    # -------------------------------------------------------------------

    @staticmethod
    def add_video_intro(folder_path: str, draft_name: str,
                        segment_id: str,
                        animation_name: str,
                        duration: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """为视频片段添加入场动画

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            segment_id: 片段ID
            animation_name: 动画名称（通过 MetadataQuery.list_video_intros 获取）
            duration: 动画持续时间（微秒或时间字符串），不指定则使用默认值

        Returns:
            dict: {"success": bool}
        """
        try:
            try:
                anim_type = IntroType.from_name(animation_name)
            except ValueError:
                return _context.make_result(False, f"未找到入场动画 '{animation_name}'")

            return _add_video_animation(folder_path, draft_name, segment_id, anim_type, duration)
        except Exception as e:
            return _context.make_result(False, f"添加入场动画失败: {e}")

    @staticmethod
    def add_video_outro(folder_path: str, draft_name: str,
                        segment_id: str,
                        animation_name: str,
                        duration: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """为视频片段添加出场动画

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            segment_id: 片段ID
            animation_name: 动画名称（通过 MetadataQuery.list_video_outros 获取）
            duration: 动画持续时间

        Returns:
            dict: {"success": bool}
        """
        try:
            try:
                anim_type = OutroType.from_name(animation_name)
            except ValueError:
                return _context.make_result(False, f"未找到出场动画 '{animation_name}'")

            return _add_video_animation(folder_path, draft_name, segment_id, anim_type, duration)
        except Exception as e:
            return _context.make_result(False, f"添加出场动画失败: {e}")

    @staticmethod
    def add_video_group_animation(folder_path: str, draft_name: str,
                                  segment_id: str,
                                  animation_name: str,
                                  duration: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """为视频片段添加组合动画

        注意: 组合动画不能与入场/出场动画同时使用。

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            segment_id: 片段ID
            animation_name: 动画名称（通过 MetadataQuery.list_video_group_animations 获取）
            duration: 动画持续时间

        Returns:
            dict: {"success": bool}
        """
        try:
            try:
                anim_type = GroupAnimationType.from_name(animation_name)
            except ValueError:
                return _context.make_result(False, f"未找到组合动画 '{animation_name}'")

            return _add_video_animation(folder_path, draft_name, segment_id, anim_type, duration)
        except Exception as e:
            return _context.make_result(False, f"添加组合动画失败: {e}")

    # -------------------------------------------------------------------
    # 文本动画
    # -------------------------------------------------------------------

    @staticmethod
    def add_text_intro(folder_path: str, draft_name: str,
                       segment_id: str,
                       animation_name: str,
                       duration: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """为文本片段添加入场动画

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            segment_id: 片段ID
            animation_name: 动画名称（通过 MetadataQuery.list_text_intros 获取）
            duration: 动画持续时间

        Returns:
            dict: {"success": bool}
        """
        try:
            try:
                anim_type = TextIntro.from_name(animation_name)
            except ValueError:
                return _context.make_result(False, f"未找到文本入场动画 '{animation_name}'")

            return _add_text_animation(folder_path, draft_name, segment_id, anim_type, duration)
        except Exception as e:
            return _context.make_result(False, f"添加文本入场动画失败: {e}")

    @staticmethod
    def add_text_outro(folder_path: str, draft_name: str,
                       segment_id: str,
                       animation_name: str,
                       duration: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """为文本片段添加出场动画

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            segment_id: 片段ID
            animation_name: 动画名称（通过 MetadataQuery.list_text_outros 获取）
            duration: 动画持续时间

        Returns:
            dict: {"success": bool}
        """
        try:
            try:
                anim_type = TextOutro.from_name(animation_name)
            except ValueError:
                return _context.make_result(False, f"未找到文本出场动画 '{animation_name}'")

            return _add_text_animation(folder_path, draft_name, segment_id, anim_type, duration)
        except Exception as e:
            return _context.make_result(False, f"添加文本出场动画失败: {e}")

    @staticmethod
    def add_text_loop(folder_path: str, draft_name: str,
                      segment_id: str,
                      animation_name: str) -> Dict[str, Any]:
        """为文本片段添加循环动画

        注意: 如需同时使用循环动画和入出场动画，请先添加入出场动画再添加循环动画。

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            segment_id: 片段ID
            animation_name: 动画名称（通过 MetadataQuery.list_text_loop_anims 获取）

        Returns:
            dict: {"success": bool}
        """
        try:
            try:
                anim_type = TextLoopAnim.from_name(animation_name)
            except ValueError:
                return _context.make_result(False, f"未找到文本循环动画 '{animation_name}'")

            return _add_text_animation(folder_path, draft_name, segment_id, anim_type, None)
        except Exception as e:
            return _context.make_result(False, f"添加文本循环动画失败: {e}")


# ---------------------------------------------------------------------------
# 内部辅助
# ---------------------------------------------------------------------------

def _parse_time(value):
    if value is None:
        return None
    from .time_tool import parse_time_value
    return parse_time_value(value)


def _find_segment(script, segment_id):
    """在可编辑轨道和导入轨道中查找指定 ID 的片段"""
    # 先搜索可编辑轨道
    for track in script.tracks.values():
        for seg in track.segments:
            if seg.segment_id == segment_id:
                return seg
    # 再搜索导入轨道（跨进程/缓存 miss 时片段仅存在于 imported_tracks）
    for imp_track in script.imported_tracks:
        for seg_data in imp_track.raw_data.get("segments", []):
            if seg_data.get("id") == segment_id:
                # imported_tracks 中的片段是原始 dict，无法直接编辑
                # 返回 None 表示找到了但不可编辑
                return None
    return None


def _add_video_animation(folder_path, draft_name, segment_id, anim_type, duration):
    script = _context.load_script(folder_path, draft_name)
    segment = _find_segment(script, segment_id)
    if segment is None:
        if _add_imported_animation(script, segment_id, anim_type, duration, is_text=False):
            _context.save_script(script)
            return _context.make_result(True, f"视频动画 ({type(anim_type).__name__}) 已添加")
        return _context.make_result(False, f"未找到片段 {segment_id}")

    dur = _parse_time(duration) if duration is not None else None
    segment.add_animation(anim_type, dur)

    # 修复: add_animation 将动画 ID 写入 extra_material_refs，
    # 但动画素材对象不会自动添加到 materials.animations，
    # 需在此显式补全，否则产生悬空引用导致剪映无法打开草稿。
    if (segment.animations_instance is not None
            and segment.animations_instance not in script.materials):
        script.materials.animations.append(segment.animations_instance)

    _context.save_script(script)

    type_name = type(anim_type).__name__
    return _context.make_result(True, f"视频动画 ({type_name}) 已添加")


def _add_text_animation(folder_path, draft_name, segment_id, anim_type, duration):
    script = _context.load_script(folder_path, draft_name)
    segment = _find_segment(script, segment_id)
    if segment is None:
        if _add_imported_animation(script, segment_id, anim_type, duration, is_text=True):
            _context.save_script(script)
            return _context.make_result(True, f"文本动画 ({type(anim_type).__name__}) 已添加")
        return _context.make_result(False, f"未找到片段 {segment_id}")

    dur = _parse_time(duration) if duration is not None else None
    segment.add_animation(anim_type, dur)

    # 修复: 同视频动画，显式补全动画素材到 materials.animations
    if (segment.animations_instance is not None
            and segment.animations_instance not in script.materials):
        script.materials.animations.append(segment.animations_instance)

    _context.save_script(script)

    type_name = type(anim_type).__name__
    return _context.make_result(True, f"文本动画 ({type_name}) 已添加")


def _add_imported_animation(script, segment_id, anim_type, duration, is_text: bool) -> bool:
    """Attach animation to an already-saved/imported segment raw dict."""
    seg_data = None
    seg_obj = None
    for imp_track in script.imported_tracks:
        for index, item in enumerate(imp_track.raw_data.get("segments", [])):
            if item.get("id") == segment_id:
                seg_data = item
                if hasattr(imp_track, "segments") and index < len(imp_track.segments):
                    seg_obj = imp_track.segments[index]
                break
        if seg_data is not None:
            break
    if seg_data is None:
        return False

    target_duration = int((seg_data.get("target_timerange") or {}).get("duration") or 0)
    dur = _parse_time(duration) if duration is not None else None
    animation = _make_animation(anim_type, dur, target_duration, is_text)
    animation_id = uuid4().hex
    anim_block = {
        "id": animation_id,
        "type": "sticker_animation",
        "multi_language_current": "none",
        "animations": [animation.export_json()],
    }

    refs = seg_data.setdefault("extra_material_refs", [])
    if animation_id not in refs:
        refs.append(animation_id)
    if seg_obj is not None:
        seg_obj.raw_data = seg_data

    existing = script.imported_materials.setdefault("material_animations", [])
    existing[:] = [item for item in existing if item.get("id") != animation_id]
    existing.append(anim_block)
    return True


def _make_animation(anim_type, duration, target_duration: int, is_text: bool):
    if is_text:
        duration = duration if duration is not None else anim_type.value.duration
        duration = min(duration, target_duration) if target_duration else duration
        if isinstance(anim_type, TextIntro):
            start = 0
        elif isinstance(anim_type, TextOutro):
            start = max(0, target_duration - duration)
        elif isinstance(anim_type, TextLoopAnim):
            start = 0
            duration = target_duration or duration
        else:
            raise TypeError(f"Invalid text animation type {type(anim_type)}")
        return Text_animation(anim_type, start, duration)

    if isinstance(anim_type, IntroType):
        start = 0
        duration = duration or anim_type.value.duration
    elif isinstance(anim_type, OutroType):
        duration = duration or anim_type.value.duration
        start = max(0, target_duration - duration)
    elif isinstance(anim_type, GroupAnimationType):
        start = 0
        duration = duration or target_duration
    else:
        raise TypeError(f"Invalid video animation type {type(anim_type)}")
    return VideoAnimation(anim_type, start, duration)
