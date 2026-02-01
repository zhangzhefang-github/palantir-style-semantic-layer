import json
import hashlib
from pathlib import Path

from governance.approval_package import build_approval_package


def _checksum(path: Path) -> str:
    sha = hashlib.sha256()
    sha.update(path.read_bytes())
    return sha.hexdigest()


def test_manifest_output(test_db_path, tmp_path):
    output_dir = tmp_path / "pkg"
    result = build_approval_package(
        {
            "db_path": test_db_path,
            "metric_name": "FPY",
            "version_a": "FPY_v1_standard",
            "version_b": "FPY_v2_rework",
            "change_type": "logical_change"
        },
        str(output_dir)
    )

    manifest_path = Path(result["manifest_json"])
    assert manifest_path.exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "package_id" in manifest
    assert "generated_at" in manifest
    assert manifest["change_context"]["metric"] == "FPY"
    assert manifest["change_context"]["version_a"] == "FPY_v1_standard"
    assert manifest["change_context"]["version_b"] == "FPY_v2_rework"
    assert "files" in manifest
    assert "checksums" in manifest

    for key, file_path in manifest["files"].items():
        path = Path(file_path)
        assert path.exists()
        assert manifest["checksums"][key] == _checksum(path)
