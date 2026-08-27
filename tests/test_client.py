from unittest.mock import MagicMock, patch

import pytest

from solaxx3.client import SolaxX3, _guess_slave_param_name
from solaxx3.exceptions import (
    RegisterReadError,
    RegistersNotLoadedError,
    SolaxConnectionError,
    UnknownRegisterError,
)
from solaxx3.models import RegisterInfo
from solaxx3.registers import RegisterRepository


def make_repo() -> RegisterRepository:
    return RegisterRepository(
        {
            "grid_voltage": RegisterInfo(
                name="grid_voltage",
                address=0,
                register_type="input",
                data_format="uint16",
                data_length=1,
                signed=False,
                si_adj=10,
                data_unit="V",
                description="Grid voltage",
            ),
            "some_holding_flag": RegisterInfo(
                name="some_holding_flag",
                address=0,
                register_type="holding",
                data_format="uint16",
                data_length=1,
                signed=False,
                si_adj=1,
                data_unit="N/A",
                description="A holding register",
            ),
        }
    )


def modbus_response(registers):
    response = MagicMock()
    response.isError.return_value = False
    response.registers = registers
    return response


@pytest.fixture
def client():
    with patch("solaxx3.client.ModbusSerialClient") as mock_serial_client_cls:
        instance = mock_serial_client_cls.return_value
        c = SolaxX3(register_repository=make_repo())
        c.client = instance
        yield c


class TestGuessSlaveParamName:
    def test_versions_before_3_10_use_slave(self):
        # pymodbus used "slave=" for the entire 3.0 - 3.9 series, not just 3.9.
        assert _guess_slave_param_name("3.0.0") == "slave"
        assert _guess_slave_param_name("3.6.9") == "slave"
        assert _guess_slave_param_name("3.8.3") == "slave"
        assert _guess_slave_param_name("3.9.0") == "slave"
        assert _guess_slave_param_name("3.9.2") == "slave"

    def test_versions_3_10_and_later_use_device_id(self):
        # pymodbus renamed slave= to device_id= in 3.10.0 (PR #2600).
        assert _guess_slave_param_name("3.10.0") == "device_id"
        assert _guess_slave_param_name("3.11.1") == "device_id"
        assert _guess_slave_param_name("3.12.1") == "device_id"
        assert _guess_slave_param_name("4.0.0") == "device_id"

    def test_unparseable_version_falls_back_to_device_id(self):
        assert _guess_slave_param_name("not-a-version") == "device_id"


class TestConnect:
    def test_connect_success_sets_connected_true(self, client):
        client.client.connect.return_value = True
        assert client.connect() is True
        assert client.connected is True

    def test_connect_failure_sets_connected_false(self, client):
        client.client.connect.return_value = False
        assert client.connect() is False
        assert client.connected is False

    def test_connect_exception_is_caught_and_reported_as_failure(self, client):
        client.client.connect.side_effect = OSError("serial port busy")
        assert client.connect() is False
        assert client.connected is False

    def test_disconnect_closes_client_and_clears_connected_flag(self, client):
        client.client.connect.return_value = True
        client.connect()
        client.disconnect()
        client.client.close.assert_called_once()
        assert client.connected is False

    def test_context_manager_connects_and_disconnects(self, client):
        client.client.connect.return_value = True
        with client as c:
            assert c.connected is True
        client.client.close.assert_called_once()


class TestReadAllRegisters:
    def test_raises_if_not_connected(self, client):
        with pytest.raises(SolaxConnectionError):
            client.read_all_registers()

    def test_reads_input_and_holding_registers(self, client):
        client.client.connect.return_value = True
        client.connect()
        client.client.read_input_registers.return_value = modbus_response([1234])
        client.client.read_holding_registers.return_value = modbus_response([1])

        client.read_all_registers()

        client.client.read_input_registers.assert_called_once()
        client.client.read_holding_registers.assert_called_once()

    def test_raises_register_read_error_on_modbus_error_response(self, client):
        client.client.connect.return_value = True
        client.connect()
        error_response = MagicMock()
        error_response.isError.return_value = True
        client.client.read_input_registers.return_value = error_response

        with pytest.raises(RegisterReadError):
            client.read_all_registers()

    def test_raises_register_read_error_on_none_response(self, client):
        client.client.connect.return_value = True
        client.connect()
        client.client.read_input_registers.return_value = None

        with pytest.raises(RegisterReadError):
            client.read_all_registers()


