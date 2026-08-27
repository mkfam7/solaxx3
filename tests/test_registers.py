import json
from pathlib import Path

import pytest

from solaxx3.exceptions import CatalogValidationError, UnknownRegisterError
from solaxx3.registers import RegisterRepository, default_repository

DATA_FILE = Path(__file__).parent.parent / "src" / "solaxx3" / "data" / "registers.json"


@pytest.fixture
def repo():
    return RegisterRepository.from_json_file(str(DATA_FILE))


def test_default_repository_loads_bundled_data():
    repo = default_repository()
    assert len(repo) > 0
    assert "grid_voltage" in repo.list_names()


def test_get_returns_register_info(repo):
    info = repo.get("grid_voltage")
    assert info.name == "grid_voltage"
    assert info.register_type == "input"
    assert info.data_unit == "V"


def test_get_unknown_register_raises(repo):
    with pytest.raises(UnknownRegisterError):
        repo.get("does_not_exist")


def test_list_names_by_type_only_returns_matching_type(repo):
    input_names = repo.list_names_by_type("input")
    holding_names = repo.list_names_by_type("holding")

    assert "grid_voltage" in input_names
    assert set(input_names).isdisjoint(holding_names)
    assert len(input_names) + len(holding_names) == len(repo)


def test_max_register_count_covers_every_register_of_that_type(repo):
    max_count = repo.max_register_count("input")
    for name in repo.list_names_by_type("input"):
        info = repo.get(name)
        assert info.end_address <= max_count


def test_bundled_catalog_declares_sanity_bounds_for_grid_voltage(repo):
    info = repo.get("grid_voltage")
    assert info.min_value is not None
    assert info.max_value is not None
    assert info.min_value < info.max_value


def test_from_json_file_rejects_a_catalog_that_fails_schema_validation(tmp_path):
    bad_catalog = {
        "grid_voltage": {
            # missing "address" and an invalid register_type
            "register_type": "not-a-real-type",
            "data_format": "uint16",
            "si_adj": 10,
            "signed": False,
            "data_unit": "V",
            "data_length": 1,
            "description": "Grid voltage",
        }
    }
    bad_file = tmp_path / "bad_registers.json"
    bad_file.write_text(json.dumps(bad_catalog))

    with pytest.raises(CatalogValidationError) as exc_info:
        RegisterRepository.from_json_file(str(bad_file))

    assert any("missing required field 'address'" in e for e in exc_info.value.errors)
    assert any("not one of" in e for e in exc_info.value.errors)
