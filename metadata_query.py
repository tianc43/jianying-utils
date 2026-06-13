"""元数据查询工具 — 查询剪映内置的转场、滤镜、字体、动画、特效等枚举

适用于 Dify 工作流的代码节点。
mode: 0=全部, 1=仅VIP, 2=仅免费
"""

from typing import Dict, Any, List

from pyJianYingDraft import (
    TransitionType, FilterType, FontType, MaskType,
    IntroType, OutroType, GroupAnimationType,
    TextIntro, TextOutro, TextLoopAnim,
    AudioSceneEffectType,
    VideoSceneEffectType, VideoCharacterEffectType
)
from pyJianYingDraft.metadata.mix_mode_meta import MixModeType

from . import _context


class MetadataQuery:
    """元数据查询工具类

    用于查询 pyjianyingdraft 内置的各种枚举值（转场、滤镜、字体等）。
    返回的信息可用于 Dify 工作流中的参数选择。
    """

    @staticmethod
    def list_transitions(mode: int = 0) -> Dict[str, Any]:
        """查询转场列表

        Args:
            mode: 0=全部, 1=仅VIP, 2=仅免费

        Returns:
            dict: {"success": bool, "items": list[dict], "count": int}
        """
        return _list_effect_enum(TransitionType, mode, "transition")

    @staticmethod
    def list_filters(mode: int = 0) -> Dict[str, Any]:
        """查询滤镜列表

        Args:
            mode: 0=全部, 1=仅VIP, 2=仅免费

        Returns:
            dict: {"success": bool, "items": list[dict], "count": int}
        """
        return _list_effect_enum(FilterType, mode, "filter")

    @staticmethod
    def list_fonts(mode: int = 0) -> Dict[str, Any]:
        """查询字体列表

        Args:
            mode: 0=全部, 1=仅VIP, 2=仅免费

        Returns:
            dict: {"success": bool, "items": list[dict], "count": int}
        """
        return _list_effect_enum(FontType, mode, "font")

    @staticmethod
    def list_masks() -> Dict[str, Any]:
        """查询蒙版列表

        Returns:
            dict: {"success": bool, "items": list[dict], "count": int}
        """
        items = []
        for member in MaskType:
            meta = member.value
            items.append({
                "name": member.name,
                "display_name": meta.name,
                "resource_id": meta.resource_id,
            })
        return _context.make_result(True, f"共 {len(items)} 种蒙版", items=items, count=len(items))

    @staticmethod
    def list_video_intros(mode: int = 0) -> Dict[str, Any]:
        """查询视频入场动画列表"""
        return _list_animation_enum(IntroType, mode, "video_intro")

    @staticmethod
    def list_video_outros(mode: int = 0) -> Dict[str, Any]:
        """查询视频出场动画列表"""
        return _list_animation_enum(OutroType, mode, "video_outro")

    @staticmethod
    def list_video_group_animations(mode: int = 0) -> Dict[str, Any]:
        """查询视频组合动画列表"""
        return _list_animation_enum(GroupAnimationType, mode, "video_group_animation")

    @staticmethod
    def list_text_intros(mode: int = 0) -> Dict[str, Any]:
        """查询文本入场动画列表"""
        return _list_animation_enum(TextIntro, mode, "text_intro")

    @staticmethod
    def list_text_outros(mode: int = 0) -> Dict[str, Any]:
        """查询文本出场动画列表"""
        return _list_animation_enum(TextOutro, mode, "text_outro")

    @staticmethod
    def list_text_loop_anims(mode: int = 0) -> Dict[str, Any]:
        """查询文本循环动画列表"""
        return _list_animation_enum(TextLoopAnim, mode, "text_loop")

    @staticmethod
    def list_video_scene_effects(mode: int = 0) -> Dict[str, Any]:
        """查询视频场景特效列表"""
        return _list_effect_enum(VideoSceneEffectType, mode, "video_scene_effect")

    @staticmethod
    def list_video_character_effects(mode: int = 0) -> Dict[str, Any]:
        """查询视频人物特效列表"""
        return _list_effect_enum(VideoCharacterEffectType, mode, "video_character_effect")

    @staticmethod
    def list_audio_scene_effects(mode: int = 0) -> Dict[str, Any]:
        """查询音频场景音效列表"""
        return _list_effect_enum(AudioSceneEffectType, mode, "audio_scene_effect")

    @staticmethod
    def list_mix_modes() -> Dict[str, Any]:
        """查询混合模式列表"""
        items = []
        for member in MixModeType:
            meta = member.value
            items.append({
                "name": member.name,
                "display_name": meta.name,
                "effect_id": meta.effect_id,
                "resource_id": meta.resource_id,
            })
        return _context.make_result(True, f"共 {len(items)} 种混合模式", items=items, count=len(items))


# ---------------------------------------------------------------------------
# 内部辅助函数
# ---------------------------------------------------------------------------

def _list_effect_enum(enum_class, mode: int, category: str) -> Dict[str, Any]:
    """通用的效果枚举列表查询"""
    items = []
    for member in enum_class:
        meta = member.value
        is_vip = getattr(meta, 'is_vip', False)

        # 按 mode 过滤
        if mode == 1 and not is_vip:
            continue
        if mode == 2 and is_vip:
            continue

        item = {
            "name": member.name,
            "display_name": meta.name,
            "is_vip": is_vip,
            "resource_id": meta.resource_id,
            "effect_id": meta.effect_id,
        }

        # 附加参数信息（如果有）
        if hasattr(meta, 'params') and meta.params:
            item["params"] = [
                {"name": p.name, "default": p.default_value, "min": p.min_value, "max": p.max_value}
                for p in meta.params
            ]

        items.append(item)

    return _context.make_result(True, f"共 {len(items)} 种{category}", items=items, count=len(items))


def _list_animation_enum(enum_class, mode: int, category: str) -> Dict[str, Any]:
    """通用的动画枚举列表查询"""
    items = []
    for member in enum_class:
        meta = member.value
        is_vip = getattr(meta, 'is_vip', False)

        if mode == 1 and not is_vip:
            continue
        if mode == 2 and is_vip:
            continue

        item = {
            "name": member.name,
            "display_name": meta.title if hasattr(meta, 'title') else getattr(meta, 'name', member.name),
            "is_vip": is_vip,
            "duration_us": meta.duration,
            "duration_seconds": round(meta.duration / 1_000_000, 2),
            "resource_id": meta.resource_id,
            "effect_id": meta.effect_id,
        }
        items.append(item)

    return _context.make_result(True, f"共 {len(items)} 种{category}", items=items, count=len(items))
