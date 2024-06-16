"""Module containing an abstract class."""

from abc import ABC, abstractmethod


class DataSourceDb(ABC):
    """Abstract class representing a data source."""

    @abstractmethod
    def save_record(self):
        """Transfer some data."""

        raise NotImplementedError

    @abstractmethod
    def bulk_save(self):
        """Transfer multiple records of data."""

        raise NotImplementedError
