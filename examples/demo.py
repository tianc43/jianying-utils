"""jianying_utils 完整工作流示例

演示如何使用各工具类创建一个完整的剪映草稿：
1. 创建草稿
2. 添加轨道
3. 添加视频、音频、字幕
4. 添加特效、转场
5. 查询元数据
6. 导出草稿

在 Dify 工作流中，每个步骤对应一个代码节点，
通过 folder_path + draft_name 传递草稿状态。
"""

import os
import sys

# 确保 jianying_utils 可被导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from jianying_utils import (
    DraftManager, TrackManager, VideoTool, AudioTool,
    TextTool, EffectTool, StickerTool, AnimationTool,
    KeyframeTool, TransitionTool, MaterialTool,
    MetadataQuery, TimeTool, ExportTool
)


def main():
    # =========================================================================
    # 配置
    # =========================================================================
    DRAFT_FOLDER = os.path.expanduser("~/JianyingPro Drafts")
    DRAFT_NAME = "示例草稿_自动创建"

    # 请替换为实际存在的素材文件路径
    VIDEO_PATH = r"C:\Videos\sample_video.mp4"
    AUDIO_PATH = r"C:\Audios\sample_audio.mp3"
    IMAGE_PATH = r"C:\Images\sample_image.jpg"

    # =========================================================================
    # 步骤 1: 创建草稿
    # =========================================================================
    print("=" * 60)
    print("步骤 1: 创建草稿")
    result = DraftManager.create_draft(
        folder_path=DRAFT_FOLDER,
        draft_name=DRAFT_NAME,
        width=1920,
        height=1080,
        fps=30,
        allow_replace=True
    )
    print(f"  结果: {result}")
    if not result["success"]:
        print("创建草稿失败，退出")
        return

    # =========================================================================
    # 步骤 2: 添加轨道
    # =========================================================================
    print("\n" + "=" * 60)
    print("步骤 2: 添加轨道")

    # 添加视频轨道
    r1 = TrackManager.add_track(DRAFT_FOLDER, DRAFT_NAME, "video")
    print(f"  视频轨道: {r1}")

    # 添加音频轨道
    r2 = TrackManager.add_track(DRAFT_FOLDER, DRAFT_NAME, "audio")
    print(f"  音频轨道: {r2}")

    # 添加文本轨道
    r3 = TrackManager.add_track(DRAFT_FOLDER, DRAFT_NAME, "text", "subtitle_track")
    print(f"  文本轨道: {r3}")

    # 添加特效轨道
    r4 = TrackManager.add_track(DRAFT_FOLDER, DRAFT_NAME, "effect")
    print(f"  特效轨道: {r4}")

    # 列出所有轨道
    tracks = TrackManager.list_tracks(DRAFT_FOLDER, DRAFT_NAME)
    print(f"  轨道列表: {tracks['tracks']}")

    # =========================================================================
    # 步骤 3: 查询元数据（了解可用的效果）
    # =========================================================================
    print("\n" + "=" * 60)
    print("步骤 3: 查询元数据")

    # 查询免费转场（前5个）
    transitions = MetadataQuery.list_transitions(mode=2)
    print(f"  免费转场数量: {transitions['count']}")
    if transitions['items']:
        for t in transitions['items'][:5]:
            print(f"    - {t['display_name']} (默认时长可查看)")

    # 查询免费滤镜（前5个）
    filters = MetadataQuery.list_filters(mode=2)
    print(f"  免费滤镜数量: {filters['count']}")
    if filters['items']:
        for f in filters['items'][:5]:
            print(f"    - {f['display_name']}")

    # 查询视频入场动画（前5个免费）
    intros = MetadataQuery.list_video_intros(mode=2)
    print(f"  免费入场动画数量: {intros['count']}")

    # 查询字体（前5个免费）
    fonts = MetadataQuery.list_fonts(mode=2)
    print(f"  免费字体数量: {fonts['count']}")

    # 查询关键帧属性
    kf_props = KeyframeTool.list_properties()
    print(f"  关键帧属性: {[p['name'] for p in kf_props['properties']]}")

    # =========================================================================
    # 步骤 4: 时间工具使用
    # =========================================================================
    print("\n" + "=" * 60)
    print("步骤 4: 时间工具")

    t1 = TimeTool.parse_time("5s")["microseconds"]
    print(f"  '5s' = {t1} 微秒")

    t2 = TimeTool.parse_time("1m30s")["microseconds"]
    print(f"  '1m30s' = {t2} 微秒")

    formatted = TimeTool.format_time(65_000_000)["formatted"]
    print(f"  65000000 μs = {formatted}")

    tr = TimeTool.create_timerange("0s", "5s")
    print(f"  时间范围: {tr}")

    tr2 = TimeTool.timerange_from_start_end("5s", "10s")
    print(f"  5s~10s: {tr2}")

    sec = TimeTool.seconds_to_microseconds(3.5)["microseconds"]
    print(f"  3.5秒 = {sec} 微秒")

    # =========================================================================
    # 步骤 5: 添加视频片段（如果素材存在）
    # =========================================================================
    print("\n" + "=" * 60)
    print("步骤 5: 添加视频片段")

    if os.path.exists(VIDEO_PATH):
        # 获取素材信息
        info = MaterialTool.get_video_info(VIDEO_PATH)
        print(f"  素材信息: {info}")

        if info["success"]:
            # 添加视频: 从0s开始，持续5s
            r = VideoTool.add_video(
                DRAFT_FOLDER, DRAFT_NAME,
                VIDEO_PATH,
                start="0s", duration="5s",
                speed=1.0, volume=1.0,
                clip_settings={"scale_x": 1.0, "scale_y": 1.0}
            )
            print(f"  添加视频: {r}")

            if r["success"]:
                seg_id = r["segment_id"]

                # 添加入场动画
                anim_r = AnimationTool.add_video_intro(
                    DRAFT_FOLDER, DRAFT_NAME,
                    seg_id,
                    animation_name="淡入",   # 替换为实际存在的动画名
                    duration="0.5s"
                )
                print(f"  入场动画: {anim_r}")
    else:
        print(f"  素材文件不存在: {VIDEO_PATH}（跳过）")

    # =========================================================================
    # 步骤 6: 批量添加图片（模拟 Dify 工作流中的 image_infos 参数）
    # =========================================================================
    print("\n" + "=" * 60)
    print("步骤 6: 批量添加图片")

    if os.path.exists(IMAGE_PATH):
        # 第二张图片轨道
        TrackManager.add_track(DRAFT_FOLDER, DRAFT_NAME, "video", "overlay_track", relative_index=1)

        image_infos = [
            {
                "video_path": IMAGE_PATH,
                "start": 0,
                "end": 5_000_000,  # 5秒
                "alpha": 0.8,
                "scale_x": 0.5,
                "scale_y": 0.5,
                "transform_x": 0.3,
                "transform_y": 0.3,
            }
        ]
        r = VideoTool.add_videos_batch(
            DRAFT_FOLDER, DRAFT_NAME,
            image_infos,
            track_name="overlay_track"
        )
        print(f"  批量添加图片: {r}")
    else:
        print(f"  素材文件不存在: {IMAGE_PATH}（跳过）")

    # =========================================================================
    # 步骤 7: 添加音频
    # =========================================================================
    print("\n" + "=" * 60)
    print("步骤 7: 添加音频")

    if os.path.exists(AUDIO_PATH):
        # 获取音频时长
        dur = MaterialTool.get_audio_duration(AUDIO_PATH)
        print(f"  音频时长: {dur}")

        if dur["success"]:
            r = AudioTool.add_audio(
                DRAFT_FOLDER, DRAFT_NAME,
                AUDIO_PATH,
                start="0s",
                volume=0.8
            )
            print(f"  添加音频: {r}")

            if r["success"]:
                seg_id = r["segment_id"]
                # 添加淡入淡出
                fade_r = AudioTool.add_fade(
                    DRAFT_FOLDER, DRAFT_NAME,
                    seg_id,
                    in_duration="1s",
                    out_duration="2s"
                )
                print(f"  淡入淡出: {fade_r}")
    else:
        print(f"  素材文件不存在: {AUDIO_PATH}（跳过）")

    # =========================================================================
    # 步骤 8: 添加字幕
    # =========================================================================
    print("\n" + "=" * 60)
    print("步骤 8: 添加字幕")

    # 批量字幕（模拟从 ASR 或 LLM 生成的字幕数据）
    captions = [
        {"text": "大家好，欢迎观看本期视频", "start": 0, "end": 3_000_000},
        {"text": "今天我们来聊聊 Python 编程", "start": 3_000_000, "end": 6_000_000},
        {"text": "首先我们来看看基础语法", "start": 6_000_000, "end": 9_000_000},
        {"text": "感谢观看，记得点赞关注！", "start": 9_000_000, "end": 12_000_000},
    ]

    r = TextTool.add_captions_batch(
        DRAFT_FOLDER, DRAFT_NAME,
        captions,
        font_size=5.0,
        text_color="#FFFFFF",
        bold=True,
        alignment=1,  # 居中
        auto_wrapping=True,
        shadow={"alpha": 0.9, "color": "#000000", "diffuse": 15, "distance": 5, "angle": -45},
        clip_settings={"transform_y": -0.8},
        track_name="subtitle_track"
    )
    print(f"  批量字幕: {r}")

    # 添加单独的艺术标题文本
    title_r = TextTool.add_text(
        DRAFT_FOLDER, DRAFT_NAME,
        text="Python 教程",
        start="1s", duration="3s",
        font_size=12.0,
        text_color="#FF6B35",
        bold=True,
        alignment=1,
        border={"alpha": 1.0, "color": "#000000", "width": 50.0},
        clip_settings={"transform_y": 0.5, "scale_x": 1.5, "scale_y": 1.5}
    )
    print(f"  标题文本: {title_r}")

    # =========================================================================
    # 步骤 9: 添加特效
    # =========================================================================
    print("\n" + "=" * 60)
    print("步骤 9: 添加特效")

    # 添加场景特效到特效轨道
    effect_r = EffectTool.add_scene_effect(
        DRAFT_FOLDER, DRAFT_NAME,
        effect_name="金粉闪闪",  # 替换为实际存在的特效名
        start="0s", duration="5s"
    )
    print(f"  场景特效: {effect_r}")

    # 批量添加特效
    effect_infos = [
        {"effect_title": "闪白", "start": 0, "end": 2_000_000},
        {"effect_title": "抖动", "start": 2_000_000, "end": 5_000_000},
    ]
    batch_r = EffectTool.add_effects_batch(
        DRAFT_FOLDER, DRAFT_NAME,
        effect_infos
    )
    print(f"  批量特效: {batch_r}")

    # 添加滤镜
    filter_r = EffectTool.add_filter_track(
        DRAFT_FOLDER, DRAFT_NAME,
        filter_name="书意",  # 替换为实际存在的滤镜名
        start="0s", duration="10s",
        intensity=80.0
    )
    print(f"  滤镜: {filter_r}")

    # =========================================================================
    # 步骤 10: 导出和保存
    # =========================================================================
    print("\n" + "=" * 60)
    print("步骤 10: 导出")

    # 导出为 JSON 字符串
    json_r = ExportTool.dumps_to_string(DRAFT_FOLDER, DRAFT_NAME)
    print(f"  JSON 大小: {json_r.get('size', 0)} 字符")

    # 列出最终轨道状态
    final_tracks = TrackManager.list_tracks(DRAFT_FOLDER, DRAFT_NAME)
    print(f"  最终轨道: {final_tracks}")

    # 加载并查看草稿状态
    load_r = DraftManager.load_draft(DRAFT_FOLDER, DRAFT_NAME)
    print(f"  草稿状态: duration={load_r.get('duration')}μs, {load_r.get('width')}x{load_r.get('height')}")

    print("\n" + "=" * 60)
    print("✅ 示例工作流完成！")
    print(f"草稿位置: {os.path.join(DRAFT_FOLDER, DRAFT_NAME)}")
    print("请在剪映中打开此草稿查看效果。")


if __name__ == "__main__":
    main()
