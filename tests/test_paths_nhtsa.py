import pytest

from vehicle_maintenance.nhtsa import decode_vin, recalls_by_vehicle
from vehicle_maintenance.paths import data_paths


def test_path_override_creates_expected_shape(tmp_path):
    paths = data_paths(tmp_path).ensure()
    assert paths.database == tmp_path / "maintenance.sqlite3"
    assert all(path.is_dir() for path in (paths.documents, paths.ocr, paths.exports, paths.backups))


def test_nhtsa_is_explicit_opt_in():
    with pytest.raises(ValueError, match="explicit consent"):
        decode_vin("1" * 17, consent=False)
    with pytest.raises(ValueError, match="17 characters"):
        decode_vin("short", consent=True)
    with pytest.raises(ValueError, match="explicit consent"):
        recalls_by_vehicle("Honda", "CR-V", 2024, consent=False)
