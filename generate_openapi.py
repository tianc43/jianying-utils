"""
Generate the complete OpenAPI 3.1.0 specification for jianying_utils.
This script reads the existing spec as a base and augments it with
proper response schemas derived from the server.py implementation.

Usage:
    python generate_openapi.py [--output path.json]
"""

from __future__ import annotations
import json, sys, os, copy
from pathlib import Path

# ── Base schemas reused across responses ──────────────────────────────

SUCCESS_BASE = {
    "success": {"type": "boolean", "description": "操作是否成功", "default": True}
}

# Specific response schemas
RESPONSE_SCHEMAS = {
    "HealthResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "status": {"type": "string", "description": "服务状态", "example": "ok"},
            "version": {"type": "string", "description": "API 版本号", "example": "0.2.0"},
            "drafts_dir": {"type": "string", "description": "草稿存储目录"},
            "active_drafts": {"type": "integer", "description": "当前活跃草稿数"}
        },
        "additionalProperties": False
    },
    "DraftCreateResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "message": {"type": "string", "description": "操作结果消息"},
            "draft_id": {"type": "string", "description": "草稿唯一 ID（12 位 hex）", "example": "ac51f93630c2"},
            "draft_name": {"type": "string", "description": "草稿名称"},
            "draft_folder": {"type": "string", "description": "草稿文件夹路径"},
            "script_path": {"type": "string", "description": "草稿脚本文件路径"}
        },
        "additionalProperties": False
    },
    "DraftsListResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "message": {"type": "string", "description": "操作结果消息"},
            "drafts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "draft_id": {"type": "string"},
                        "draft_name": {"type": "string"},
                        "draft_folder": {"type": "string"}
                    }
                }
            },
            "count": {"type": "integer", "description": "草稿总数"}
        },
        "additionalProperties": False
    },
    "DraftInfoResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "message": {"type": "string", "description": "操作结果消息"},
            "draft_folder": {"type": "string", "description": "草稿文件夹路径"},
            "draft_name": {"type": "string", "description": "草稿名称"},
            "script_path": {"type": "string", "description": "草稿脚本文件路径"},
            "width": {"type": "integer", "description": "视频宽度"},
            "height": {"type": "integer", "description": "视频高度"},
            "fps": {"type": "integer", "description": "帧率"},
            "duration": {"type": "integer", "description": "草稿总时长（微秒）"}
        },
        "additionalProperties": False
    },
    "DraftExportResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "message": {"type": "string", "description": "操作结果消息"},
            "json_string": {"type": "string", "description": "草稿 JSON 字符串"},
            "draft_name": {"type": "string", "description": "草稿名称"}
        },
        "additionalProperties": False
    },
    "GenericSuccessResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功", "default": True},
            "message": {"type": "string", "description": "操作结果消息"}
        },
        "additionalProperties": False
    },
    "DraftSaveResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "message": {"type": "string", "description": "操作结果消息"},
            "script_path": {"type": "string", "description": "保存后的脚本文件路径"}
        },
        "additionalProperties": False
    },
    "TrackItem": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "轨道名称"},
            "type": {"type": "string", "description": "轨道类型"},
            "render_index": {"type": "integer", "description": "渲染层级"},
            "mute": {"type": "boolean", "description": "是否静音"},
            "segment_count": {"type": "integer", "description": "片段数量"},
            "source": {"type": "string", "description": "来源标识（imported=导入轨道）"}
        }
    },
    "TrackAddResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "message": {"type": "string", "description": "操作结果消息"},
            "track_type": {"type": "string", "description": "轨道类型"},
            "track_name": {"type": "string", "description": "轨道名称"}
        },
        "additionalProperties": False
    },
    "TrackListResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "message": {"type": "string", "description": "操作结果消息"},
            "tracks": {
                "type": "array",
                "items": {"$ref": "#/components/schemas/TrackItem"},
                "description": "轨道列表"
            }
        },
        "additionalProperties": False
    },
    "MetadataItem": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "内部名称"},
            "display_name": {"type": "string", "description": "显示名称"},
            "is_vip": {"type": "boolean", "description": "是否 VIP"},
            "resource_id": {"type": "string", "description": "资源 ID"},
            "effect_id": {"type": "string", "description": "效果 ID"},
            "duration_us": {"type": "integer", "description": "持续时间（微秒，动画类）"},
            "duration_seconds": {"type": "number", "description": "持续时间（秒，动画类）"},
            "params": {
                "type": "array",
                "items": {"$ref": "#/components/schemas/MetadataParamItem"},
                "description": "参数列表"
            }
        }
    },
    "MetadataParamItem": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "参数名称"},
            "default": {"type": "number", "description": "默认值"},
            "min": {"type": "number", "description": "最小值"},
            "max": {"type": "number", "description": "最大值"}
        }
    },
    "SegmentResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "message": {"type": "string", "description": "操作结果消息"},
            "segment_id": {"type": "string", "description": "新创建片段的 ID"}
        },
        "additionalProperties": False
    },
    "BatchResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "message": {"type": "string", "description": "操作结果消息"},
            "count": {"type": "integer", "description": "添加的片段数量"},
            "segment_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "新创建片段的 ID 列表"
            }
        },
        "additionalProperties": False
    },
    "TimeParseResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "microseconds": {"type": "integer", "description": "解析后的微秒数", "example": 5000000},
            "message": {"type": "string", "description": "操作结果消息"}
        },
        "additionalProperties": False
    },
    "TimeFormatResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "formatted": {"type": "string", "description": "格式化后的时间字符串", "example": "00:01:05.000"},
            "message": {"type": "string", "description": "操作结果消息"}
        },
        "additionalProperties": False
    },
    "SimpleWorkflowResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "message": {"type": "string", "description": "操作结果消息"},
            "duration": {"type": "integer", "description": "草稿总时长（微秒）"},
            "duration_seconds": {"type": "number", "description": "草稿总时长（秒）"}
        },
        "additionalProperties": False
    },
    "MaterialVideoInfoResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "message": {"type": "string", "description": "操作结果消息"},
            "duration": {"type": "integer", "description": "时长（微秒）"},
            "width": {"type": "integer", "description": "视频宽度"},
            "height": {"type": "integer", "description": "视频高度"},
            "type": {"type": "string", "description": "素材类型（video/image）"},
            "material_name": {"type": "string", "description": "素材文件名"},
            "path": {"type": "string", "description": "素材文件路径"}
        },
        "additionalProperties": False
    },
    "MaterialAudioDurationResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "message": {"type": "string", "description": "操作结果消息"},
            "duration": {"type": "integer", "description": "音频时长（微秒）"},
            "duration_seconds": {"type": "number", "description": "音频时长（秒）"},
            "material_name": {"type": "string", "description": "素材文件名"},
            "path": {"type": "string", "description": "素材文件路径"}
        },
        "additionalProperties": False
    },
    "MetadataListResponse": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "description": "操作是否成功"},
            "message": {"type": "string", "description": "操作结果消息"},
            "items": {
                "type": "array",
                "items": {"$ref": "#/components/schemas/MetadataItem"},
                "description": "元数据项列表"
            },
            "count": {"type": "integer", "description": "总数"}
        },
        "additionalProperties": False
    },
}

