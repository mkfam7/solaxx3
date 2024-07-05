from typing import Any, Dict, List, Tuple

import mysql.connector

from .data_source_db import DataSourceDb


class MySQLDataSource(DataSourceDb):
    def __init__(self, mysql_connection_info: Dict[str, str]) -> None:
        self.user = mysql_connection_info["user"]
        self.host = mysql_connection_info["host"]
        self.password = mysql_connection_info["password"]

    def save_record(
        self,
        database: str,
        tablename: str,
        data: Dict[str, Any],
        use_obj_connection: bool = False,
        close_obj_connection: bool = True,
    ):
        query, values = self.create_query(tablename, data)

        if use_obj_connection:
            try:
                self.cursor.execute(query, values)

                if close_obj_connection:
                    self.db.commit()
                    self.db.close()

            finally:
                self.db.commit()
                self.db.close()

        else:
            db = mysql.connector.connect(
                user=self.user,
                host=self.host,
                password=self.password,
                database=database,
            )
            try:
                cursor = db.cursor()
                cursor.execute(query, values)
                db.commit()
                db.close()
            finally:
                db.close()

    def bulk_save(self, export_data: List[Dict[str, Any]]) -> None:
        for index, unit in enumerate(export_data):
            database, table_name, data = unit.values()

            if not hasattr(self, "db") or not hasattr(self, "cursor") or not self.db.is_connected():
                self.db = mysql.connector.connect(
                    user=self.user,
                    host=self.host,
                    password=self.password,
                    database=database,
                )
                try:
                    self.cursor = self.db.cursor()
                finally:
                    self.db.close()

            self.save_record(database, table_name, data, True, index + 1 == len(export_data))

    def create_query(self, table_name: str, data: dict) -> Tuple[str, list]:
        columns = list(data.keys())
        values = list(data.values())

        query = (
            f"REPLACE INTO {table_name} (" + ", ".join(columns) + ") VALUES (" + ", ".join(["%s"] * len(columns)) + ")"
        )
        return (query, values)
