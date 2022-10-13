from trac_runtime.executors.k8s import JOB_STATUS, K8sExecutor


def test_k8s_executor(task_spec, run_config):
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
    assert outputs["file2"] == b"hello worldhello world\n"

    executor.delete(job_handle)
