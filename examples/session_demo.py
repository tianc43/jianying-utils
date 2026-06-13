"""Dify 工作流示例 — 使用会话模式在同一脚本中完成所有操作

在 Dify 工作流中，推荐使用**单个代码节点**完成所有操作，
通过 _context 的会话管理器避免 save/reload 开销。

适用场景:
- AI 生成字幕 → 自动创建剪映草稿
- 批量视频合成
- 模板填充
"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pyJianYingDraft import (
    DraftFolder, TrackType,
    VideoSegment, AudioSegment, TextSegment,
    VideoMaterial, AudioMaterial,
    Timerange, ClipSettings,
    TextStyle, TextBorder, TextShadow,
    IntroType, FilterType, TransitionType,
    KeyframeProperty, tim
)


def create_video_draft(folder_path: str, draft_name: str,
                       video_path: str = None,
                       audio_path: str = None,
                       captions: list = None,
                       title_text: str = None):
    """一站式创建视频草稿

    Args:
        folder_path: 草稿根文件夹
        draft_name: 草稿名称
        video_path: 主视频路径（可选）
        audio_path: 背景音乐路径（可选）
        captions: 字幕列表 [{"text": str, "start": int, "end": int}]
        title_text: 标题文本（可选）
    """
    # 1. 创建草稿
    folder = DraftFolder(folder_path)
    script = folder.create_draft(draft_name, 1920, 1080, 30, allow_replace=True)

    # 2. 添加主视频
    if video_path and os.path.exists(video_path):
        script.add_track(TrackType.video)
        mat = VideoMaterial(video_path)
        seg = VideoSegment(mat, Timerange(0, mat.duration))
        script.add_segment(seg)
        print(f"  视频已添加: {mat.material_name} ({mat.duration/1e6:.1f}s)")

    # 3. 添加背景音乐
    if audio_path and os.path.exists(audio_path):
        script.add_track(TrackType.audio)
        mat = AudioMaterial(audio_path)
        # 只取前30秒或与视频等长
        duration = min(mat.duration, script.duration or mat.duration)
        seg = AudioSegment(mat, Timerange(0, duration), volume=0.5)
        seg.add_fade("1s", "2s")  # 1s淡入 2s淡出
        script.add_segment(seg)
        print(f"  音频已添加: {mat.material_name} (音量0.5, 淡入淡出)")

    # 4. 添加字幕
    if captions:
        script.add_track(TrackType.text, "字幕")
        style = TextStyle(
            size=5, bold=True, color=(1, 1, 1),
            align=1, auto_wrapping=True
        )
        border = TextBorder(color=(0, 0, 0), width=40)
        shadow = TextShadow(alpha=0.9, color=(0, 0, 0), diffuse=15, distance=5, angle=-45)
        cs = ClipSettings(transform_y=-0.8)

        for cap in captions:
            text = cap["text"]
            tr = Timerange(cap["start"], cap["end"] - cap["start"])
            seg = TextSegment(text, tr, style=style, border=border, shadow=shadow, clip_settings=cs)
            script.add_segment(seg, "字幕")

        print(f"  字幕已添加: {len(captions)} 条")

    # 5. 添加标题
    if title_text:
        script.add_track(TrackType.text, "标题", relative_index=1)

        style = TextStyle(size=12, bold=True, color=(1, 0.42, 0.21), align=1)
        border = TextBorder(color=(0, 0, 0), width=60)
        cs = ClipSettings(transform_y=0.5, scale_x=1.5, scale_y=1.5)
        tr = Timerange(tim("0.5s"), tim("3s"))
        seg = TextSegment(title_text, tr, style=style, border=border, clip_settings=cs)
        script.add_segment(seg, "标题")
        print(f"  标题已添加: {title_text}")

    # 6. 保存
    script.save()
    print(f"  草稿已保存: {script.save_path}")
    print(f"  总时长: {script.duration/1e6:.1f}s")

    return {
        "success": True,
        "draft_path": os.path.join(folder_path, draft_name),
        "duration": script.duration,
        "duration_seconds": script.duration / 1e6
    }


def main():
    """示例: 模拟从 ASR/LLM 生成的字幕数据创建剪映草稿"""

    # 临时目录
    tmpdir = tempfile.mkdtemp(prefix='jianying_demo_')
    print(f"草稿目录: {tmpdir}\n")

    # 模拟 ASR 输出的字幕数据（时间单位: 微秒）
    captions = [
        {"text": "大家好，欢迎观看本期教程", "start": 0, "end": 3_000_000},
        {"text": "今天我们学习 Python 剪映自动化", "start": 3_000_000, "end": 6_000_000},
        {"text": "首先安装 pyJianYingDraft 库", "start": 6_000_000, "end": 9_000_000},
        {"text": "然后使用工具类创建草稿", "start": 9_000_000, "end": 12_000_000},
        {"text": "添加视频、音频和字幕", "start": 12_000_000, "end": 15_000_000},
        {"text": "最后保存草稿，在剪映中打开", "start": 15_000_000, "end": 18_000_000},
        {"text": "感谢观看，记得点赞关注！", "start": 18_000_000, "end": 21_000_000},
    ]

    # 一站式创建（不需要视频/音频素材也能运行）
    print("创建草稿...")
    result = create_video_draft(
        folder_path=tmpdir,
        draft_name="AI字幕草稿",
        captions=captions,
        title_text="Python 剪映教程"
    )

    print(f"\n结果: {result}")

    # 验证文件
    content_path = os.path.join(tmpdir, "AI字幕草稿", "draft_content.json")
    if os.path.exists(content_path):
        size = os.path.getsize(content_path)
        print(f"\ndraft_content.json: {size:,} bytes")
        print("请在剪映中打开此草稿查看效果:")
        print(f"  {os.path.join(tmpdir, 'AI字幕草稿')}")

    # 清理
    shutil.rmtree(tmpdir)
    print("\n示例完成!")


if __name__ == "__main__":
    main()
