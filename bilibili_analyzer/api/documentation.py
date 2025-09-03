"""
API文档路由 - Swagger/OpenAPI文档
"""

from flask import Blueprint, render_template_string, jsonify, request
from . import bp

# Swagger UI HTML模板
SWAGGER_UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bilibili Video Analysis API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
    <style>
        html {
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }
        *, *:before, *:after {
            box-sizing: inherit;
        }
        body {
            margin: 0;
            background: #fafafa;
        }
        .swagger-ui .topbar {
            display: none;
        }
        .custom-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .custom-header h1 {
            margin: 0;
            font-size: 2em;
        }
        .custom-header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class="custom-header">
        <h1>🎬 Bilibili Video Analysis API</h1>
        <p>RESTful API for analyzing Bilibili video content and managing knowledge base</p>
    </div>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            const spec = {
                "openapi": "3.0.0",
                "info": {
                    "title": "Bilibili Video Analysis API",
                    "version": "1.0.0",
                    "description": "RESTful API for analyzing Bilibili video content and managing knowledge base. This API provides endpoints for video information extraction, subtitle downloading, content analysis, and knowledge base management.",
                    "contact": {
                        "name": "API Support",
                        "email": "support@example.com"
                    },
                    "license": {
                        "name": "MIT",
                        "url": "https://opensource.org/licenses/MIT"
                    }
                },
                "servers": [
                    {
                        "url": "http://localhost:5000",
                        "description": "Development server"
                    }
                ],
                "paths": {
                    "/api/v1/health": {
                        "get": {
                            "summary": "Health Check",
                            "description": "Check the health status of the API service",
                            "tags": ["System"],
                            "responses": {
                                "200": {
                                    "description": "Service is healthy",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "success": {"type": "boolean"},
                                                    "message": {"type": "string"},
                                                    "timestamp": {"type": "string"},
                                                    "data": {
                                                        "type": "object",
                                                        "properties": {
                                                            "status": {"type": "string"},
                                                            "components": {"type": "object"},
                                                            "version": {"type": "string"}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/api/v1/video/extract": {
                        "post": {
                            "summary": "Extract Video Information",
                            "description": "Extract video information from Bilibili using BV ID",
                            "tags": ["Video"],
                            "requestBody": {
                                "required": true,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["bvid"],
                                            "properties": {
                                                "bvid": {
                                                    "type": "string",
                                                    "description": "Bilibili video ID",
                                                    "example": "BV1GJ411x7h7"
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Video information extracted successfully",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "success": {"type": "boolean"},
                                                    "message": {"type": "string"},
                                                    "data": {
                                                        "type": "object",
                                                        "properties": {
                                                            "video_info": {"type": "object"},
                                                            "subtitle_available": {"type": "boolean"},
                                                            "db_id": {"type": "integer"}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                },
                                "404": {
                                    "description": "Video not found"
                                },
                                "500": {
                                    "description": "Internal server error"
                                }
                            }
                        }
                    },
                    "/api/v1/subtitle/download": {
                        "post": {
                            "summary": "Download Subtitle",
                            "description": "Download subtitle for a specific video",
                            "tags": ["Video"],
                            "requestBody": {
                                "required": true,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["bvid"],
                                            "properties": {
                                                "bvid": {
                                                    "type": "string",
                                                    "description": "Bilibili video ID"
                                                },
                                                "language": {
                                                    "type": "string",
                                                    "description": "Subtitle language",
                                                    "default": "zh-CN"
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Subtitle downloaded successfully"
                                },
                                "404": {
                                    "description": "Video or subtitle not found"
                                }
                            }
                        }
                    },
                    "/api/v1/analyze": {
                        "post": {
                            "summary": "Analyze Content",
                            "description": "Analyze video subtitle content using AI",
                            "tags": ["Analysis"],
                            "requestBody": {
                                "required": true,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["bvid"],
                                            "properties": {
                                                "bvid": {
                                                    "type": "string",
                                                    "description": "Bilibili video ID"
                                                },
                                                "language": {
                                                    "type": "string",
                                                    "description": "Subtitle language",
                                                    "default": "zh-CN"
                                                },
                                                "service_name": {
                                                    "type": "string",
                                                    "description": "LLM service name"
                                                },
                                                "force_reanalyze": {
                                                    "type": "boolean",
                                                    "description": "Force re-analysis even if cached result exists",
                                                    "default": false
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "Content analyzed successfully"
                                },
                                "404": {
                                    "description": "Video or subtitle not found"
                                }
                            }
                        }
                    },
                    "/api/v1/knowledge/search": {
                        "get": {
                            "summary": "Search Knowledge Base",
                            "description": "Search knowledge entries using full-text search",
                            "tags": ["Knowledge"],
                            "parameters": [
                                {
                                    "name": "q",
                                    "in": "query",
                                    "required": true,
                                    "description": "Search query",
                                    "schema": {"type": "string"}
                                },
                                {
                                    "name": "limit",
                                    "in": "query",
                                    "description": "Maximum number of results",
                                    "schema": {"type": "integer", "default": 50}
                                },
                                {
                                    "name": "offset",
                                    "in": "query",
                                    "description": "Offset for pagination",
                                    "schema": {"type": "integer", "default": 0}
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "Search results"
                                }
                            }
                        }
                    },
                    "/api/v1/knowledge": {
                        "get": {
                            "summary": "List Knowledge Entries",
                            "description": "Get paginated list of knowledge entries",
                            "tags": ["Knowledge"],
                            "parameters": [
                                {
                                    "name": "page",
                                    "in": "query",
                                    "description": "Page number",
                                    "schema": {"type": "integer", "default": 1}
                                },
                                {
                                    "name": "per_page",
                                    "in": "query",
                                    "description": "Items per page",
                                    "schema": {"type": "integer", "default": 20}
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "List of knowledge entries"
                                }
                            }
                        },
                        "post": {
                            "summary": "Create Knowledge Entry",
                            "description": "Create a new knowledge entry",
                            "tags": ["Knowledge"],
                            "requestBody": {
                                "required": true,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["title", "content"],
                                            "properties": {
                                                "title": {
                                                    "type": "string",
                                                    "description": "Entry title"
                                                },
                                                "content": {
                                                    "type": "string",
                                                    "description": "Entry content"
                                                },
                                                "knowledge_type": {
                                                    "type": "string",
                                                    "description": "Type of knowledge",
                                                    "default": "concept",
                                                    "enum": ["concept", "fact", "method", "tip"]
                                                },
                                                "importance": {
                                                    "type": "integer",
                                                    "description": "Importance level (1-5)",
                                                    "default": 1,
                                                    "minimum": 1,
                                                    "maximum": 5
                                                },
                                                "tags": {
                                                    "type": "array",
                                                    "items": {"type": "string"},
                                                    "description": "List of tags"
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "201": {
                                    "description": "Knowledge entry created successfully"
                                },
                                "400": {
                                    "description": "Invalid request data"
                                }
                            }
                        }
                    },
                    "/api/v1/tags": {
                        "get": {
                            "summary": "List Tags",
                            "description": "Get paginated list of tags",
                            "tags": ["Tags"],
                            "parameters": [
                                {
                                    "name": "page",
                                    "in": "query",
                                    "description": "Page number",
                                    "schema": {"type": "integer", "default": 1}
                                },
                                {
                                    "name": "per_page",
                                    "in": "query",
                                    "description": "Items per page",
                                    "schema": {"type": "integer", "default": 20}
                                }
                            ],
                            "responses": {
                                "200": {
                                    "description": "List of tags"
                                }
                            }
                        },
                        "post": {
                            "summary": "Create Tag",
                            "description": "Create a new tag",
                            "tags": ["Tags"],
                            "requestBody": {
                                "required": true,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "required": ["name"],
                                            "properties": {
                                                "name": {
                                                    "type": "string",
                                                    "description": "Tag name"
                                                },
                                                "color": {
                                                    "type": "string",
                                                    "description": "Tag color (hex format)",
                                                    "default": "#007bff"
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "201": {
                                    "description": "Tag created successfully"
                                },
                                "409": {
                                    "description": "Tag already exists"
                                }
                            }
                        }
                    },
                    "/api/v1/stats": {
                        "get": {
                            "summary": "Get System Statistics",
                            "description": "Get comprehensive system statistics",
                            "tags": ["System"],
                            "responses": {
                                "200": {
                                    "description": "System statistics"
                                }
                            }
                        }
                    }
                },
                "tags": [
                    {
                        "name": "System",
                        "description": "System management and monitoring"
                    },
                    {
                        "name": "Video",
                        "description": "Video information extraction and management"
                    },
                    {
                        "name": "Analysis",
                        "description": "Content analysis using AI"
                    },
                    {
                        "name": "Knowledge",
                        "description": "Knowledge base management"
                    },
                    {
                        "name": "Tags",
                        "description": "Tag management"
                    }
                ],
                "components": {
                    "schemas": {
                        "ApiResponse": {
                            "type": "object",
                            "properties": {
                                "success": {"type": "boolean"},
                                "message": {"type": "string"},
                                "timestamp": {"type": "string"},
                                "data": {"type": "object"}
                            }
                        },
                        "PaginatedResponse": {
                            "type": "object",
                            "properties": {
                                "success": {"type": "boolean"},
                                "message": {"type": "string"},
                                "timestamp": {"type": "string"},
                                "data": {
                                    "type": "object",
                                    "properties": {
                                        "items": {"type": "array"},
                                        "pagination": {
                                            "type": "object",
                                            "properties": {
                                                "total": {"type": "integer"},
                                                "page": {"type": "integer"},
                                                "per_page": {"type": "integer"},
                                                "pages": {"type": "integer"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            };
            
            SwaggerUIBundle({
                url: "",
                spec: spec,
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                defaultModelsExpandDepth: -1,
                displayRequestDuration: true,
                docExpansion: "none",
                filter: true,
                showExtensions: true,
                showCommonExtensions: true
            });
        };
    </script>
</body>
</html>
"""

@bp.route('/docs', methods=['GET'])
def api_documentation():
    """API文档页面"""
    return render_template_string(SWAGGER_UI_TEMPLATE)

@bp.route('/docs/openapi.json', methods=['GET'])
def openapi_spec():
    """OpenAPI规范JSON"""
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Bilibili Video Analysis API",
            "version": "1.0.0",
            "description": "RESTful API for analyzing Bilibili video content and managing knowledge base"
        },
        "servers": [
            {
                "url": request.host_url.rstrip('/'),
                "description": "Current server"
            }
        ],
        "paths": {
            "/api/v1/health": {
                "get": {
                    "summary": "Health Check",
                    "tags": ["System"],
                    "responses": {
                        "200": {
                            "description": "Service is healthy"
                        }
                    }
                }
            }
        },
        "tags": [
            {"name": "System", "description": "System management"}
        ]
    }
    
    return jsonify(spec)