import pytest
from trac_runtime.executors.docker import JOB_STATUS, LocalDockerExecutor


def test_docker_executor(task_spec, run_config):

    executor = LocalDockerExecutor(task_spec, run_config)
    job_handle = executor.submit()
    assert job_handle

    # wait for the task to finish
    while True:
        status = executor.get_status(job_handle)
        if status == JOB_STATUS.SUCCESS:
            break
    output = executor.get_output(job_handle)
    assert output["file2"] == b"hello worldhello world\n"

    logs = executor.get_logs(job_handle)
    assert logs

    executor.delete(job_handle)


def test_docker_executor_failed_job(failed_task_spec, run_config):

    executor = LocalDockerExecutor(failed_task_spec, run_config)
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

    executor.delete(job_handle)
