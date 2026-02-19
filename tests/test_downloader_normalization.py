import os
import sys
import zipfile
from unittest.mock import patch

sys.path.append(os.getcwd())

from core.downloader import _is_valid_apk, _is_xapk, _normalize_downloaded_file


def _build_zip(path: str, files: dict[str, str]):
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)


def test_normalize_keeps_valid_apk(tmp_path):
    src_apk = tmp_path / "input.apk"
    out_apk = tmp_path / "latest.apk"
    _build_zip(str(src_apk), {"AndroidManifest.xml": "<manifest/>", "classes.dex": "x"})

    assert _is_valid_apk(str(src_apk))
    _normalize_downloaded_file(str(src_apk), str(out_apk))

    assert out_apk.exists()
    assert _is_valid_apk(str(out_apk))


def test_normalize_converts_xapk(tmp_path):
    src_xapk = tmp_path / "input.xapk"
    out_apk = tmp_path / "latest.apk"
    _build_zip(
        str(src_xapk),
        {"manifest.json": '{"package_name":"com.example"}', "base.apk": "dummy"},
    )

    assert _is_xapk(str(src_xapk))

    converted = tmp_path / "input.apk"
    _build_zip(str(converted), {"AndroidManifest.xml": "<manifest/>"})

    with patch("core.downloader._convert_xapk_to_apk", return_value=str(converted)):
        _normalize_downloaded_file(str(src_xapk), str(out_apk))

    assert out_apk.exists()
    assert _is_valid_apk(str(out_apk))


def test_normalize_rejects_non_apk_package(tmp_path):
    src_file = tmp_path / "bad.bin"
    out_apk = tmp_path / "latest.apk"
    src_file.write_text("not a package", encoding="utf-8")

    try:
        _normalize_downloaded_file(str(src_file), str(out_apk))
    except RuntimeError as e:
        assert "neither a valid APK nor a convertible XAPK" in str(e)
    else:
        raise AssertionError("Expected RuntimeError for invalid download payload")
