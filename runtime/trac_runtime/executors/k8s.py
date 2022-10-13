import logging
import os
import random
import string
import tempfile

import kubernetes as k8s

from ..schema import FILE_TYPE, RunConfig, TaskDef
from .base import JOB_STATUS, BaseExecutor

LOG = logging.getLogger(__name__)


class K8sExecutor(BaseExecutor):
    """
    Executor for running tasks on kubernetes, as job resources
    """

    def __init__(self, task_spec, run_config, **kwargs):
        super().__init__(task_spec, run_config)
        # initialize kubernetes client
        k8s.config.load_kube_config()
        self.k8s_client = k8s.client

    def compile(self):
        """
        For the compile step, we generate a kubernetes job spec
        """
        # generate a unique identifier for the job, 6 random characters
        identifier = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=6)
        )
        job_name = self.task_spec.name + "-" + identifier

        job_spec = self.k8s_client.V1Job()
        # use generated name to avoid name conflict
        job_spec.metadata = self.k8s_client.V1ObjectMeta(
            name=job_name,
            labels={
                "owned_by": job_name,
                "app": "trac",
            },
        )
        # set the spec of the job
        job_spec.spec = self.k8s_client.V1JobSpec(
            template=self.k8s_client.V1PodTemplateSpec(
                spec=self.k8s_client.V1PodSpec(
                    containers=[
                        self.k8s_client.V1Container(
                            name=self.task_spec.name,
                            image=self.task_spec.container.image,
                            command=self.task_spec.container.command,
                            args=self.task_spec.container.args,
                            env=[
                                self.k8s_client.V1EnvVar(
                                    name=env[0],
                                    value=env[1],
                                )
                                for env in self.task_spec.container.envs
                            ],
                            volume_mounts=[],
                        )
                    ],
                    volumes=[],
                ),
            ),
        )
        # set restart policy to never, so that the job will not restart if it fails
        job_spec.spec.template.spec.restart_policy = "Never"

        # log the job spec for debugging
        LOG.debug("Job spec: %s", job_spec.to_dict())

        return job_spec

    def submit(self):
        """
        For submit step, we create a kubernetes job as specified by compiled_task
        and return its id as job handle
        """
        self.compile()
        self.preprocess()
        job_spec = self.compiled_task
        # create the job
        job = self.k8s_client.BatchV1Api().create_namespaced_job(
            namespace="default",
            body=job_spec,
        )
        return job.metadata.name

    def preprocess(self):
        """
        For preprocess step, we create a kubernetes configmap that contains all the
        parameter files as specified by task_spec, and later mount it to the job


        For input files, we create a configmap that contains all the file contents, and mount it to the job
        (THIS IS QUITE HACKY, NEED TO FIND A BETTER WAY)
        """
        # check if compile has been called
        if not self.compiled_task:
            self.compiled_task = self.compile()
        compiled_task = self.compiled_task

        # create a configmap for parameters
        parameters = self.run_config.parameters
        # convert all the parameters to string
        # TODO: need to handle the composite types
        parameters = {k: str(v) for k, v in parameters.items()}
        param_config_map = self.k8s_client.V1ConfigMap(
            metadata=self.k8s_client.V1ObjectMeta(
                generate_name=self.task_spec.name + "-param-",
                labels={
                    "owned_by": compiled_task.metadata.name,
                    "app": "trac",
                },
            ),
            data={k: v for k, v in parameters.items()},
        )

        param_config_map = self.k8s_client.CoreV1Api().create_namespaced_config_map(
            namespace="default",
            body=param_config_map,
        )

        input_files = [f for f in self.task_spec.files if f.type == FILE_TYPE.INPUT]
        # get the location of the input files from run_config
        for f in input_files:
            # TODO: when the output file is located under the same directory as the input file
            # it will be read only, we need to fix the permission
            file_path_on_host = self.run_config.input_files[f.name]
            print(f)
            # read the file content and save it to the configmap
            with open(file_path_on_host, "r") as file_on_host:
                # create a configmap for input files
                input_file_config_map = self.k8s_client.V1ConfigMap(
                    metadata=self.k8s_client.V1ObjectMeta(
                        generate_name=self.task_spec.name + "-input-",
                        labels={
                            "owned_by": compiled_task.metadata.name,
                            "app": "trac",
                        },
                    ),
                    data={f.name: file_on_host.read()},
                )

                input_file_config_map = (
                    self.k8s_client.CoreV1Api().create_namespaced_config_map(
                        namespace="default",
                        body=input_file_config_map,
                    )
                )

                # mount the configmap to the job, and set the file path to the file.mount_path
                compiled_task.spec.template.spec.volumes.append(
                    self.k8s_client.V1Volume(
                        name=f.name,
                        config_map=self.k8s_client.V1ConfigMapVolumeSource(
                            name=input_file_config_map.metadata.name,
                        ),
                    )
                )

                # for the mount_path, since the key of the configmap is the file name, we use the directory of the mount_path as the mount_path
                compiled_task.spec.template.spec.containers[0].volume_mounts.append(
                    self.k8s_client.V1VolumeMount(
                        name=f.name,
                        mount_path=f.mount_path,
                        sub_path=f.name,
                    )
                )

        # mount the configmap to the job
        compiled_task.spec.template.spec.volumes.append(
            self.k8s_client.V1Volume(
                name="parameters",
                config_map=self.k8s_client.V1ConfigMapVolumeSource(
                    name=param_config_map.metadata.name,
                ),
            )
        )

        compiled_task.spec.template.spec.containers[0].volume_mounts.append(
            self.k8s_client.V1VolumeMount(
                name="parameters",
                mount_path="/parameters.json",
            )
        )

        return compiled_task

    def get_status(self, job_handle):
        """
        Given a job handle (in this case, the name of the kubernetes job), get the status of the job
        """
        status = (
            self.k8s_client.BatchV1Api()
            .read_namespaced_job_status(
                name=job_handle,
                namespace="default",
            )
            .status
        )
        if status.succeeded == 1:
            return JOB_STATUS.SUCCESS
        elif status.failed == 1:
            return JOB_STATUS.FAILED
        else:
            return JOB_STATUS.RUNNING

    def get_output(self, job_handle):
        """
        Get the content of the output files as specified by task_spec from the job pod
        and return it as a dictionary
        """
        raise NotImplementedError

    def get_logs(self, job_handle):
        """
        Given a job handle (in this case, the name of the kubernetes job), get the logs of the job
        """
        # find the pod name of the job
        pod_name = (
            self.k8s_client.CoreV1Api()
            .list_namespaced_pod(
                namespace="default",
                label_selector="job-name=" + job_handle,
            )
            .items[0]
            .metadata.name
        )
        # get the logs of the pod
        logs = self.k8s_client.CoreV1Api().read_namespaced_pod_log(
            name=pod_name,
            namespace="default",
        )
        return logs

    def cancel(self, job_handle):
        """
        Given a job handle (in this case, the name of the kubernetes job), cancel the job
        """
        job = self.k8s_client.BatchV1Api().read_namespaced_job(
            name=job_handle,
            namespace="default",
        )
        job.spec.active_deadline_seconds = 0
        self.k8s_client.BatchV1Api().replace_namespaced_job(
            name=job_handle,
            namespace="default",
            body=job,
        )

    def delete(self, job_handle):
        """
        Given a job handle (in this case, the name of the kubernetes job), delete the job
        """
        job = self.k8s_client.BatchV1Api().read_namespaced_job(
            name=job_handle,
            namespace="default",
        )
        self.k8s_client.BatchV1Api().delete_namespaced_job(
            name=job_handle,
            namespace="default",
        )

        # delete the configmaps with label owned_by = job_handle
        configmaps = self.k8s_client.CoreV1Api().list_namespaced_config_map(
            namespace="default",
            label_selector="owned_by=" + job_handle,
        )
        for configmap in configmaps.items:
            LOG.info(f"Deleting configmap {configmap.metadata.name}")
            self.k8s_client.CoreV1Api().delete_namespaced_config_map(
                name=configmap.metadata.name,
                namespace="default",
            )