# ── Map each path+method to its response schema ───────────────────────

PATH_RESPONSE_MAP = {
    ("/health", "get"): "HealthResponse",
    ("/drafts", "post"): "DraftCreateResponse",
    ("/drafts", "get"): "DraftsListResponse",
    ("/drafts/{draft_id}", "get"): "DraftInfoResponse",
    ("/drafts/{draft_id}", "delete"): "GenericSuccessResponse",
    ("/drafts/{draft_id}/save", "post"): "DraftSaveResponse",
    ("/drafts/{draft_id}/export", "post"): "DraftExportResponse",
    ("/drafts/{draft_id}/tracks", "post"): "TrackAddResponse",
    ("/drafts/{draft_id}/tracks", "get"): "TrackListResponse",
    ("/drafts/{draft_id}/videos", "post"): "SegmentResponse",
    ("/drafts/{draft_id}/videos/batch", "post"): "BatchResponse",
    ("/drafts/{draft_id}/audios", "post"): "SegmentResponse",
    ("/drafts/{draft_id}/audios/batch", "post"): "BatchResponse",
    ("/drafts/{draft_id}/audios/fade", "post"): "GenericSuccessResponse",
    ("/drafts/{draft_id}/texts", "post"): "SegmentResponse",
    ("/drafts/{draft_id}/captions", "post"): "BatchResponse",
    ("/drafts/{draft_id}/effects/scene", "post"): "GenericSuccessResponse",
    ("/drafts/{draft_id}/effects/character", "post"): "GenericSuccessResponse",
    ("/drafts/{draft_id}/effects/filter", "post"): "GenericSuccessResponse",
    ("/drafts/{draft_id}/effects/batch", "post"): "BatchResponse",
    ("/drafts/{draft_id}/stickers", "post"): "SegmentResponse",
    ("/drafts/{draft_id}/animations/video-intro", "post"): "GenericSuccessResponse",
    ("/drafts/{draft_id}/animations/video-outro", "post"): "GenericSuccessResponse",
    ("/drafts/{draft_id}/animations/video-group", "post"): "GenericSuccessResponse",
    ("/drafts/{draft_id}/animations/text-intro", "post"): "GenericSuccessResponse",
    ("/drafts/{draft_id}/animations/text-outro", "post"): "GenericSuccessResponse",
    ("/drafts/{draft_id}/animations/text-loop", "post"): "GenericSuccessResponse",
    ("/drafts/{draft_id}/keyframes", "post"): "GenericSuccessResponse",
    ("/drafts/{draft_id}/keyframes/batch", "post"): "BatchResponse",
    ("/drafts/{draft_id}/transitions", "post"): "GenericSuccessResponse",
    ("/drafts/{draft_id}/transitions/batch", "post"): "BatchResponse",
    ("/drafts/{draft_id}/workflow/simple", "post"): "SimpleWorkflowResponse",
    ("/metadata/transitions", "get"): "MetadataListResponse",
    ("/metadata/filters", "get"): "MetadataListResponse",
    ("/metadata/fonts", "get"): "MetadataListResponse",
    ("/metadata/masks", "get"): "MetadataListResponse",
    ("/metadata/mix-modes", "get"): "MetadataListResponse",
    ("/metadata/video-intros", "get"): "MetadataListResponse",
    ("/metadata/video-outros", "get"): "MetadataListResponse",
    ("/metadata/video-group-anims", "get"): "MetadataListResponse",
    ("/metadata/text-intros", "get"): "MetadataListResponse",
    ("/metadata/text-outros", "get"): "MetadataListResponse",
    ("/metadata/text-loop-anims", "get"): "MetadataListResponse",
    ("/metadata/scene-effects", "get"): "MetadataListResponse",
    ("/metadata/character-effects", "get"): "MetadataListResponse",
    ("/metadata/audio-effects", "get"): "MetadataListResponse",
    ("/material/video-info", "get"): "MaterialVideoInfoResponse",
    ("/material/audio-duration", "get"): "MaterialAudioDurationResponse",
    ("/util/time/parse", "post"): "TimeParseResponse",
    ("/util/time/format", "post"): "TimeFormatResponse",
}


