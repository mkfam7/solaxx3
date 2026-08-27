import pytest

from solaxx3.models import RegisterInfo


def make_kwargs(**overrides):
    defaults = dict(
        name="test_register",
        address=0,
        register_type="input",
        data_format="uint16",
        data_length=1,
        signed=False,
        si_adj=1,
        data_unit="V",
        description="Test register",
    )
    defaults.update(overrides)
    return defaults


def test_valid_register_info_constructs_fine():
    info = RegisterInfo(**make_kwargs(min_value=0, max_value=100))
    assert info.min_value == 0
    assert info.max_value == 100


def test_bounds_default_to_none():
    info = RegisterInfo(**make_kwargs())
    assert info.min_value is None
    assert info.max_value is None


def test_negative_address_rejected():
    with pytest.raises(ValueError):
        RegisterInfo(**make_kwargs(address=-1))


def test_zero_data_length_rejected():
    with pytest.raises(ValueError):
        RegisterInfo(**make_kwargs(data_length=0))


def test_zero_si_adj_rejected():
    with pytest.raises(ValueError):
        RegisterInfo(**make_kwargs(si_adj=0))


def test_min_value_greater_than_max_value_rejected():
    with pytest.raises(ValueError):
        RegisterInfo(**make_kwargs(min_value=100, max_value=50))


def test_from_dict_reads_optional_bounds_when_present():
    data = make_kwargs(min_value=10, max_value=20)
    del data["name"]
    info = RegisterInfo.from_dict("test_register", data)
    assert (info.min_value, info.max_value) == (10, 20)


def test_from_dict_bounds_default_to_none_when_absent():
    data = make_kwargs()
    del data["name"]
    info = RegisterInfo.from_dict("test_register", data)
    assert (info.min_value, info.max_value) == (None, None)
