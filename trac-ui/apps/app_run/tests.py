from apps.app_run.forms import create_form_from_parameter_schema
from apps.data_gateway.models import DataSet
from apps.trac_app.models import AppDefinition, AppInstance
from django.test import SimpleTestCase, TestCase
from trac.schema.task import ParameterDef


class TestAppRunForm(TestCase):
    def setUp(self):
        # create an app definition
        app_def = AppDefinition.objects.create(
            name="test_app",
            image_name="test_app",
            image_tag="latest",
            description="test app",
        )

        # create an app instance
        app_inst = AppInstance.objects.create(name="test_instance", app=app_def)

        # create a dataset
        DataSet.objects.create(name="test_dataset", app=app_inst)

    def test_create_form_from_parameter_schema(self):
        """
        Test the dynamic form creation
        """

        params = [
            ParameterDef(name="param1", type="string", default="default1"),
            ParameterDef(name="param2", type="integer", default=2),
            ParameterDef(name="param3", type="number", default=3.0),
            ParameterDef(name="param4", type="boolean", default=True),
        ]

        form_class = create_form_from_parameter_schema(params, 1)

        form = form_class()

        # test the form fields
        self.assertEqual(form.fields["param1"].initial, "default1")
        self.assertEqual(form.fields["param2"].initial, 2)
        self.assertEqual(form.fields["param3"].initial, 3.0)
        self.assertEqual(form.fields["param4"].initial, True)

        # test the form validation
        data = {
            "name": "test",
            "description": "test",
            "dataset": 1,
            "param1": "test1",
            "param2": 2,
            "param3": 3.0,
            "param4": True,
        }

        filled_form = form_class(data=data)

        # print the form errors
        print(filled_form.errors)
        self.assertTrue(filled_form.is_valid())