class TestRead:
    def test_raises_if_registers_not_loaded(self, client):
        with pytest.raises(RegistersNotLoadedError):
            client.read("grid_voltage")

    def test_raises_for_unknown_register(self, client):
        client.client.connect.return_value = True
        client.connect()
        client.client.read_input_registers.return_value = modbus_response([1234])
        client.client.read_holding_registers.return_value = modbus_response([1])
        client.read_all_registers()

        with pytest.raises(UnknownRegisterError):
            client.read("does_not_exist")

    def test_reads_and_decodes_a_known_register(self, client):
        client.client.connect.return_value = True
        client.connect()
        client.client.read_input_registers.return_value = modbus_response([1234])
        client.client.read_holding_registers.return_value = modbus_response([1])
        client.read_all_registers()

        reading = client.read("grid_voltage")

        assert reading.value == 123.4
        assert reading.unit == "V"
        # NamedTuple unpacking still works for backward compatibility
        value, unit = reading
        assert (value, unit) == (123.4, "V")


def test_list_register_names_returns_catalog_names(client):
    assert set(client.list_register_names()) == {"grid_voltage", "some_holding_flag"}


class TestSelfCorrectingSlaveParam:
    def _client_guessing(self, wrong_guess: str) -> "SolaxX3":
        """Build a client whose initial guess is deliberately wrong."""

        mock_serial_client_cls = patch("solaxx3.client.ModbusSerialClient").start()
        instance = mock_serial_client_cls.return_value
        instance.connect.return_value = True

        with patch("solaxx3.client._guess_slave_param_name", return_value=wrong_guess):
            c = SolaxX3(register_repository=make_repo(), device_id=7)
        c.client = instance
        c.connect()
        return c

    def _strict_read_fn(self, accepted_kwarg: str, response):
        def read_fn(**kwargs):
            if accepted_kwarg not in kwargs:
                wrong_kwarg = "slave" if accepted_kwarg == "device_id" else "device_id"
                raise TypeError(
                    f"read_input_registers() got an unexpected keyword "
                    f"argument '{wrong_kwarg}'"
                )
            assert kwargs[accepted_kwarg] == 7
            return response

        return read_fn

    def test_flips_from_device_id_to_slave_on_type_error(self):
        client = self._client_guessing(wrong_guess="device_id")
        strict_fn = self._strict_read_fn("slave", modbus_response([0] * 100))
        client.client.read_input_registers.side_effect = strict_fn
        client.client.read_holding_registers.side_effect = strict_fn

        client.read_all_registers()

        assert client._slave_param_name == "slave"
        patch.stopall()

    def test_flips_from_slave_to_device_id_on_type_error(self):
        client = self._client_guessing(wrong_guess="slave")
        strict_fn = self._strict_read_fn("device_id", modbus_response([0] * 100))
        client.client.read_input_registers.side_effect = strict_fn
        client.client.read_holding_registers.side_effect = strict_fn

        client.read_all_registers()

        assert client._slave_param_name == "device_id"
        patch.stopall()

    def test_correction_persists_across_later_calls(self):
        client = self._client_guessing(wrong_guess="device_id")
        strict_fn = self._strict_read_fn("slave", modbus_response([0] * 100))
        client.client.read_input_registers.side_effect = strict_fn
        client.client.read_holding_registers.side_effect = strict_fn

        client.read_all_registers()
        assert client._slave_param_name == "slave"

        # a second read should go straight to "slave" with no more TypeErrors
        client.read_all_registers()
        assert client._slave_param_name == "slave"
        patch.stopall()

    def test_unrelated_type_error_is_not_swallowed(self):
        client = self._client_guessing(wrong_guess="device_id")

        def broken_read_fn(**kwargs):
            raise TypeError("some unrelated bug, nothing to do with kwargs")

        client.client.read_input_registers.side_effect = broken_read_fn
        client.client.read_holding_registers.return_value = modbus_response([0] * 100)

        with patch("solaxx3.client.time.sleep"):
            with pytest.raises(RegisterReadError):
                client.read_all_registers()

        # the guess was never "corrected" because this wasn't a keyword mismatch
        assert client._slave_param_name == "device_id"
        patch.stopall()


