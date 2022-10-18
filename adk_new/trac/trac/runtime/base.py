# runtime takes care of the actual execution of the app image

from abc import ABC, abstractmethod
from enum import Enum

from ..schema import RunConfig, TaskDef


class JOB_STATUS(Enum):
    """
    Job status enumeration
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class BaseExecutor(ABC):
    def __init__(self, task_spec: TaskDef, run_config: RunConfig) -> None:
        """
        Constructor
        """
        self.task_spec = task_spec
        self.run_config = run_config
        self.compiled_task = None

        self.validate()

    def validate(self):
        """
        Validate if run_config is valid for task_spec
        """
        # check if the parameters provided in run_config comply with the task_spec
        for param in self.run_config.parameters:
            # find the parameter definition in task_spec
            param_def = None
            for param_def in self.task_spec.parameter.parameters:
                if param_def.name == param:
                    break

            if param_def is None:
                raise Exception(f"Parameter {param} not found in task_spec")

            # check if the type is correct
            actual_type = type(self.run_config.parameters[param])
            expected_type = param_def.type
            # map the expected type to python type
            if expected_type == "integer":
                expected_type = int
            elif expected_type == "number":
                expected_type = float
            elif expected_type == "float":
                expected_type = float
            elif expected_type == "string":
                expected_type = str
            elif expected_type == "boolean":
                expected_type = bool
            else:
                raise Exception(f"Unknown parameter type {expected_type}")

            if actual_type != expected_type:
                msg = f"Parameter {param} has type {actual_type}, expected {expected_type}"
                raise Exception(msg)

        # check if the input files provided in run_config comply with the task_spec
        for file in self.run_config.input_files:
            # find the file definition in task_spec
            file_def = None
            for file_def in self.task_spec.io.files:
                if file_def.name == file:
                    break

            if file_def is None:
                raise Exception(f"Input file {file} not found in task_spec")

        # task_spec should always have container field defined since
        # the spec is processed by the compiler, so the handler field
        # is translated to container field
        if self.task_spec.container is None:
            raise Exception("task_spec.container is not defined")

        return True

    @abstractmethod
    def compile(self) -> None:
        """
        Compile the task specification into a executor specific format
        """

    @abstractmethod
    def submit(self) -> None:
        """
        Submit the compiled task to the executor
        """

    @abstractmethod
    def preprocess(self) -> None:
        """
        Prepare the input files for the task
        """

    @abstractmethod
    def get_status(self, job_handle: str) -> JOB_STATUS:
        """
        Get the status of the task
        """

    @abstractmethod
    def get_output(self, job_handle: str) -> None:
        """
        Get the output of the task
        """

    @abstractmethod
    def get_logs(self, job_handle: str) -> None:
        """
        Get the logs of the task
        """

    @abstractmethod
    def cancel(self, job_handle: str) -> None:
        """
        Cancel the task
        """

    @abstractmethod
    def cleanup(self, job_handle: str) -> None:
        """
        Cleanup the task
        """
