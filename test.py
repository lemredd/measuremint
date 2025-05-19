from main import hx, app
from unittest import TestCase

from fastapi.testclient import TestClient


class HxApplicationTest(TestCase):
    client = TestClient(hx)

    def test_forbidden_access(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 403)

    def test_documentation(self):
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)

    def test_suggest_units(self):
        response = self.client.get("/suggestions", headers={"HX-Request": "true"})
        self.assertEqual(response.status_code, 200)

    def test_undefined_units(self):
        response = self.client.post(
            "/convert",
            headers={"HX-Request": "true"},
            data={"quantity": 1, "from_unit": "foo", "to_unit": "bar"},
        )
        self.assertEqual(response.status_code, 422)

    def test_incompatible_conversions(self):
        response = self.client.post(
            "/convert",
            headers={"HX-Request": "true"},
            data={"quantity": 1, "from_unit": "second", "to_unit": "meter"},
        )
        self.assertEqual(response.status_code, 422)


class JsonApplicationTest(TestCase):
    client = TestClient(app)
    endpoint = "/json/convert"

    def test_undefined_units(self):
        from_unit = "foo"
        to_unit = "bar"
        json = {
            "quantity": 1,
            "from_unit": from_unit,
            "to_unit": to_unit,
        }
        response = self.client.post(self.endpoint, json=json)
        self.assertEqual(response.status_code, 422)
