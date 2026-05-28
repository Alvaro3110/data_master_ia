from app.main import app


def test_ask_analytics_openapi_uses_envelope_schema() -> None:
    schema = app.openapi()
    response_schema = schema["paths"]["/api/v1/ask-analytics"]["post"]["responses"]["200"]["content"][
        "application/json"
    ]["schema"]
    assert "$ref" in response_schema
    assert "AskEnvelopeResponse" in response_schema["$ref"]
