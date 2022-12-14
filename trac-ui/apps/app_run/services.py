import csv
import io
import logging
import tempfile
import time
import uuid
from typing import Dict, List

from trac.runtime.run import JOB_STATUS, RunConfig, get_output, get_status, submit
from trac.schema.task import FileDef

from ..data_gateway.models import DataSet, Resource
from ..data_gateway.services.gsheet import GoogleSheetsDataBackend
from ..trac_app.models import AppDefinition, AppInstance
from .models import AppRun

LOG = logging.getLogger(__name__)


def pull_data_to_local_tempdir(dataset: DataSet, tempdir) -> Dict[str, str]:
    """
    Pull the data files to a local temp dir
    Return a dict of file_name: file_path
    """

    input_schema: List[FileDef] = dataset.schema["input_schema"]
    result = {}

    if dataset.backend == "db":
        # get the data from the db
        for file_def in input_schema:
            resource_type = file_def.name

            # get the data from the db
            resources = dataset.resources.filter(resource_type=resource_type)
            file_name = resource_type + ".csv"

            LOG.info(f"Writing {file_name} to {tempdir}")

            with open(tempdir + "/" + file_name, "w") as f:
                writer = csv.DictWriter(
                    f, fieldnames=file_def.file_schema["properties"].keys()
                )
                writer.writeheader()
                writer.writerows([resource.value for resource in resources])

            LOG.info(f"Number of rows: {len(resources)}")

            result[resource_type] = tempdir + "/" + file_name

    elif dataset.backend == "gsheet":
        # get the data from the gsheet
        records = GoogleSheetsDataBackend.read_spreadsheet(dataset.url)

        for file_def in input_schema:
            resource_type = file_def.name

            resources = records[resource_type]

            file_name = resource_type + ".csv"
            LOG.info(f"Writing {file_name} to {tempdir}")

            with open(tempdir + "/" + file_name, "w") as f:
                writer = csv.DictWriter(
                    f, fieldnames=file_def.file_schema["properties"].keys()
                )
                writer.writeheader()
                writer.writerows(resources)

            LOG.info(f"Number of rows: {len(resources)}")

            result[resource_type] = tempdir + "/" + file_name

    else:
        raise Exception("Unknown backend")

    return result


def run_app(
    app_run: AppRun,
) -> str:
    """
    Trigger a runtime job for an app run
    """

    parameters = app_run.parameters
    dataset = app_run.dataset

    # get the app_def from the instance_id
    app = AppInstance.objects.get(id=app_run.app.id)
    app_def = app.app

    # get the task spec
    task_spec = app_def.task_spec()

    # pull the dataset files to a local temp folder
    tempdir = tempfile.mkdtemp()
    file_mapping = pull_data_to_local_tempdir(dataset, tempdir)

    # create a runconfig object
    run_config = RunConfig(
        parameters=parameters,
        input_files=file_mapping,
    )

    job_handle = submit(
        task_spec=task_spec,
        run_config=run_config,
        backend="docker",
    )

    print(job_handle)

    return job_handle


def wait_for_job_completion(job_handle):
    """
    Wait till the job to be finished, either succeed or failed
    """
    # TODO: hardcoded timeout
    for _ in range(10):
        status = get_status(job_handle)
        LOG.info(f"Job status: {status}")
        if status == JOB_STATUS.SUCCESS:
            return job_handle
        elif status == JOB_STATUS.FAILED:
            raise Exception("Job failed")
        else:
            time.sleep(1)


def fetch_job_output(app_run: AppRun) -> DataSet:
    """
    Fetch the output files from the job
    Create a DataSet object that holds the contents
    """

    # get the app_def from the instance_id
    app = AppInstance.objects.get(id=app_run.app.id)
    app_def = app.app

    task_spec = app_def.task_spec()

    job_handle = app_run.job_handle

    output = get_output(
        job_handle=job_handle,
        task_spec=task_spec,
        backend="docker",
    )

    # get the output schema
    output_schema: List[FileDef] = app_run.dataset.schema["output_schema"]
    data_backend = app_run.dataset.backend

    output_dataset = DataSet(
        name=app_run.name + "_output",
        schema=app_run.dataset.schema,
        backend=data_backend,
        app=app,
    )

    # parse output as a list of dicts
    resource_map = {}
    for file_def in output_schema:
        resource_type = file_def.name

        contents = output[resource_type]
        # parse the contents as a csv in bytes format
        contents = io.StringIO(contents.decode("utf-8"))
        reader = csv.DictReader(contents, delimiter=",")
        records = [row for row in reader]

        resource_map[resource_type] = records

    if data_backend == "db":
        # save the resources to db in bulk
        for resource_type, records in resource_map.items():
            Resource.objects.bulk_create(
                [
                    Resource(
                        dataset=output_dataset,
                        resource_type=resource_type,
                        value=record,
                    )
                    for record in records
                ]
            )
    elif data_backend == "gsheet":
        uniq_identifier = str(uuid.uuid4())[:8]
        spreadsheet_name = output_dataset.name + "_" + uniq_identifier
        sheet_url = GoogleSheetsDataBackend.init_spreadsheet(
            spreadsheet_name=spreadsheet_name,
            schemas=output_schema,
        )

        # fill in the data
        for resource_type, records in resource_map.items():
            GoogleSheetsDataBackend.write_records(
                spreadsheet_url=sheet_url,
                worksheet_name=resource_type,
                records=records,
            )

        output_dataset.url = sheet_url
        output_dataset.initialized = True

    else:
        raise Exception("Unknown backend")

    output_dataset.save()

    # return the new dataset
    return output_dataset
