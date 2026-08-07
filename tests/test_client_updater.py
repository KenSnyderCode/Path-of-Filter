import hashlib
import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from client_updater.updater import run_update

LOGGER = logging.getLogger("test")


def _mock_response(json_data=None, content=None):
    response = Mock()
    response.raise_for_status = Mock()
    if json_data is not None:
        response.json = Mock(return_value=json_data)
    if content is not None:
        response.content = content
    return response


def test_run_update_installs_when_no_local_state(tmp_path):
    content = b"# a fake filter\n"
    sha256 = hashlib.sha256(content).hexdigest()
    manifest = {"sha256": sha256, "version": "abc123", "league": "Test League", "generatedAtUtc": "now"}

    install_path = tmp_path / "CommunityAutoFilter.filter"
    state_path = tmp_path / "state.json"

    with patch("client_updater.updater.requests.get") as mock_get:
        mock_get.side_effect = [_mock_response(json_data=manifest), _mock_response(content=content)]
        updated = run_update("http://example/manifest.json", "http://example/filter", install_path, state_path, LOGGER)

    assert updated is True
    assert install_path.read_bytes() == content
    assert state_path.exists()


def test_run_update_skips_when_already_current(tmp_path):
    content = b"# already installed\n"
    sha256 = hashlib.sha256(content).hexdigest()
    manifest = {"sha256": sha256, "version": "abc123", "league": "Test League", "generatedAtUtc": "now"}

    install_path = tmp_path / "CommunityAutoFilter.filter"
    install_path.write_bytes(content)
    state_path = tmp_path / "state.json"
    state_path.write_text(f'{{"sha256": "{sha256}"}}', encoding="utf-8")

    with patch("client_updater.updater.requests.get") as mock_get:
        mock_get.side_effect = [_mock_response(json_data=manifest)]
        updated = run_update("http://example/manifest.json", "http://example/filter", install_path, state_path, LOGGER)

    assert updated is False
    mock_get.assert_called_once()  # only the manifest was fetched, never the (unchanged) filter body


def test_run_update_rejects_hash_mismatch(tmp_path):
    manifest = {"sha256": "deadbeef" * 8, "version": "abc123", "league": "Test League"}
    install_path = tmp_path / "CommunityAutoFilter.filter"
    state_path = tmp_path / "state.json"

    with patch("client_updater.updater.requests.get") as mock_get:
        mock_get.side_effect = [_mock_response(json_data=manifest), _mock_response(content=b"wrong content")]
        with pytest.raises(RuntimeError, match="does not match manifest"):
            run_update("http://example/manifest.json", "http://example/filter", install_path, state_path, LOGGER)

    assert not install_path.exists()
