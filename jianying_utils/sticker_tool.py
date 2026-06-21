"""贴纸工具 — 添加贴纸片段

适用于 Dify 工作流的代码节点。
"""

from typing import Optional, Dict, Any, Union

from pyJianYingDraft import StickerSegment, Timerange, ClipSettings

from . import _context


class StickerTool:
    """贴纸工具类"""

    @staticmethod
    def add_sticker(folder_path: str, draft_name: str,
                    resource_id: str,
                    start: Union[str, int], duration: Union[str, int],
                    transform_x: float = 0.0,
                    transform_y: float = 0.0,
                    scale_x: float = 1.0,
                    scale_y: float = 1.0,
                    alpha: float = 1.0,
                    rotation: float = 0.0,
                    track_name: Optional[str] = None) -> Dict[str, Any]:
        """添加贴纸片段

        贴纸的 resource_id 可通过 TemplateTool.inspect_material 从模板草稿中获取。

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            resource_id: 贴纸 resource_id
            start: 起始时间（微秒或时间字符串）
            duration: 持续时间（微秒或时间字符串）
            transform_x: X位移（半画布宽为单位）
            transform_y: Y位移（半画布高为单位）
            scale_x: X缩放
            scale_y: Y缩放
            alpha: 不透明度 0~1
            rotation: 旋转角度
            track_name: 目标轨道名称

        Returns:
            dict: {"success": bool, "segment_id": str}
        """
        try:
            script = _context.load_script(folder_path, draft_name)

            start_us = _parse_time(start)
            dur_us = _parse_time(duration)
            tr = Timerange(start_us, dur_us)

            cs = ClipSettings(
                transform_x=transform_x,
                transform_y=transform_y,
                scale_x=scale_x,
                scale_y=scale_y,
                alpha=alpha,
                rotation=rotation
            )

            segment = StickerSegment(resource_id, tr, clip_settings=cs)
            script.add_segment(segment, track_name)
            _context.save_script(script)

            return _context.make_result(
                True,
                f"贴纸已添加",
                segment_id=segment.segment_id
            )
        except Exception as e:
            return _context.make_result(False, f"添加贴纸失败: {e}")


def _parse_time(value):
    if value is None:
        return None
    from .time_tool import parse_time_value
    return parse_time_value(value)
