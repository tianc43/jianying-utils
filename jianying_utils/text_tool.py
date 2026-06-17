"""文本/字幕工具 — 添加文本、批量字幕、SRT导入、文本样式

适用于 Dify 工作流的代码节点。
"""

from typing import Optional, Dict, Any, List, Union

from pyJianYingDraft import (
    TextSegment, TextStyle, TextBorder, TextBackground, TextShadow,
    Timerange, ClipSettings, FontType
)

from . import _context


class TextTool:
    """文本/字幕工具类"""

    @staticmethod
    def add_text(folder_path: str, draft_name: str,
                 text: str, start: Union[str, int], duration: Union[str, int],
                 font: Optional[str] = None,
                 font_size: float = 8.0,
                 text_color: str = "#FFFFFF",
                 alpha: float = 1.0,
                 bold: bool = False,
                 italic: bool = False,
                 underline: bool = False,
                 alignment: int = 0,
                 vertical: bool = False,
                 letter_spacing: int = 0,
                 line_spacing: int = 0,
                 auto_wrapping: bool = False,
                 line_max_width: float = 0.82,
                 border: Optional[Dict[str, Any]] = None,
                 background: Optional[Dict[str, Any]] = None,
                 shadow: Optional[Dict[str, Any]] = None,
                 clip_settings: Optional[Dict[str, Any]] = None,
                 track_name: Optional[str] = None) -> Dict[str, Any]:
        """添加文本片段

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            text: 文本内容
            start: 起始时间（微秒或时间字符串）
            duration: 持续时间（微秒或时间字符串）
            font: 字体名称（通过 MetadataQuery.list_fonts 获取可选值）
            font_size: 字体大小，默认8.0
            text_color: 文字颜色，十六进制格式 "#RRGGBB"，默认白色
            alpha: 文字不透明度 0~1，默认1.0
            bold: 是否加粗
            italic: 是否斜体
            underline: 是否下划线
            alignment: 对齐方式 0=左对齐, 1=居中, 2=右对齐
            vertical: 是否竖排文本
            letter_spacing: 字符间距
            line_spacing: 行间距
            auto_wrapping: 是否自动换行
            line_max_width: 最大行宽比例 0~1
            border: 描边设置字典 {"alpha": float, "color": str, "width": float}
            background: 背景设置字典 {"color": str, ...}
            shadow: 阴影设置字典 {"alpha": float, "color": str, "diffuse": float, "distance": float, "angle": float}
            clip_settings: 图像调节设置字典
            track_name: 目标轨道名称

        Returns:
            dict: {"success": bool, "segment_id": str}
        """
        try:
            script = _context.load_script(folder_path, draft_name)

            start_us = _parse_time(start)
            duration_us = _parse_time(duration)
            tr = Timerange(start_us, duration_us)

            # 字体
            font_enum = None
            if font:
                try:
                    font_enum = FontType.from_name(font)
                except ValueError:
                    return _context.make_result(False, f"未找到字体 '{font}'")

            # 颜色
            color_rgb = _hex_to_rgb(text_color)

            # 文本样式
            style = TextStyle(
                size=font_size,
                bold=bold, italic=italic, underline=underline,
                color=color_rgb, alpha=alpha,
                align=alignment, vertical=vertical,
                letter_spacing=letter_spacing, line_spacing=line_spacing,
                auto_wrapping=auto_wrapping, max_line_width=line_max_width
            )

            # 描边
            text_border = None
            if border:
                border_color = _hex_to_rgb(border.get("color", "#000000"))
                text_border = TextBorder(
                    alpha=border.get("alpha", 1.0),
                    color=border_color,
                    width=border.get("width", 40.0)
                )

            # 背景
            text_bg = None
            if background:
                text_bg = TextBackground(
                    color=background.get("color", "#000000"),
                    style=background.get("style", 1),
                    alpha=background.get("alpha", 1.0),
                    round_radius=background.get("round_radius", 0.0),
                    height=background.get("height", 0.14),
                    width=background.get("width", 0.14),
                    horizontal_offset=background.get("horizontal_offset", 0.5),
                    vertical_offset=background.get("vertical_offset", 0.5)
                )

            # 阴影
            text_shadow = None
            if shadow:
                shadow_color = _hex_to_rgb(shadow.get("color", "#000000"))
                text_shadow = TextShadow(
                    alpha=shadow.get("alpha", 1.0),
                    color=shadow_color,
                    diffuse=shadow.get("diffuse", 15.0),
                    distance=shadow.get("distance", 5.0),
                    angle=shadow.get("angle", -45.0)
                )

            cs = _context.parse_clip_settings(clip_settings)

            segment = TextSegment(
                text, tr,
                font=font_enum,
                style=style,
                clip_settings=cs,
                border=text_border,
                background=text_bg,
                shadow=text_shadow
            )

            script.add_segment(segment, track_name)
            _context.save_script(script)

            return _context.make_result(
                True,
                f"文本片段已添加",
                segment_id=segment.segment_id
            )
        except Exception as e:
            return _context.make_result(False, f"添加文本失败: {e}")

    @staticmethod
    def add_captions_batch(folder_path: str, draft_name: str,
                           captions: List[Dict[str, Any]],
                           font: Optional[str] = None,
                           font_size: float = 5.0,
                           text_color: str = "#FFFFFF",
                           alpha: float = 1.0,
                           bold: bool = False,
                           italic: bool = False,
                           underline: bool = False,
                           alignment: int = 1,
                           letter_spacing: int = 0,
                           line_spacing: int = 0,
                           line_max_width: float = 0.82,
                           auto_wrapping: bool = True,
                           border: Optional[Dict[str, Any]] = None,
                           background: Optional[Dict[str, Any]] = None,
                           shadow: Optional[Dict[str, Any]] = None,
                           clip_settings: Optional[Dict[str, Any]] = None,
                           track_name: Optional[str] = None,
                           has_shadow: bool = False) -> Dict[str, Any]:
        """批量添加字幕

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            captions: 字幕列表，每项包含:
                - text (str): 字幕文本（必须）
                - start (int): 起始时间微秒（必须）
                - end (int): 结束时间微秒（必须）
            font: 字体名称
            font_size: 字体大小，默认5.0（模仿剪映导入字幕的默认值）
            text_color: 文字颜色 "#RRGGBB"
            alpha: 不透明度 0~1
            bold/italic/underline: 文字样式开关
            alignment: 对齐方式 0=左 1=中 2=右
            letter_spacing/line_spacing: 间距
            line_max_width: 最大行宽
            auto_wrapping: 自动换行
            border: 描边设置
            background: 背景设置
            shadow: 阴影设置
            clip_settings: 图像调节设置
            track_name: 目标轨道名称
            has_shadow: 是否启用阴影（当 shadow 为 None 时使用默认阴影）

        Returns:
            dict: {"success": bool, "segment_ids": list, "count": int}
        """
        try:
            script = _context.load_script(folder_path, draft_name)

            font_enum = None
            if font:
                try:
                    font_enum = FontType.from_name(font)
                except ValueError:
                    return _context.make_result(False, f"未找到字体 '{font}'")

            color_rgb = _hex_to_rgb(text_color)

            style = TextStyle(
                size=font_size,
                bold=bold, italic=italic, underline=underline,
                color=color_rgb, alpha=alpha,
                align=alignment,
                letter_spacing=letter_spacing, line_spacing=line_spacing,
                auto_wrapping=auto_wrapping, max_line_width=line_max_width
            )

            text_border = None
            if border:
                border_color = _hex_to_rgb(border.get("color", "#000000"))
                text_border = TextBorder(
                    alpha=border.get("alpha", 1.0),
                    color=border_color,
                    width=border.get("width", 40.0)
                )

            text_bg = None
            if background:
                text_bg = TextBackground(
                    color=background.get("color", "#000000"),
                    style=background.get("style", 1),
                    alpha=background.get("alpha", 1.0),
                    round_radius=background.get("round_radius", 0.0),
                    height=background.get("height", 0.14),
                    width=background.get("width", 0.14),
                    horizontal_offset=background.get("horizontal_offset", 0.5),
                    vertical_offset=background.get("vertical_offset", 0.5)
                )

            text_shadow = None
            if shadow:
                shadow_color = _hex_to_rgb(shadow.get("color", "#000000"))
                text_shadow = TextShadow(
                    alpha=shadow.get("alpha", 1.0),
                    color=shadow_color,
                    diffuse=shadow.get("diffuse", 15.0),
                    distance=shadow.get("distance", 5.0),
                    angle=shadow.get("angle", -45.0)
                )
            elif has_shadow:
                text_shadow = TextShadow()

            # 默认字幕 clip_settings（模仿剪映导入字幕时的位置）
            if clip_settings is None:
                cs = ClipSettings(transform_y=-0.8)
            else:
                cs = _context.parse_clip_settings(clip_settings)

            segment_ids = []
            for cap in captions:
                text = cap["text"]
                start = cap["start"]
                end = cap["end"]
                duration = end - start
                tr = Timerange(start, duration)

                segment = TextSegment(
                    text, tr,
                    font=font_enum,
                    style=style,
                    clip_settings=cs,
                    border=text_border,
                    background=text_bg,
                    shadow=text_shadow
                )
                script.add_segment(segment, track_name)
                segment_ids.append(segment.segment_id)

            _context.save_script(script)

            return _context.make_result(
                True,
                f"批量添加了 {len(segment_ids)} 条字幕",
                segment_ids=segment_ids,
                count=len(segment_ids)
            )
        except Exception as e:
            return _context.make_result(False, f"批量添加字幕失败: {e}")

    @staticmethod
    def import_srt(folder_path: str, draft_name: str,
                   srt_path: str, track_name: str,
                   font: Optional[str] = None,
                   font_size: float = 5.0,
                   text_color: str = "#FFFFFF",
                   alignment: int = 1,
                   time_offset: Union[str, float] = 0.0,
                   clip_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """从 SRT 文件导入字幕

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            srt_path: SRT 文件路径
            track_name: 文本轨道名称（不存在则自动创建）
            font: 字体名称
            font_size: 字体大小
            text_color: 文字颜色
            alignment: 对齐方式
            time_offset: 字幕整体时间偏移
            clip_settings: 图像调节设置

        Returns:
            dict: {"success": bool, "count": int}
        """
        try:
            script = _context.load_script(folder_path, draft_name)

            font_enum = None
            if font:
                try:
                    font_enum = FontType.from_name(font)
                except ValueError:
                    return _context.make_result(False, f"未找到字体 '{font}'")

            color_rgb = _hex_to_rgb(text_color)

            style = TextStyle(
                size=font_size,
                color=color_rgb,
                align=alignment,
                auto_wrapping=True
            )

            if clip_settings is None:
                cs = ClipSettings(transform_y=-0.8)
            else:
                cs = _context.parse_clip_settings(clip_settings)

            script.import_srt(srt_path, track_name,
                              time_offset=time_offset,
                              text_style=style,
                              clip_settings=cs)
            _context.save_script(script)

            return _context.make_result(True, f"SRT 字幕已导入: {srt_path}")
        except Exception as e:
            return _context.make_result(False, f"导入 SRT 失败: {e}")


# ---------------------------------------------------------------------------
# 内部辅助
# ---------------------------------------------------------------------------

def _parse_time(value):
    if value is None:
        return None
    from pyJianYingDraft import tim
    return tim(value) if isinstance(value, str) else int(round(value))


def _hex_to_rgb(hex_color: str):
    """#RRGGBB → (r, g, b) 0~1"""
    h = hex_color.lstrip('#')
    return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)
