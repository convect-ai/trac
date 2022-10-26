# definitions about tasks and apps

import re
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field, root_validator, validator


class FILE_TYPE(str, Enum):
    """File type enumeration"""

    INPUT = "input"
    OUTPUT = "output"


class ParameterDef(BaseModel):
    name: str
    type: str
    default: Any = None
    description: str = None


class ParametersSpec(BaseModel):
    mount_path: str  # mount path for the parameter file
    parameters: List[ParameterDef]


class FileDef(BaseModel):
    name: str
    # enum file type, e.g., INPUT, OUTPUT, etc.
    type: FILE_TYPE = FILE_TYPE.INPUT
    mount_path: str
    description: str = None
    # schema for the file, a json schema object
    file_schema: dict

    @validator("file_schema")
    def validate_file_schema(cls, v):
        """
        Validate if schema is a valid json schema object
        """
        try:
            Draft202012Validator.check_schema(v)
        except Exception as e:
            raise ValueError(f"Invalid schema: {e}")
        return v


class FilesSpec(BaseModel):
    files: List[FileDef]


class ContainerSpec(BaseModel):
    image: str
    tag: str
    command: Optional[List[str]]
    args: Optional[List[str]]
    # envs, a list of (name, value) pairs
    envs: Optional[List[Tuple[str, str]]] = []


class PythonHandlerSpec(BaseModel):
    handler: str
    kwargs: Dict[str, Any] = {}  # additional kwargs for the handler function

    @validator("handler")
    def validate_handler(cls, v):
        """
        Validate if handler is a valid python handler

        e.g., "module:handler_func"
        """
        if ":" not in v:
            raise ValueError(
                "Invalid handler, should be in format of 'module:handler_func'"
            )
        return v


class TaskDef(BaseModel):
    name: str = Field(..., description="Name of the task")
    description: str = Field(..., description="Description of the task")

    # parameters specification
    parameter: ParametersSpec = Field(
        None, description="Parameters specification for the task"
    )

    # io specification
    io: FilesSpec = Field(None, description="IO specification for the task")

    # container definition
    container: Optional[ContainerSpec] = None

    # handler definition
    handler: Optional[PythonHandlerSpec] = None

    @validator("name")
    def validate_name(cls, v):
        """
        Name should only contain alphanumeric characters and underscore and "-"
        """
        name_pattern = re.compile(r"^[a-zA-Z0-9_-]+$")
        if not name_pattern.match(v):
            raise ValueError("Name should only contain alphanumeric characters")
        return v

    @root_validator
    def container_handler_mutex(cls, values):
        """
        Validate if container and handler are mutually exclusive
        """
        # if values.get("container") and values.get("handler"):
        #     raise ValueError("Container and handler are mutually exclusive")

        # at leaset one of container and handler should be defined
        if not values.get("container") and not values.get("handler"):
            raise ValueError("Container or handler should be defined")
        return values


class AppDef(BaseModel):
    name: str = Field(..., description="Name of the app")
    description: str = Field(..., description="Description of the app")
    tasks: List[TaskDef] = Field(..., description="List of tasks")


class RunConfig(BaseModel):
    """
    Configs for a concrete task, including the parameter values, the input and output file locations
    """

    parameters: Dict[str, Any] = Field(..., description="Parameter values")
    input_files: Dict[str, str] = Field(..., description="Input file locations")