class TestRetry:
    def test_max_retries_must_be_at_least_one(self):
        with pytest.raises(ValueError):
            SolaxX3(register_repository=make_repo(), max_retries=0)

    def test_succeeds_without_retrying_on_first_try(self, client):
        client.client.connect.return_value = True
        client.connect()
        client.client.read_input_registers.return_value = modbus_response([1234])
        client.client.read_holding_registers.return_value = modbus_response([1])

        with patch("solaxx3.client.time.sleep") as mock_sleep:
            client.read_all_registers()

        mock_sleep.assert_not_called()
        client.client.read_input_registers.assert_called_once()

    def test_recovers_after_a_transient_error_response(self, client):
        client.client.connect.return_value = True
        client.connect()

        error_response = MagicMock()
        error_response.isError.return_value = True
        client.client.read_input_registers.side_effect = [
            error_response,
            modbus_response([1234]),
        ]
        client.client.read_holding_registers.return_value = modbus_response([1])

        with patch("solaxx3.client.time.sleep") as mock_sleep:
            client.read_all_registers()

        assert client.client.read_input_registers.call_count == 2
        mock_sleep.assert_called_once()

    def test_recovers_after_a_transient_exception(self, client):
        client.client.connect.return_value = True
        client.connect()

        client.client.read_input_registers.side_effect = [
            OSError("serial glitch"),
            modbus_response([1234]),
        ]
        client.client.read_holding_registers.return_value = modbus_response([1])

        with patch("solaxx3.client.time.sleep"):
            client.read_all_registers()

        assert client.client.read_input_registers.call_count == 2

    def test_raises_register_read_error_after_exhausting_all_retries(self, client):
        client.client.connect.return_value = True
        client.connect()

        error_response = MagicMock()
        error_response.isError.return_value = True
        client.client.read_input_registers.return_value = error_response

        with patch("solaxx3.client.time.sleep"):
            with pytest.raises(RegisterReadError):
                client.read_all_registers()

        # default max_retries is 3
        assert client.client.read_input_registers.call_count == 3

    def test_backoff_delay_doubles_between_attempts(self, client):
        client.client.connect.return_value = True
        client.connect()

        error_response = MagicMock()
        error_response.isError.return_value = True
        client.client.read_input_registers.return_value = error_response
        client.client.read_holding_registers.return_value = modbus_response([1])

        with patch("solaxx3.client.time.sleep") as mock_sleep:
            with pytest.raises(RegisterReadError):
                client.read_all_registers()

        # default retry_backoff_seconds=0.2, doubling: 0.2, 0.4 (2 sleeps for 3 attempts)
        assert [call.args[0] for call in mock_sleep.call_args_list] == [0.2, 0.4]

    def test_custom_retry_settings_are_respected(self):
        with patch("solaxx3.client.ModbusSerialClient") as mock_serial_client_cls:
            instance = mock_serial_client_cls.return_value
            c = SolaxX3(
                register_repository=make_repo(),
                max_retries=5,
                retry_backoff_seconds=0.01,
            )
            c.client = instance
            instance.connect.return_value = True
            c.connect()

            error_response = MagicMock()
            error_response.isError.return_value = True
            instance.read_input_registers.return_value = error_response
            instance.read_holding_registers.return_value = modbus_response([1])

            with patch("solaxx3.client.time.sleep") as mock_sleep:
                with pytest.raises(RegisterReadError):
                    c.read_all_registers()

            assert instance.read_input_registers.call_count == 5
            assert mock_sleep.call_count == 4
