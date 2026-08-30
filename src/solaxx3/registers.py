"""Catalog of the inverter's Modbus registers.

The register catalog used to be a ~3500-line hardcoded dict baked into a
class body. That made it hard to review, diff, or reuse the data from
non-Python tooling. It now lives in ``data/registers.json`` and is loaded
once, validated, and exposed through :class:`RegisterRepository`.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources

from .exceptions import CatalogValidationError, UnknownRegisterError
from .models import RegisterInfo, RegisterType
from .schema import validate_catalog

_DEFAULT_DATA_FILE = "registers.json"


class RegisterRepository:
    """Read-only, in-memory catalog of :class:`RegisterInfo` definitions."""

    def __init__(self, registers: dict[str, RegisterInfo]) -> None:
        self._registers = registers

    @classmethod
    def from_json_file(cls, path: str) -> RegisterRepository:
        """Build a repository from a JSON file on disk."""

        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
        return cls._from_raw(raw)

    @classmethod
    def from_package_data(cls) -> RegisterRepository:
        """Build a repository from the JSON data bundled with this package."""

        raw_text = (
            resources.files("solaxx3")
            .joinpath("data", _DEFAULT_DATA_FILE)
            .read_text(encoding="utf-8")
        )
        return cls._from_raw(json.loads(raw_text))

    @classmethod
    def _from_raw(cls, raw: dict[str, dict]) -> RegisterRepository:
        errors = validate_catalog(raw)
        if errors:
            raise CatalogValidationError(errors)

        registers = {
            name: RegisterInfo.from_dict(name, data) for name, data in raw.items()
        }
        return cls(registers)

    def get(self, name: str) -> RegisterInfo:
        """Return the :class:`RegisterInfo` for ``name``.

        Raises:
            UnknownRegisterError: if no register with that name exists.
        """

        try:
            return self._registers[name]
        except KeyError as exc:
            raise UnknownRegisterError(name) from exc

    def list_names(self) -> list[str]:
        """Return the names of every register in the catalog."""

        return list(self._registers.keys())

    def list_names_by_type(self, register_type: RegisterType) -> list[str]:
        """Return the names of every register of the given type."""

        return [
            name
            for name, info in self._registers.items()
            if info.register_type == register_type
        ]

    def max_register_count(self, register_type: RegisterType) -> int:
        """Return how many consecutive registers of ``register_type`` must be
        read (from address 0) to cover every known register of that type.

        Used instead of a hardcoded block count so a full read always
        covers every register the catalog knows about, and no more.
        """

        end_addresses = [
            info.end_address
            for info in self._registers.values()
            if info.register_type == register_type
        ]
        return max(end_addresses, default=0)

    def __len__(self) -> int:
        return len(self._registers)


@lru_cache(maxsize=1)
def default_repository() -> RegisterRepository:
    """Return the repository built from the package's bundled data file.

    Cached because the catalog is immutable and reasonably large (~350
    entries) — no need to re-parse the JSON file on every call.
    """

    return RegisterRepository.from_package_data()
