# defines the base class for all executors
from abc import ABC, abstractmethod
from enum import Enum


class JOB_STATUS(Enum):
    """
    Job status enumeration
    """

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class BaseExecutor(ABC):
    def __init__(self, task_spec, run_config):
        """
        Constructor
        """
        self.task_spec = task_spec
        self.run_config = run_config

        self.compiled_task = None

    @abstractmethod
    def compile(self):
        """
        Compile the task specification into a executor specific format
        """

    @abstractmethod
    def submit(self):
        """
        Submit the compiled task to the executor
        """

    @abstractmethod
    def preprocess(self):
        """
        Prepare the input files for the task
        """

    @abstractmethod
    def get_status(self, job_handle):
        """
        Get the status of the task
        """

    @abstractmethod
    def get_output(self, job_handle):
        """
        Get the output of the task
        """

    @abstractmethod
    def get_logs(self, job_handle):
        """
        Get the logs of the task
        """

    @abstractmethod
    def cancel(self, job_handle):
        """
        Cancel the task
        """
