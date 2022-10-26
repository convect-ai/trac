"""
Utility functions to generate API docs for a dataset
"""

import re

from trac.schema.task import FileDef

from .models import DataSet


def generate_openapi_paths(url_prefix, resource_schema: FileDef):
    """
    Generate openapi path (GET, POST, PUT, DELETE) definition for a jsonschema defined resource
    """
    resource_type = resource_schema.name.lower()

    paths = {
        f"/{url_prefix}/{resource_type}/": {
            "get": {
                "summary": f"List {resource_type}",
                "description": f"List all {resource_type}",
                "operationId": f"list_{resource_type}",
                "responses": {
                    "200": {
                        "description": f"List of {resource_type}",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {
                                        "$ref": f"#/components/schemas/{resource_type}"
                                    },
                                }
                            }
                        },
                    }
                },
            },
            "post": {
                "summary": f"Create {resource_type}",
                "description": f"Create a new {resource_type}",
                "operationId": f"create_{resource_type}",
                "requestBody": {
                    "description": f"{resource_type} to create",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{resource_type}"}
                        }
                    },
                    "required": True,
                },
                "responses": {
                    "201": {
                        "description": f"{resource_type} created",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": f"#/components/schemas/{resource_type}"
                                }
                            }
                        },
                    }
                },
            },
        },
        f"/{url_prefix}/{resource_type}/{{resource_id}}/": {
            "get": {
                "summary": f"Get {resource_type}",
                "description": f"Get a {resource_type}",
                "operationId": f"get_{resource_type}",
                "parameters": [
                    {
                        "name": "resource_id",
                        "in": "path",
                        "description": f"{resource_type} id",
                        "required": True,
                        "schema": {"type": "integer", "format": "int64"},
                    },
                ],
                "responses": {
                    "200": {
                        "description": f"{resource_type} found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": f"#/components/schemas/{resource_type}"
                                }
                            }
                        },
                    }
                },
            },
            "put": {
                "summary": f"Update {resource_type}",
                "description": f"Update a {resource_type}",
                "operationId": f"update_{resource_type}",
                "parameters": [
                    {
                        "name": "resource_id",
                        "in": "path",
                        "description": f"{resource_type} id",
                        "required": True,
                        "schema": {"type": "integer", "format": "int64"},
                    },
                ],
                "requestBody": {
                    "description": f"{resource_type} to update",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{resource_type}"}
                        }
                    },
                    "required": True,
                },
                "responses": {
                    "200": {
                        "description": f"{resource_type} updated",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": f"#/components/schemas/{resource_type}"
                                }
                            }
                        },
                    }
                },
            },
            "delete": {
                "summary": f"Delete {resource_type}",
                "description": f"Delete a {resource_type}",
                "operationId": f"delete_{resource_type}",
                "parameters": [
                    {
                        "name": "resource_id",
                        "in": "path",
                        "description": f"{resource_type} id",
                        "required": True,
                        "schema": {"type": "integer", "format": "int64"},
                    },
                ],
                "responses": {"204": {"description": f"{resource_type} deleted"}},
            },
        },
    }
    return paths


def generate_openapi_schema_component(resource_schema: FileDef):
    """
    Generate openapi schema component for a jsonschema defined resource
    """
    resource_type = resource_schema.name.lower()
    # sanitize the resource_schema["properties"] by replacing non-alphanumeric characters with _
    properties = {
        re.sub(r"\W+", "_", k): v
        for k, v in resource_schema.file_schema["properties"].items()
    }

    schema = {
        resource_type: {
            "type": "object",
            "properties": properties,
        }
    }

    return schema


def generate_openapi_schema_for_dataset(dataset: DataSet):
    """
    Generate openapi schema for a given dataset
    """
    url_prefix = f"data_gateway/datasets/{dataset.id}/api"
    schemas = dataset.schema["input_schema"]
    paths = {}
    oas_schemas = {}
    for schema in schemas:
        resource_paths = generate_openapi_paths(url_prefix, schema)
        paths.update(resource_paths)

        oas_schema = generate_openapi_schema_component(schema)
        oas_schemas.update(oas_schema)

    components = {
        "schemas": oas_schemas,
    }
    return {
        "openapi": "3.0.0",
        "info": {"title": f"{dataset.name} API", "version": "1.0.0"},
        "description": "API specification for the dataset - {}".format(dataset.name),
        "paths": paths,
        "components": components,
    }
