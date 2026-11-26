import io
import json
from unittest.mock import patch

import pytest

from terra_client import TerraClient


def response(content, status="completed"):
    return io.BytesIO(
        json.dumps(
            {
                "status": status,
                "model": "mock",
                "output": [{"type": "message", "content": content}],
            }
        ).encode()
    )


def test_valid_response_and_request_has_no_storage_or_tools():
    with patch(
        "urllib.request.urlopen",
        return_value=response(
            [{"type": "output_text", "text": '{"polarity":"neutral"}'}]
        ),
    ) as call:
        label, meta = TerraClient(
            "test-secret", "https://example.invalid/v1"
        ).sentiment("fictional")
    assert label == "neutral" and meta["reported_model"] == "mock"
    body = json.loads(call.call_args.args[0].data)
    assert body["store"] is False and "tools" not in body
    assert body["model"] == "gpt-6.1-terra"


@pytest.mark.parametrize(
    "content,status",
    [
        ([{"type": "refusal", "refusal": "no"}], "completed"),
        ([{"type": "output_text", "text": '{"polarity":"neutral"}'}], "incomplete"),
        ([{"type": "output_text", "text": '{"polarity":"diagnosis"}'}], "completed"),
        (
            [{"type": "output_text", "text": '{"polarity":"neutral","extra":1}'}],
            "completed",
        ),
    ],
)
def test_bad_response_is_not_accepted(content, status):
    with patch("urllib.request.urlopen", return_value=response(content, status)):
        with pytest.raises(ValueError):
            TerraClient("test-secret", "https://example.invalid/v1").sentiment(
                "fictional"
            )
