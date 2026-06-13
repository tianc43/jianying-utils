"""特效/滤镜工具 — 场景特效、人物特效、滤镜轨道、片段级效果

适用于 Dify 工作流的代码节点。
"""

from typing import Optional, Dict, Any, List, Union

from pyJianYingDraft import (
    Timerange, VideoSceneEffectType, VideoCharacterEffectType, FilterType
)

from . import _context


class EffectTool:
    """特效/滤镜工具类"""

    @staticmethod
    def add_scene_effect(folder_path: str, draft_name: str,
                         effect_name: str,
                         start: Union[str, int], duration: Union[str, int],
                         params: Optional[List[float]] = None,
                         track_name: Optional[str] = None) -> Dict[str, Any]:
        """向特效轨道添加场景特效

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            effect_name: 特效名称（通过 MetadataQuery.list_video_scene_effects 获取）
            start: 起始时间（微秒或时间字符串）
            duration: 持续时间（微秒或时间字符串）
            params: 特效参数列表 (0~100)，未提供的项使用默认值
            track_name: 特效轨道名称

        Returns:
            dict: {"success": bool}
        """
        try:
            script = _context.load_script(folder_path, draft_name)

            try:
                effect_type = VideoSceneEffectType.from_name(effect_name)
            except ValueError:
                return _context.make_result(False, f"未找到场景特效 '{effect_name}'")

            start_us = _parse_time(start)
            dur_us = _parse_time(duration)
            tr = Timerange(start_us, dur_us)

            script.add_effect(effect_type, tr, track_name, params=params)
            _context.save_script(script)

            return _context.make_result(True, f"场景特效 '{effect_name}' 已添加")
        except Exception as e:
            return _context.make_result(False, f"添加场景特效失败: {e}")

    @staticmethod
    def add_character_effect(folder_path: str, draft_name: str,
                             effect_name: str,
                             start: Union[str, int], duration: Union[str, int],
                             params: Optional[List[float]] = None,
                             track_name: Optional[str] = None) -> Dict[str, Any]:
        """向特效轨道添加人物特效

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            effect_name: 特效名称（通过 MetadataQuery.list_video_character_effects 获取）
            start: 起始时间
            duration: 持续时间
            params: 特效参数列表 (0~100)
            track_name: 特效轨道名称

        Returns:
            dict: {"success": bool}
        """
        try:
            script = _context.load_script(folder_path, draft_name)

            try:
                effect_type = VideoCharacterEffectType.from_name(effect_name)
            except ValueError:
                return _context.make_result(False, f"未找到人物特效 '{effect_name}'")

            start_us = _parse_time(start)
            dur_us = _parse_time(duration)
            tr = Timerange(start_us, dur_us)

            script.add_effect(effect_type, tr, track_name, params=params)
            _context.save_script(script)

            return _context.make_result(True, f"人物特效 '{effect_name}' 已添加")
        except Exception as e:
            return _context.make_result(False, f"添加人物特效失败: {e}")

    @staticmethod
    def add_filter_track(folder_path: str, draft_name: str,
                         filter_name: str,
                         start: Union[str, int], duration: Union[str, int],
                         intensity: float = 100.0,
                         track_name: Optional[str] = None) -> Dict[str, Any]:
        """向滤镜轨道添加滤镜

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            filter_name: 滤镜名称（通过 MetadataQuery.list_filters 获取）
            start: 起始时间
            duration: 持续时间
            intensity: 滤镜强度 0~100，默认100
            track_name: 滤镜轨道名称

        Returns:
            dict: {"success": bool}
        """
        try:
            script = _context.load_script(folder_path, draft_name)

            try:
                filter_type = FilterType.from_name(filter_name)
            except ValueError:
                return _context.make_result(False, f"未找到滤镜 '{filter_name}'")

            start_us = _parse_time(start)
            dur_us = _parse_time(duration)
            tr = Timerange(start_us, dur_us)

            script.add_filter(filter_type, tr, track_name, intensity=intensity)
            _context.save_script(script)

            return _context.make_result(True, f"滤镜 '{filter_name}' 已添加，强度 {intensity}")
        except Exception as e:
            return _context.make_result(False, f"添加滤镜失败: {e}")

    @staticmethod
    def add_effects_batch(folder_path: str, draft_name: str,
                          effect_infos: List[Dict[str, Any]],
                          track_name: Optional[str] = None) -> Dict[str, Any]:
        """批量添加特效

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            effect_infos: 特效信息列表，每项:
                - effect_title (str): 特效名称（必须）
                - start (int): 起始时间微秒（必须）
                - end (int): 结束时间微秒（必须）
                - params (list[float]): 参数列表，可选
                - type (str): "scene" 或 "character"，默认 "scene"
            track_name: 特效轨道名称

        Returns:
            dict: {"success": bool, "count": int}
        """
        try:
            script = _context.load_script(folder_path, draft_name)
            count = 0

            for info in effect_infos:
                effect_name = info["effect_title"]
                start = info["start"]
                end = info["end"]
                duration = end - start
                params = info.get("params", None)
                effect_type_str = info.get("type", "scene")

                tr = Timerange(start, duration)

                if effect_type_str == "character":
                    try:
                        et = VideoCharacterEffectType.from_name(effect_name)
                    except ValueError:
                        continue
                else:
                    try:
                        et = VideoSceneEffectType.from_name(effect_name)
                    except ValueError:
                        continue

                script.add_effect(et, tr, track_name, params=params)
                count += 1

            _context.save_script(script)

            return _context.make_result(True, f"批量添加了 {count} 个特效", count=count)
        except Exception as e:
            return _context.make_result(False, f"批量添加特效失败: {e}")


def _parse_time(value):
    if value is None:
        return None
    from pyJianYingDraft import tim
    return tim(value) if isinstance(value, str) else int(round(value))
