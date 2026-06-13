"""草稿管理工具 — 创建、加载、复制、删除、保存草稿

适用于 Dify 工作流的代码节点。
"""

import os
from typing import Optional, Dict, Any, List

from . import _context


class DraftManager:
    """草稿文件夹管理工具类"""

    @staticmethod
    def create_draft(folder_path: str, draft_name: str,
                     width: int = 1920, height: int = 1080, fps: int = 30,
                     maintrack_adsorb: bool = True,
                     allow_replace: bool = False) -> Dict[str, Any]:
        """创建新草稿

        Args:
            folder_path: 草稿根文件夹路径（如剪映草稿目录）
            draft_name: 草稿名称（即文件夹名）
            width: 视频宽度（像素），默认1920
            height: 视频高度（像素），默认1080
            fps: 帧率，默认30
            maintrack_adsorb: 是否启用主轨道吸附（主轨磁吸），默认True
            allow_replace: 是否允许覆盖同名草稿，默认False

        Returns:
            dict: {"success": bool, "draft_folder": str, "draft_name": str, "script_path": str}
        """
        try:
            script = _context.create_script(
                folder_path, draft_name, width, height, fps,
                maintrack_adsorb=maintrack_adsorb,
                allow_replace=allow_replace
            )
            script.save()
            return _context.make_result(
                True,
                f"草稿 '{draft_name}' 创建成功",
                draft_folder=_context.get_draft_path(folder_path, draft_name),
                draft_name=draft_name,
                script_path=script.save_path
            )
        except Exception as e:
            return _context.make_result(False, f"创建草稿失败: {e}")

    @staticmethod
    def load_draft(folder_path: str, draft_name: str) -> Dict[str, Any]:
        """加载已有草稿

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称

        Returns:
            dict: {"success": bool, "draft_folder": str, "draft_name": str, "script_path": str}
        """
        try:
            script = _context.load_script(folder_path, draft_name)
            return _context.make_result(
                True,
                f"草稿 '{draft_name}' 加载成功",
                draft_folder=_context.get_draft_path(folder_path, draft_name),
                draft_name=draft_name,
                script_path=script.save_path,
                duration=script.duration,
                width=script.width,
                height=script.height,
                fps=script.fps
            )
        except Exception as e:
            return _context.make_result(False, f"加载草稿失败: {e}")

    @staticmethod
    def duplicate_draft(folder_path: str, template_name: str,
                        new_draft_name: str,
                        allow_replace: bool = False) -> Dict[str, Any]:
        """复制草稿为新草稿并准备编辑

        Args:
            folder_path: 草稿根文件夹路径
            template_name: 原始草稿名称
            new_draft_name: 新草稿名称
            allow_replace: 是否允许覆盖同名草稿

        Returns:
            dict: {"success": bool, "draft_folder": str, "draft_name": str}
        """
        try:
            folder_obj = __import__("pyjianyingdraft", fromlist=["DraftFolder"]).DraftFolder(folder_path)
            script = folder_obj.duplicate_as_template(template_name, new_draft_name, allow_replace)
            return _context.make_result(
                True,
                f"草稿 '{template_name}' 已复制为 '{new_draft_name}'",
                draft_folder=_context.get_draft_path(folder_path, new_draft_name),
                draft_name=new_draft_name,
                script_path=script.save_path
            )
        except Exception as e:
            return _context.make_result(False, f"复制草稿失败: {e}")

    @staticmethod
    def list_drafts(folder_path: str) -> Dict[str, Any]:
        """列出草稿文件夹中所有草稿

        Args:
            folder_path: 草稿根文件夹路径

        Returns:
            dict: {"success": bool, "drafts": list[str]}
        """
        try:
            folder_obj = __import__("pyjianyingdraft", fromlist=["DraftFolder"]).DraftFolder(folder_path)
            drafts = folder_obj.list_drafts()
            return _context.make_result(True, f"共找到 {len(drafts)} 个草稿", drafts=drafts)
        except Exception as e:
            return _context.make_result(False, f"列出草稿失败: {e}")

    @staticmethod
    def remove_draft(folder_path: str, draft_name: str) -> Dict[str, Any]:
        """删除指定草稿

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称

        Returns:
            dict: {"success": bool}
        """
        try:
            folder_obj = __import__("pyjianyingdraft", fromlist=["DraftFolder"]).DraftFolder(folder_path)
            folder_obj.remove(draft_name)
            return _context.make_result(True, f"草稿 '{draft_name}' 已删除")
        except Exception as e:
            return _context.make_result(False, f"删除草稿失败: {e}")

    @staticmethod
    def save_draft(folder_path: str, draft_name: str) -> Dict[str, Any]:
        """保存草稿到磁盘

        Args:
            folder_path: 草稿根文件夹路径
            draft_name: 草稿名称

        Returns:
            dict: {"success": bool, "script_path": str}
        """
        try:
            script = _context.load_script(folder_path, draft_name)
            path = _context.save_script(script)
            return _context.make_result(True, "草稿已保存", script_path=path)
        except Exception as e:
            return _context.make_result(False, f"保存草稿失败: {e}")
