import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Si boto3 o urllib3 no están instalados en el entorno local, creamos un mock en sys.modules
if "boto3" not in sys.modules:
    mock_boto3 = MagicMock()
    sys.modules["boto3"] = mock_boto3

if "urllib3" not in sys.modules:
    mock_urllib3 = MagicMock()
    sys.modules["urllib3"] = mock_urllib3

# Importación dinámica de handlers desde sus respectivos directorios
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG_DIR = os.path.join(BASE_DIR, "lambda-catalog")
CONSUMER_DIR = os.path.join(BASE_DIR, "lambda-consumer")

import importlib.util

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

catalog_handler = load_module("catalog_handler", os.path.join(CATALOG_DIR, "handler.py"))
consumer_handler = load_module("consumer_handler", os.path.join(CONSUMER_DIR, "handler.py"))


class TestServerlessCoworking(unittest.TestCase):

    def setUp(self):
        catalog_handler.events_client = None

    def test_catalog_health_endpoint(self):
        """Verifica que el endpoint /health del catálogo responda HTTP 200."""
        event = {
            "httpMethod": "GET",
            "path": "/health",
            "requestContext": {"http": {"method": "GET", "path": "/health"}},
        }
        res = catalog_handler.lambda_handler(event, None)
        self.assertEqual(res["statusCode"], 200)
        body = json.loads(res["body"])
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["service"], "lambda-catalog-service")

    def test_catalog_list_spaces(self):
        """Verifica que el listado de espacios retorne la lista de salas."""
        event = {
            "httpMethod": "GET",
            "path": "/spaces",
            "requestContext": {"http": {"method": "GET", "path": "/spaces"}},
        }
        res = catalog_handler.lambda_handler(event, None)
        self.assertEqual(res["statusCode"], 200)
        body = json.loads(res["body"])
        self.assertIsInstance(body, list)
        self.assertGreater(len(body), 0)

    def test_catalog_get_space_by_id(self):
        """Verifica la consulta de un espacio específico por ID."""
        event = {
            "httpMethod": "GET",
            "path": "/spaces/1",
            "pathParameters": {"id": "1"},
        }
        res = catalog_handler.lambda_handler(event, None)
        self.assertEqual(res["statusCode"], 200)
        body = json.loads(res["body"])
        self.assertEqual(body["id"], 1)
        self.assertIn("price_per_hour", body)

    def test_catalog_update_availability_publishes_eventbridge(self):
        """Verifica que al actualizar disponibilidad se emita un evento a EventBridge."""
        mock_events = MagicMock()
        mock_events.put_events.return_value = {"FailedEntryCount": 0, "Entries": [{"EventId": "evt-123"}]}
        catalog_handler.events_client = mock_events

        event = {
            "httpMethod": "PATCH",
            "path": "/spaces/1/availability",
            "pathParameters": {"id": "1"},
            "body": json.dumps({"available": False}),
        }

        res = catalog_handler.lambda_handler(event, None)
        self.assertEqual(res["statusCode"], 200)
        body = json.loads(res["body"])
        self.assertFalse(body["space"]["available"])

        # Verificar que se llamó a EventBridge
        mock_events.put_events.assert_called_once()
        call_args = mock_events.put_events.call_args[1]["Entries"][0]
        self.assertEqual(call_args["Source"], "coworking.catalog")
        self.assertEqual(call_args["DetailType"], "SpaceChanged")

        detail = json.loads(call_args["Detail"])
        self.assertEqual(detail["space_id"], 1)
        self.assertFalse(detail["current_availability"])

    def test_consumer_processes_sqs_event(self):
        """Verifica que el consumer procese correctamente un lote de mensajes SQS con envelope de EventBridge."""
        sample_path = os.path.join(BASE_DIR, "events", "sqs_sample.json")
        with open(sample_path, "r", encoding="utf-8") as f:
            sqs_event = json.load(f)

        res = consumer_handler.lambda_handler(sqs_event, None)
        self.assertEqual(res["statusCode"], 200)
        self.assertEqual(res["processed_count"], 1)
        self.assertEqual(len(res["batchItemFailures"]), 0)


if __name__ == "__main__":
    unittest.main()
