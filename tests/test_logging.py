import json
import logging

from app.logging_config import JsonFormatter

def test_json_formatter_outputs_valid_json():
    record = logging.LogRecord("t", logging.INFO, "f.py", 1, "hello", None, None)
    record.extra_fields = {"status": 200}
    data = json.loads(JsonFormatter().format(record))
    assert data["message"] == "hello"
    assert data["level"] == "INFO"
    assert data["status"] == 200

def test_response_has_request_id_header(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert len(response.headers["X-Request-ID"]) == 36