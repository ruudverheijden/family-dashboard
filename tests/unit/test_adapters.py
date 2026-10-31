import pytest

from app.integrations import common as integrations


@pytest.mark.parametrize(
    "new_url",
    [
        "http://other.test/dav",
        "http://old.test:8080/dav",
        "https://old.test/dav",
        "http://old.test/proxy",
    ],
)
def test_saved_secret_is_bound_to_address(new_url):
    old = "http://old.test/dav"
    with pytest.raises(ValueError):
        integrations.endpoint_secret(old, new_url, "old-secret", "")
    assert integrations.endpoint_secret(old, new_url, "old-secret", "replacement") == "replacement"


def test_trailing_slash_can_reuse_secret():
    assert (
        integrations.endpoint_secret(
            "https://example.test/dav/", "https://example.test/dav", "saved", ""
        )
        == "saved"
    )


def test_removing_endpoint_also_forgets_credential():
    assert integrations.endpoint_secret("https://example.test", "", "saved", "") == ""
