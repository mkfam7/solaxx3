from solaxx3.schema import validate_catalog

VALID_ENTRY = {
    "address": 0,
    "register_type": "input",
    "data_format": "uint16",
    "si_adj": 10,
    "signed": False,
    "data_unit": "V",
    "data_length": 1,
    "description": "Grid voltage",
}


def test_valid_catalog_has_no_errors():
    assert validate_catalog({"grid_voltage": VALID_ENTRY}) == []


def test_valid_catalog_with_optional_bounds_has_no_errors():
    entry = dict(VALID_ENTRY, min_value=80, max_value=300)
    assert validate_catalog({"grid_voltage": entry}) == []


def test_root_must_be_an_object():
    errors = validate_catalog(["not", "an", "object"])
    assert len(errors) == 1
    assert "<root>" in errors[0]


def test_missing_required_field_is_reported():
    entry = dict(VALID_ENTRY)
    del entry["address"]
    errors = validate_catalog({"grid_voltage": entry})
    assert any("missing required field 'address'" in e for e in errors)


def test_wrong_type_is_reported():
    entry = dict(VALID_ENTRY, address="not-an-int")
    errors = validate_catalog({"grid_voltage": entry})
    assert any("grid_voltage.address" in e and "expected type" in e for e in errors)


def test_invalid_enum_value_is_reported():
    entry = dict(VALID_ENTRY, register_type="bogus")
    errors = validate_catalog({"grid_voltage": entry})
    assert any("register_type" in e and "not one of" in e for e in errors)


def test_negative_address_below_minimum_is_reported():
    entry = dict(VALID_ENTRY, address=-1)
    errors = validate_catalog({"grid_voltage": entry})
    assert any("below minimum" in e for e in errors)


def test_unexpected_field_is_reported():
    entry = dict(VALID_ENTRY, made_up_field="oops")
    errors = validate_catalog({"grid_voltage": entry})
    assert any("unexpected field 'made_up_field'" in e for e in errors)


def test_min_value_greater_than_max_value_is_reported():
    entry = dict(VALID_ENTRY, min_value=100, max_value=50)
    errors = validate_catalog({"grid_voltage": entry})
    assert any("min_value" in e and "greater than" in e for e in errors)


def test_multiple_errors_are_all_collected_not_just_the_first():
    entry = dict(VALID_ENTRY)
    del entry["address"]
    entry["register_type"] = "bogus"
    errors = validate_catalog({"grid_voltage": entry})
    assert len(errors) >= 2


def test_errors_from_multiple_registers_are_all_collected():
    bad_entry = dict(VALID_ENTRY)
    del bad_entry["address"]
    errors = validate_catalog({"good": VALID_ENTRY, "bad": bad_entry})
    assert len(errors) == 1
    assert "bad: missing required field 'address'" in errors[0]
