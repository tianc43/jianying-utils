"""动画工具 — 视频/文本的入场、出场、组合/循环动画

适用于 Dify 工作流的代码节点。
"""

from typing import Optional, Dict, Any, Union

from pyJianYingDraft import (
    IntroType, OutroType, GroupAnimationType,
    TextIntro, TextOutro, TextLoopAnim
)

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
    from pyJianYingDraft import tim
    return tim(value) if isinstance(value, str) else int(round(value))


def _find_segment(script, segment_id):
    for track in script.tracks.values():
        for seg in track.segments:
            if seg.segment_id == segment_id:
                return seg
    return None


def _add_video_animation(folder_path, draft_name, segment_id, anim_type, duration):
    script = _context.load_script(folder_path, draft_name)
    segment = _find_segment(script, segment_id)
    if segment is None:
        return _context.make_result(False, f"未找到片段 {segment_id}")

    dur = _parse_time(duration) if duration is not None else None
    segment.add_animation(anim_type, dur)
    _context.save_script(script)

    type_name = type(anim_type).__name__
    return _context.make_result(True, f"视频动画 ({type_name}) 已添加")


def _add_text_animation(folder_path, draft_name, segment_id, anim_type, duration):
    script = _context.load_script(folder_path, draft_name)
    segment = _find_segment(script, segment_id)
    if segment is None:
        return _context.make_result(False, f"未找到片段 {segment_id}")

    dur = _parse_time(duration) if duration is not None else None
    segment.add_animation(anim_type, dur)
    _context.save_script(script)

    type_name = type(anim_type).__name__
    return _context.make_result(True, f"文本动画 ({type_name}) 已添加")
