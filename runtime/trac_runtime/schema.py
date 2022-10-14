# defines the schema for task specifications


from enum import Enum
from typing import Any, Dict, List, Tuple

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
    command: List[str]
    args: List[str]
    # envs, a list of (name, value) pairs
    envs: List[Tuple[str, str]] = []


class TaskDef(BaseModel):
    name: str = Field(..., description="Name of the task")
    description: str = Field(..., description="Description of the task")

    parameters: ParametersSpec = Field(None, description="Parameters for the task")

    files: FilesSpec = Field(None, description="Files for the task")

    # container definition
    container: ContainerSpec = Field(..., description="Container definition")


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
