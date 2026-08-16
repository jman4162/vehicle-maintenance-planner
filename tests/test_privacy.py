from PIL import Image

from vehicle_maintenance.privacy import audit_tree


def test_clean_tree_passes(tmp_path):
    (tmp_path / "README.md").write_text("Entirely synthetic guidance.")
    report = audit_tree(tmp_path)
    assert report.passed
    assert report.scanned_files == 1


def test_private_artifacts_and_identifiers_fail(tmp_path):
    (tmp_path / "record.sqlite3").write_bytes(b"sqlite")
    (tmp_path / ".env").write_text("SERVICE_" + "TOKEN=" + "'" + "abcdefghijklmnop" + "'")
    (tmp_path / "private.local.md").write_text("contact " + "owner" + "@example.test")
    report = audit_tree(tmp_path)
    kinds = {finding.kind for finding in report.findings}
    assert not report.passed
    assert {"private_artifact", "private_file", "email", "credential"} <= kinds


def test_media_only_allowed_in_synthetic_fixture(tmp_path):
    image = Image.new("RGB", (4, 4), "white")
    public_image = tmp_path / "receipt.jpg"
    image.save(public_image)
    fixture_dir = tmp_path / "tests" / "fixtures" / "synthetic"
    fixture_dir.mkdir(parents=True)
    image.save(fixture_dir / "generated.jpg")
    report = audit_tree(tmp_path)
    media_paths = [finding.path for finding in report.findings if finding.kind == "media"]
    assert media_paths == ["receipt.jpg"]


def test_ignored_build_directories_are_not_scanned(tmp_path):
    ignored = tmp_path / "node_modules"
    ignored.mkdir()
    (ignored / ".env").write_text("PASS" + "WORD=" + "'" + "not-public-value" + "'")
    assert audit_tree(tmp_path).passed


def test_private_store_directories_are_rejected(tmp_path):
    exports = tmp_path / "exports"
    exports.mkdir()
    (exports / "packet.txt").write_text("encrypted-looking but still private")
    report = audit_tree(tmp_path)
    assert any(finding.kind == "private_store" for finding in report.findings)
