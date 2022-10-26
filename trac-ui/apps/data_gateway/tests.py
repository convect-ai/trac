import json

from apps.data_gateway.models import FileDefListDecoder, FileDefListEncoder
from django.test import SimpleTestCase
from trac.schema.task import FILE_TYPE, FileDef


class SchemaUtilsTestCase(SimpleTestCase):
    def test_encode_schema(self):
        schema = {
            "input_schema": [
                FileDef(
                    name="input_file",
                    description="input file",
                    type=FILE_TYPE.INPUT,
                    mount_path="/input",
                    file_schema={
                        "type": "object",
                        "properties": {
                            "some_property": {"type": "string"},
                        },
                    },
                )
            ],
            "output_schema": [
                FileDef(
                    name="output_file",
                    description="output file",
                    type=FILE_TYPE.OUTPUT,
                    mount_path="/output",
                    file_schema={
                        "type": "object",
                        "properties": {
                            "some_property": {"type": "string"},
                        },
                    },
                )
            ],
        }
        encoder = FileDefListEncoder()
        encoded = encoder.encode(schema)

        expected_encoded_schema = {
            "input_schema": [
                {
                    "name": "input_file",
                    "description": "input file",
                    "type": "input",
                    "mount_path": "/input",
                    "file_schema": {
                        "type": "object",
                        "properties": {
                            "some_property": {"type": "string"},
                        },
                    },
                }
            ],
            "output_schema": [
                {
                    "name": "output_file",
                    "description": "output file",
                    "type": "output",
                    "mount_path": "/output",
                    "file_schema": {
                        "type": "object",
                        "properties": {
                            "some_property": {"type": "string"},
                        },
                    },
                }
            ],
        }

        self.assertDictEqual(json.loads(encoded), expected_encoded_schema)

    def test_decode_schema(self):

        schema = {
            "input_schema": [
                {
                    "name": "input_file",
                    "description": "input file",
                    "type": "input",
                    "mount_path": "/input",
                    "file_schema": {
                        "type": "object",
                        "properties": {
                            "some_property": {"type": "string"},
                        },
                    },
                }
            ],
            "output_schema": [
                {
                    "name": "output_file",
                    "description": "output file",
                    "type": "output",
                    "mount_path": "/output",
                    "file_schema": {
                        "type": "object",
                        "properties": {
                            "some_property": {"type": "string"},
                        },
                    },
                }
            ],
        }

        schema = json.dumps(schema)

        decoder = FileDefListDecoder()
        decoded = decoder.decode(schema)

        expected_decoded_schema = {
            "input_schema": [
                FileDef(
                    name="input_file",
                    description="input file",
                    type=FILE_TYPE.INPUT,
                    mount_path="/input",
                    file_schema={
                        "type": "object",
                        "properties": {
                            "some_property": {"type": "string"},
                        },
                    },
                )
            ],
            "output_schema": [
                FileDef(
                    name="output_file",
                    description="output file",
                    type=FILE_TYPE.OUTPUT,
                    mount_path="/output",
                    file_schema={
                        "type": "object",
                        "properties": {
                            "some_property": {"type": "string"},
                        },
                    },
                )
            ],
        }

        self.assertDictEqual(decoded, expected_decoded_schema)
