import os
import sys
from unittest.mock import Mock, patch

sys.path.append(os.getcwd())

from core.sources.apkpure import APKPureSource


def test_apkpure_builds_direct_url():
    source = APKPureSource(file_type="xapk", version="latest")
    url = source._build_direct_url("com.example.app")
    assert url == "https://d.apkpure.com/b/XAPK/com.example.app?version=latest"


@patch("core.sources.apkpure.requests.get")
def test_apkpure_extracts_version_from_filename(mock_get):
    response = Mock()
    response.status_code = 200
    response.url = "https://cdn.example/file.apk"
    response.headers = {
        "Content-Type": "application/octet-stream",
        "Content-Disposition": 'attachment; filename="SampleApp_v3.12.4_APKPure.apk"',
    }
    response.raise_for_status = Mock()
    response.close = Mock()
    mock_get.return_value = response

    source = APKPureSource()
    version, release_url, title = source.get_latest_version("com.example.app")

    assert version == "3.12.4"
    assert release_url == "https://d.apkpure.com/b/XAPK/com.example.app?version=latest"
    assert "SampleApp" in title
    response.close.assert_called_once()
