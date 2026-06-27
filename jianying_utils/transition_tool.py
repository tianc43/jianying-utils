"""转场工具 — 为视频片段添加转场效果

适用于 Dify 工作流的代码节点。
"""

from typing import Optional, Dict, Any, List, Union

from pyJianYingDraft import TransitionType
from pyJianYingDraft.video_segment import Transition

from . import _context


class TransitionTool:
    """转场工具类

    注意: 转场应当添加在**前面的**片段上（即转场发生在该片段和下一个片段之间）。
    """

    @staticmethod
    def add_transition(folder_path: str, draft_name: str,
                       segment_id: str,
                       transition_name: str,
                       duration: Optional[Union[str, int]] = None) -> Dict[str, Any]:
        """为视频片段添加转场

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            segment_id: 片段ID（转场添加在前面的片段上）
            transition_name: 转场名称（通过 MetadataQuery.list_transitions 获取）
            duration: 转场持续时间（微秒或时间字符串），不指定则使用默认值

        Returns:
            dict: {"success": bool}
        """
        try:
            try:
                trans_type = TransitionType.from_name(transition_name)
            except ValueError:
                return _context.make_result(False, f"未找到转场 '{transition_name}'")

            script = _context.load_script(folder_path, draft_name)
            segment = _find_segment(script, segment_id)
            dur = _parse_time(duration) if duration is not None else None

            if segment is None:
                if _add_imported_transition(script, segment_id, trans_type, dur):
                    _context.save_script(script)
                    return _context.make_result(True, f"转场 '{transition_name}' 已添加")
                return _context.make_result(False, f"未找到片段 {segment_id}")

            segment.add_transition(trans_type, duration=dur)
            _context.save_script(script)

            return _context.make_result(True, f"转场 '{transition_name}' 已添加")
        except Exception as e:
            return _context.make_result(False, f"添加转场失败: {e}")

    @staticmethod
    def add_transitions_batch(folder_path: str, draft_name: str,
                              transitions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量添加转场

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            transitions: 转场列表，每项:
                - segment_id (str): 片段ID（必须）
                - transition_name (str): 转场名称（必须）
                - duration (int): 持续时间微秒（可选）

        Returns:
            dict: {"success": bool, "count": int}
        """
        try:
            script = _context.load_script(folder_path, draft_name)
            count = 0

            for t in transitions:
                seg_id = t["segment_id"]
                name = t["transition_name"]
                dur = t.get("duration")

                try:
                    trans_type = TransitionType.from_name(name)
                except ValueError:
                    continue

                dur_val = _parse_time(dur) if dur is not None else None
                segment = _find_segment(script, seg_id)
                if segment is None:
                    if _add_imported_transition(script, seg_id, trans_type, dur_val):
                        count += 1
                    continue

                segment.add_transition(trans_type, duration=dur_val)
                count += 1

            _context.save_script(script)

            return _context.make_result(True, f"批量添加了 {count} 个转场", count=count)
        except Exception as e:
            return _context.make_result(False, f"批量添加转场失败: {e}")


def _parse_time(value):
    if value is None:
        return None
    from .time_tool import parse_time_value
    return parse_time_value(value)


def _find_segment(script, segment_id):
    """在可编辑轨道和导入轨道中查找指定 ID 的片段"""
    for track in script.tracks.values():
        for seg in track.segments:
            if seg.segment_id == segment_id:
                return seg
    # 跨进程/缓存 miss 时片段仅存在于 imported_tracks
    for imp_track in script.imported_tracks:
        for seg_data in imp_track.raw_data.get("segments", []):
            if seg_data.get("id") == segment_id:
                return None  # 原始数据不可编辑
    return None


def _add_imported_transition(script, segment_id, trans_type, duration) -> bool:
    """Attach transition to an already-saved/imported video segment raw dict."""
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

    if seg_data.get("transition"):
        raise ValueError("当前片段已有转场, 不能再添加新的转场")

    transition = Transition(trans_type, duration=duration)
    transition_json = transition.export_json()
    seg_data["transition"] = transition_json
    refs = seg_data.setdefault("extra_material_refs", [])
    if transition.global_id not in refs:
        refs.append(transition.global_id)
    if seg_obj is not None:
        seg_obj.raw_data = seg_data

    script.imported_materials.setdefault("transitions", []).append(transition_json)
    return True
