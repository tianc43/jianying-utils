"""轨道管理工具 — 添加、列出轨道

适用于 Dify 工作流的代码节点。
"""

from typing import Optional, Dict, Any, List

from pyJianYingDraft import TrackType

from . import _context


# 轨道类型字符串到枚举的映射
_TRACK_TYPE_MAP = {
    "video": TrackType.video,
    "audio": TrackType.audio,
    "text": TrackType.text,
    "effect": TrackType.effect,
    "filter": TrackType.filter,
    "sticker": TrackType.sticker,
}


class TrackManager:
    """轨道管理工具类"""

    @staticmethod
    def add_track(folder_path: str, draft_name: str,
                  track_type: str, track_name: Optional[str] = None,
                  mute: bool = False, relative_index: int = 0,
                  absolute_index: Optional[int] = None) -> Dict[str, Any]:
        """向草稿中添加轨道

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            track_type: 轨道类型字符串，可选: "video", "audio", "text", "effect", "filter", "sticker"
            track_name: 轨道名称，仅在创建第一个同类型轨道时可省略
            mute: 是否静音，默认False
            relative_index: 相对图层位置（越高越前景），默认0
            absolute_index: 绝对图层位置（直接覆盖 render_index），不与 relative_index 同时使用

        Returns:
            dict: {"success": bool, "track_name": str}
        """
        try:
            if track_type not in _TRACK_TYPE_MAP:
                return _context.make_result(
                    False,
                    f"不支持的轨道类型 '{track_type}'，可选: {list(_TRACK_TYPE_MAP.keys())}"
                )

            script = _context.load_script(folder_path, draft_name)
            tt = _TRACK_TYPE_MAP[track_type]
            script.add_track(tt, track_name, mute=mute,
                             relative_index=relative_index,
                             absolute_index=absolute_index)
            _context.save_script(script)

            actual_name = track_name or tt.name
            return _context.make_result(True, f"轨道 '{actual_name}' 已添加", track_name=actual_name)
        except Exception as e:
            return _context.make_result(False, f"添加轨道失败: {e}")

    @staticmethod
    def list_tracks(folder_path: str, draft_name: str) -> Dict[str, Any]:
        """列出草稿中所有轨道信息

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称

        Returns:
            dict: {"success": bool, "tracks": list[dict]}
        """
        try:
            script = _context.load_script(folder_path, draft_name)
            tracks_info = []
            for name, track in script.tracks.items():
                tracks_info.append({
                    "name": name,
                    "type": track.track_type.name,
                    "render_index": track.render_index,
                    "mute": track.mute,
                    "segment_count": len(track.segments)
                })

            # 也列出导入的轨道（模板模式）
            for track in script.imported_tracks:
                tracks_info.append({
                    "name": track.name,
                    "type": track.track_type.name,
                    "render_index": track.render_index,
                    "source": "imported",
                    "segment_count": len(getattr(track, 'segments', []))
                })

            return _context.make_result(True, f"共 {len(tracks_info)} 条轨道", tracks=tracks_info)
        except Exception as e:
            return _context.make_result(False, f"列出轨道失败: {e}")
