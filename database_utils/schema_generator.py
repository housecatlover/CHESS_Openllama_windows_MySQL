import re
import logging
import random
import os
from typing import Dict, List, Optional

from database_utils.execution import execute_sql
from database_utils.db_info import get_db_schema
from database_utils.schema import DatabaseSchema, get_primary_keys

class DatabaseSchemaGenerator:
    CACHED_DB_SCHEMA = {}

    def __init__(self, tentative_schema: Optional[DatabaseSchema] = None, schema_with_examples: Optional[DatabaseSchema] = None,
                 schema_with_descriptions: Optional[DatabaseSchema] = None, db_id: Optional[str] = None, db_path: Optional[str] = None,
                 add_examples: bool = True):
        self.db_id = db_id
        self.db_path = db_path
        self.add_examples = add_examples
        if self.db_id not in DatabaseSchemaGenerator.CACHED_DB_SCHEMA:
            DatabaseSchemaGenerator._load_schema_into_cache(db_id=db_id, db_path=db_path)
        self.schema_structure = tentative_schema or DatabaseSchema()
        self.schema_with_examples = schema_with_examples or DatabaseSchema()
        self.schema_with_descriptions = schema_with_descriptions or DatabaseSchema()
        self._initialize_schema_structure()

    @staticmethod
    def _set_primary_keys(db_path: str, database_schema: DatabaseSchema) -> None:
        schema_with_primary_keys = {
            table_name: {
                # col[1]: {"primary_key": True} for col in execute_sql(db_path, f"PRAGMA table_info(`{table_name}`)") if col[5] > 0
                col[0]: {"primary_key": True} for col in execute_sql(db_path, f"SHOW COLUMNS FROM `{table_name}`") if col[3].upper() == "PRI"
            }
            for table_name in database_schema.tables.keys()
        }
        database_schema.set_columns_info(schema_with_primary_keys)

    @staticmethod
    def _set_foreign_keys(db_path: str, database_schema: DatabaseSchema) -> None:
        schema_with_references = {
            table_name: {
                column_name: {"foreign_keys": [], "referenced_by": []} for column_name in table_schema.columns.keys()
            }
            for table_name, table_schema in database_schema.tables.items()
        }

        database_name = os.getenv("MYSQL_DATABASE", "documents")

        for table_name, columns in schema_with_references.items():
            foreign_keys_info = execute_sql(
                db_path,
                f"""
                SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = '{database_name}'
                  AND TABLE_NAME = '{table_name}'
                  AND REFERENCED_TABLE_NAME IS NOT NULL;
                """
            )
            for fk in foreign_keys_info:
                source_column, dest_table, destination_column = fk
                source_table = table_name
                destination_table = database_schema.get_actual_table_name(dest_table)

                schema_with_references[source_table][source_column]["foreign_keys"].append((destination_table, destination_column))
                schema_with_references[destination_table][destination_column]["referenced_by"].append((source_table, source_column))

        database_schema.set_columns_info(schema_with_references)

    @classmethod
    def _load_schema_into_cache(cls, db_id: str, db_path: str) -> None:
        db_schema = DatabaseSchema.from_schema_dict(get_db_schema(db_path))
        schema_with_type = {}
        for table_name in db_schema.tables.keys():
            # columns = execute_sql(db_path, f"PRAGMA table_info(`{table_name}`)", fetch="all")
            columns = execute_sql(db_path, f"SHOW COLUMNS FROM `{table_name}`", fetch="all")
            schema_with_type[table_name] = {}
            for col in columns:
                schema_with_type[table_name][col[0]] = {"type": col[1]}
                unique_values = execute_sql(db_path, f"SELECT COUNT(*) FROM (SELECT DISTINCT `{col[0]}` FROM `{table_name}` LIMIT 21) AS subquery;", "all", 480)
                is_categorical = int(unique_values[0][0]) < 20
                unique_values = None
                if is_categorical:
                    unique_values = execute_sql(db_path, f"SELECT DISTINCT `{col[0]}` FROM `{table_name}` WHERE `{col[0]}` IS NOT NULL")
                schema_with_type[table_name][col[0]].update({"unique_values": unique_values})
                try:
                    value_statics_query = f"""
                    SELECT CONCAT('Total count ', COUNT(`{col[0]}`), ' - Distinct count ', COUNT(DISTINCT `{col[0]}`),
                        ' - Null count ', SUM(CASE WHEN `{col[0]}` IS NULL THEN 1 ELSE 0 END)) AS counts
                    FROM (SELECT `{col[0]}` FROM `{table_name}` LIMIT 100000) AS limited_dataset;
                    """
                    value_statics = execute_sql(db_path, value_statics_query, "all", 480)
                    schema_with_type[table_name][col[0]].update({
                        "value_statics": str(value_statics[0][0]) if value_statics else None
                    })
                except Exception as e:
                    print(f"An error occurred while fetching statistics for {col[0]} in {table_name}: {e}")
                    schema_with_type[table_name][col[0]].update({"value_statics": None})
        db_schema.set_columns_info(schema_with_type)
        cls.CACHED_DB_SCHEMA[db_id] = db_schema
        cls._set_primary_keys(db_path, cls.CACHED_DB_SCHEMA[db_id])
        cls._set_foreign_keys(db_path, cls.CACHED_DB_SCHEMA[db_id])