def load_existing_spec(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_response_schemas(spec: dict) -> dict:
    """Update all endpoint responses to reference proper schemas."""
    spec = copy.deepcopy(spec)

    # Add response schemas to components
    if "components" not in spec:
        spec["components"] = {}
    if "schemas" not in spec["components"]:
        spec["components"]["schemas"] = {}
    for name, schema in RESPONSE_SCHEMAS.items():
        spec["components"]["schemas"][name] = schema

    # Update path responses
    for path_url, path_obj in spec.get("paths", {}).items():
        for method, operation in path_obj.items():
            key = (path_url, method.lower())
            schema_name = PATH_RESPONSE_MAP.get(key)
            if schema_name and "responses" in operation:
                success_resp = operation["responses"].get("200", {})
                if "content" in success_resp:
                    content_type = success_resp["content"].get("application/json", {})
                    content_type["schema"] = {"$ref": f"#/components/schemas/{schema_name}"}
                    success_resp["content"]["application/json"] = content_type
                    success_resp["description"] = _describe_schema(schema_name)
                    operation["responses"]["200"] = success_resp

    return spec


def _describe_schema(name: str) -> str:
    descriptions = {
        "HealthResponse": "服务健康状态",
        "DraftCreateResponse": "草稿创建成功，返回 draft_id",
        "DraftsListResponse": "活跃草稿列表",
        "DraftInfoResponse": "草稿详细信息（尺寸、时长、帧率等）",
        "DraftExportResponse": "草稿 JSON 导出",
        "GenericSuccessResponse": "操作成功",
        "TrackAddResponse": "轨道添加成功",
        "TrackListResponse": "轨道列表",
        "SegmentResponse": "片段添加成功，返回 segment_id",
        "BatchResponse": "批量操作成功",
        "TimeParseResponse": "时间解析结果",
        "TimeFormatResponse": "时间格式化结果",
        "SimpleWorkflowResponse": "一键创建完成",
        "MaterialVideoInfoResponse": "视频/图片素材信息",
        "MaterialAudioDurationResponse": "音频时长信息",
        "MetadataListResponse": "元数据查询结果",
    }
    return descriptions.get(name, "Successful Response")


def generate(input_path: str, output_path: str):
    spec = load_existing_spec(input_path)
    spec = apply_response_schemas(spec)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)

    # Print summary
    paths_count = len(spec.get("paths", {}))
    schemas_count = len(spec.get("components", {}).get("schemas", {}))
    endpoints_count = sum(len(methods) for methods in spec.get("paths", {}).values())
    resp_mapped = sum(1 for k in PATH_RESPONSE_MAP
                      for p, ms in spec.get("paths", {}).items()
                      if p == k[0]
                      for m in ms
                      if m == k[1])

    print(f"OpenAPI spec generated: {output_path}")
    print(f"  Path groups: {paths_count}")
    print(f"  Total endpoints: {endpoints_count}")
    print(f"  Schema definitions: {schemas_count}")
    print(f"  Response schemas mapped: {resp_mapped} endpoints")

    # Verify JSON is valid
    with open(output_path, "r", encoding="utf-8") as f:
        json.load(f)
    print(f"  JSON validation: PASSED")


if __name__ == "__main__":
    default_input = Path(__file__).parent.parent / "jianying_api_openapi.json"
    default_output = Path(__file__).parent / "jianying_api_openapi.json"

    input_path = default_input
    output_path = default_output

    # Parse args
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--input" and i + 1 < len(args):
            input_path = args[i + 1]
        elif arg == "--output" and i + 1 < len(args):
            output_path = args[i + 1]

    generate(str(input_path), str(output_path))
