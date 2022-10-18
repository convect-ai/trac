import pytest
from trac.runtime.base import JOB_STATUS
from trac.runtime.docker import LocalDockerExecutor
from trac.schema.task import FILE_TYPE, RunConfig, TaskDef


def test_docker_executor(task_spec, run_config):

    task_spec = TaskDef.parse_obj(task_spec)
    run_config = RunConfig.parse_obj(run_config)

    executor = LocalDockerExecutor(task_spec, run_config)
    job_handle = executor.submit()
    assert job_handle

    # wait for the task to finish
    while True:
        status = executor.get_status(job_handle)
        if status == JOB_STATUS.SUCCESS:
            break
    output = executor.get_output(job_handle)
    assert output["file2"] == b"hello world"

    logs = executor.get_logs(job_handle)
    assert logs

    executor.cleanup(job_handle)


def test_docker_executor_failed_job(task_spec_will_fail, run_config):

    task_spec = TaskDef.parse_obj(task_spec_will_fail)
    run_config = RunConfig.parse_obj(run_config)

    executor = LocalDockerExecutor(task_spec, run_config)
    job_handle = executor.submit()
    assert job_handle

    # wait for the task to finish
    while True:
        status = executor.get_status(job_handle)
        if status == JOB_STATUS.FAILED:
            break

    # get the output should raise an exception
    with pytest.raises(Exception):
        executor.get_output(job_handle)

    logs = executor.get_logs(job_handle)
    assert logs

    executor.cleanup(job_handle)
