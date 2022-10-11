# defines the schema for task specifications


from enum import Enum
from typing import List, Tuple

from jsonschema import Draft202012Validator
from pydantic import BaseModel, Field, validator


class FILE_TYPE(Enum):
    """File type enumeration"""

    INPUT = "input"
    OUTPUT = "output"


class ParameterDef(BaseModel):
    name: str
    type: str
    default: str = None
    description: str = None


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


class ContainerDef(BaseModel):
    image: str
    tag: str
    command: List[str]
    args: List[str]
    # envs, a list of (name, value) pairs
    envs: List[Tuple[str, str]] = []


class TaskSpec(BaseModel):
    name: str = Field(..., description="Name of the task")
    description: str = Field(..., description="Description of the task")
    parameters: List[ParameterDef] = Field(..., description="List of parameters")

    # list of files, each file has a name, type, mount path, and schema
    files: List[FileDef] = Field(..., description="List of files")

    # container definition
    container: ContainerDef = Field(..., description="Container definition")


class AppSpec(BaseModel):
    name: str = Field(..., description="Name of the app")
    description: str = Field(..., description="Description of the app")
    tasks: List[TaskSpec] = Field(..., description="List of tasks")
