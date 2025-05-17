from main import hx
from unittest import TestCase

from fastapi.testclient import TestClient


class HxApplicationTest(TestCase):
    client = TestClient(hx)

    def test_forbidden_access(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 403)

    def test_suggest_units(self):
        response = self.client.get("/suggestions", headers={"HX-Request": "true"})
        self.assertEqual(response.status_code, 200)
