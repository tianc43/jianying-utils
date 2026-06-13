"""导出工具 — 序列化草稿为 JSON

适用于 Dify 工作流的代码节点。
"""

import json
from typing import Dict, Any

from . import _context


class ExportTool:
    """草稿导出/序列化工具类"""

    @staticmethod
    def dump_to_file(folder_path: str, draft_name: str,
                     output_path: str) -> Dict[str, Any]:
        """将草稿导出为 JSON 文件

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            output_path: 输出文件路径

        Returns:
            dict: {"success": bool, "output_path": str}
        """
        try:
            script = _context.load_script(folder_path, draft_name)
            script.dump(output_path)
            return _context.make_result(True, f"草稿已导出到 {output_path}", output_path=output_path)
        except Exception as e:
            return _context.make_result(False, f"导出失败: {e}")

    @staticmethod
    def dumps_to_string(folder_path: str, draft_name: str) -> Dict[str, Any]:
        """将草稿导出为 JSON 字符串

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称

        Returns:
            dict: {"success": bool, "json_string": str, "size": int}
        """
        try:
            script = _context.load_script(folder_path, draft_name)
            json_str = script.dumps()
            return _context.make_result(
                True,
                f"草稿已序列化为 JSON（{len(json_str)} 字符）",
                json_string=json_str,
                size=len(json_str)
            )
        except Exception as e:
            return _context.make_result(False, f"序列化失败: {e}")

    @staticmethod
    def load_from_string(folder_path: str, draft_name: str,
                         json_string: str) -> Dict[str, Any]:
        """从 JSON 字符串恢复草稿内容（覆盖写入）

        注意: 此方法会覆盖草稿的 draft_content.json

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称
            json_string: JSON 字符串

        Returns:
            dict: {"success": bool}
        """
        try:
            script_path = _context.get_script_path(folder_path, draft_name)
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(json_string)
            return _context.make_result(True, "草稿已从 JSON 字符串恢复")
        except Exception as e:
            return _context.make_result(False, f"恢复草稿失败: {e}")

    @staticmethod
    def parse_draft_content(json_string: str) -> Dict[str, Any]:
        """解析 draft_content JSON 字符串为可读字典

        Args:
            json_string: draft_content 的 JSON 字符串

        Returns:
            dict: {"success": bool, "content": dict}
        """
        try:
            content = json.loads(json_string)
            return _context.make_result(True, "解析成功", content=content)
        except json.JSONDecodeError as e:
            return _context.make_result(False, f"JSON 解析失败: {e}")
