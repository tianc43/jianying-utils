"""视频片段工具 — 添加视频/图片片段、批量添加、片段级效果

适用于 Dify 工作流的代码节点。
"""

from typing import Optional, Dict, Any, List, Union

from pyJianYingDraft import (
    VideoSegment, VideoMaterial, Timerange, ClipSettings,
    FilterType, MaskType, TransitionType,
    VideoSceneEffectType, VideoCharacterEffectType
)
from pyJianYingDraft.metadata.mix_mode_meta import MixModeType

from . import _context
from .time_tool import TimeTool


class VideoTool:
    """视频/图片片段工具类"""

    @staticmethod
    def add_video(folder_path: str, draft_name: str,
                  video_path: str, start: Union[str, int],
                  duration: Optional[Union[str, int]] = None,
                  speed: float = 1.0, volume: float = 1.0,
                  change_pitch: bool = False,
                  clip_settings: Optional[Dict[str, Any]] = None,
                  track_name: Optional[str] = None,
                  source_timerange_start: Optional[Union[str, int]] = None,
                  source_timerange_duration: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """添加单个视频/图片片段到轨道

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            video_path: 视频/图片文件路径
            start: 片段在轨道上的起始时间（微秒或时间字符串如 "5s"）
            duration: 片段持续时间（微秒或时间字符串），不指定则自动根据素材计算
            speed: 播放速度，默认1.0
            volume: 音量，默认1.0
            change_pitch: 是否跟随变速改变音调，默认False
            clip_settings: 图像调节设置字典，可选键: alpha, flip_horizontal, flip_vertical,
                           rotation, scale_x, scale_y, transform_x, transform_y
            track_name: 目标轨道名称，当只有一条视频轨道时可省略
            source_timerange_start: 素材截取起始时间
            source_timerange_duration: 素材截取持续时间

        Returns:
            dict: {"success": bool, "segment_id": str}
        """
        try:
            script = _context.load_script(folder_path, draft_name)

            # 解析时间
            start_us = _context_parse_time(start)
            duration_us = _context_parse_time(duration) if duration is not None else None

            # 创建素材
            material = VideoMaterial(video_path)

            # 计算目标时间范围
            if duration_us is None:
                if speed != 1.0:
                    duration_us = round(material.duration / speed)
                else:
                    duration_us = material.duration
            target_tr = Timerange(start_us, duration_us)

            # 素材截取范围
            source_tr = None
            if source_timerange_start is not None or source_timerange_duration is not None:
                src_start = _context_parse_time(source_timerange_start) if source_timerange_start else 0
                src_dur = _context_parse_time(source_timerange_duration) if source_timerange_duration else material.duration
                source_tr = Timerange(src_start, src_dur)

            # 图像调节
            cs = _context.parse_clip_settings(clip_settings)

            # 创建片段
            segment = VideoSegment(
                material, target_tr,
                source_timerange=source_tr,
                speed=speed if source_tr is None else None,
                volume=volume,
                change_pitch=change_pitch,
                clip_settings=cs
            )

            script.add_segment(segment, track_name)
            _context.save_script(script)

            return _context.make_result(
                True,
                f"视频片段已添加: {material.material_name}",
                segment_id=segment.segment_id,
                material_name=material.material_name,
                duration=segment.target_timerange.duration
            )
        except Exception as e:
            return _context.make_result(False, f"添加视频失败: {e}")

    @staticmethod
    def add_videos_batch(folder_path: str, draft_name: str,
                         video_infos: List[Dict[str, Any]],
                         track_name: Optional[str] = None) -> Dict[str, Any]:
        """批量添加视频/图片片段

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            video_infos: 视频信息列表，每项包含:
                - video_path (str): 视频文件路径（必须）
                - start (int): 起始时间微秒（必须）
                - end (int): 结束时间微秒（必须）
                - speed (float): 播放速度，默认1.0
                - volume (float): 音量，默认1.0
                - alpha (float): 透明度 0~1，默认1.0
                - transform_x (float): X位移
                - transform_y (float): Y位移
                - scale_x (float): X缩放
                - scale_y (float): Y缩放
            track_name: 目标轨道名称

        Returns:
            dict: {"success": bool, "segment_ids": list[str], "count": int}
        """
        try:
            script = _context.load_script(folder_path, draft_name)
            segment_ids = []

            for info in video_infos:
                video_path = info["video_path"]
                start = info["start"]
                end = info["end"]
                duration = end - start

                speed = info.get("speed", 1.0)
                volume = info.get("volume", 1.0)

                cs_dict = {}
                if "alpha" in info:
                    cs_dict["alpha"] = info["alpha"]
                if "transform_x" in info:
                    cs_dict["transform_x"] = info["transform_x"]
                if "transform_y" in info:
                    cs_dict["transform_y"] = info["transform_y"]
                if "scale_x" in info:
                    cs_dict["scale_x"] = info["scale_x"]
                if "scale_y" in info:
                    cs_dict["scale_y"] = info["scale_y"]

                cs = ClipSettings(**cs_dict) if cs_dict else None

                material = VideoMaterial(video_path)
                target_tr = Timerange(start, duration)
                segment = VideoSegment(material, target_tr, speed=speed, volume=volume, clip_settings=cs)
                script.add_segment(segment, track_name)
                segment_ids.append(segment.segment_id)

            _context.save_script(script)

            return _context.make_result(
                True,
                f"批量添加了 {len(segment_ids)} 个视频片段",
                segment_ids=segment_ids,
                count=len(segment_ids)
            )
        except Exception as e:
            return _context.make_result(False, f"批量添加视频失败: {e}")


# ---------------------------------------------------------------------------
# 内部辅助
# ---------------------------------------------------------------------------

def _context_parse_time(value):
    """解析时间值"""
    if value is None:
        return None
    from pyJianYingDraft import tim
    if isinstance(value, str):
        return tim(value)
    return int(round(value))
