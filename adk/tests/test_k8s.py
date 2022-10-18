from trac.runtime.k8s import JOB_STATUS, K8sExecutor
from trac.schema.task import RunConfig, TaskDef


def test_k8s_executor(task_spec, run_config):
    task_spec = TaskDef.parse_obj(task_spec)
    run_config = RunConfig.parse_obj(run_config)

    executor = K8sExecutor(task_spec, run_config)
    job_handle = executor.submit()
    assert job_handle

    # wait for the task to finish
    while True:
        status = executor.get_status(job_handle)
        if status == JOB_STATUS.SUCCESS:
            break

    logs = executor.get_logs(job_handle)
    assert logs

    outputs = executor.get_output(job_handle)
    assert outputs["file2"] == b"hello world"

    executor.cleanup(job_handle)
