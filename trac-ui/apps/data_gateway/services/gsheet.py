# code to interact with google sheets API
import logging
from typing import List

import gspread
from trac.schema.task import FileDef, TaskDef

LOG = logging.getLogger(__name__)


class GoogleSheetsDataBackend:

    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = gspread.service_account()
        return cls._client

    @classmethod
    def init_spreadsheet(cls, schemas: List[FileDef], spreadsheet_name):
        """
        Initialize a spreadsheet according to schemas.
        Each element of schemas is a jsonschema describing a resource
        """
        client = cls.get_client()

        # check if spreadsheet already exists
        try:
            spreadsheet = client.open(spreadsheet_name)
            LOG.warning(
                f"The spreadsheet {spreadsheet_name} already exists. Skip initialization."
            )

            return spreadsheet.url
        except gspread.exceptions.SpreadsheetNotFound:
            spreadsheet = client.create(spreadsheet_name)

        for schema in schemas:
            cls.init_worksheet(spreadsheet, schema)

        # share the spreadsheet with the user
        # TODO: this is hardcoded for the testing user now
        spreadsheet.share("dayeye2006@gmail.com", perm_type="user", role="writer")
        # return the spreadsheet url
        return spreadsheet.url

    @classmethod
    def init_worksheet(cls, spreadsheet, schema: FileDef):
        """
        Initialize a worksheet according to a schema
        """
        ncols = len(schema.file_schema["properties"])
        nrows = 1  # header
        title = schema.name
        worksheet = spreadsheet.add_worksheet(title=title, rows=nrows, cols=ncols)
        # set headers
        headers = list(schema.file_schema["properties"].keys())
        # write the hedder row
        worksheet.update("A1", [headers])
        return worksheet

    @classmethod
    def read_spreadsheet(cls, spreadsheet_url):
        """
        Read a spreadsheet and return all data as a dictionary
        """
        spreadsheet = cls.get_client().open_by_url(spreadsheet_url)
        worksheets = spreadsheet.worksheets()

        data = {}
        for worksheet in worksheets:
            data[worksheet.title] = worksheet.get_all_records()

        return data
