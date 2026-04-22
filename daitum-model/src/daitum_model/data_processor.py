# Copyright 2026 Daitum
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import datetime
import json
import os.path
from typing import cast

from daitum_model import DataType, MapDataType, ModelBuilder, ObjectDataType
from daitum_model.fields import ComboField, DataField, Field
from daitum_model.tables import DataTable, Table


def prepare_data(model: ModelBuilder, input_path: str, output_path: str):
    data_tables = [table for table in model.get_tables() if isinstance(table, DataTable)]
    table_data = {}
    for table in data_tables:

        folder = "model-data" if table.model_level else "scenarios/Initial"
        output_filename = f"{output_path}/{folder}/{table.id}.csv"
        input_filename = f"{input_path}/{table.id}.csv"

        converted_data = []

        data_fields: list[Field] = [
            field
            for field in table.get_fields()
            if (
                isinstance(field, DataField)
                or (isinstance(field, ComboField) and field.calculate_in_optimiser)
            )
        ]

        if os.path.exists(input_filename):
            with open(input_filename) as input_fp:
                reader = csv.DictReader(input_fp)
                table_data[table.id] = [row for row in reader]
                for row in table_data[table.id]:
                    converted_row: dict = {}
                    for field in data_fields:
                        if field.id not in row:
                            converted_row.setdefault(field.id, None)
                            continue

                        value = _convert(field, row[field.id], table_data)
                        converted_row[field.id] = json.dumps(value) if value is not None else None

                        if field.tracking_group is not None:
                            tracked_field = table.get_field(field.tracking_id)
                            if isinstance(tracked_field, DataField):
                                converted_row[tracked_field.id] = converted_row[field.id]

                    converted_data.append(converted_row)

        field_names = [field.id for field in data_fields]
        with open(output_filename, "w", newline="") as output_fp:
            writer = csv.DictWriter(output_fp, fieldnames=field_names)
            writer.writeheader()
            writer.writerows(converted_data)


def _convert(field: Field, raw_value: str, table_data: dict):
    if not raw_value:
        return None

    if field.data_type.is_array():
        return [
            _convert_singular(field, token.strip(), table_data) for token in raw_value.split(",")
        ]

    return _convert_singular(field, raw_value, table_data)


def _convert_singular(field: Field, raw_value: str, table_data: dict):
    data_type = field.data_type

    if isinstance(data_type, DataType):
        return _convert_primitive(data_type, raw_value)

    if isinstance(data_type, MapDataType):
        return {
            index: _convert_primitive(data_type._data_type, token.strip())
            for index, token in enumerate(raw_value.split(","))
            if token.strip()
        }

    if isinstance(data_type, ObjectDataType):
        source_table = cast(Table, data_type._source_table)

        table_rows = table_data.get(source_table.id, [])

        for row_uid, table_row in enumerate(table_rows):
            if table_row[source_table.key_column] == raw_value:
                if source_table.id_field is not None:
                    id_value = str(table_row[source_table.id_field])
                    return {"stringKey": id_value}
                return {"rowUid": row_uid}

    return None


def _convert_primitive(data_type: DataType, raw_value: str):  # noqa PLR0911
    if data_type.is_array():
        data_type = data_type.from_array()
    if data_type == DataType.STRING:
        return raw_value
    if data_type == DataType.BOOLEAN:
        return raw_value.upper() == "TRUE"
    if data_type == DataType.INTEGER:
        return int(raw_value)
    if data_type == DataType.DECIMAL:
        return float(raw_value)
    if data_type == DataType.DATE:
        date_value = datetime.datetime.strptime(raw_value, "%d/%m/%Y")
        return [date_value.year, date_value.month, date_value.day]
    if data_type == DataType.TIME:
        time_value = datetime.datetime.strptime(raw_value, "%H:%M")
        return [time_value.hour, time_value.minute, 0]
    if data_type == DataType.DATETIME:
        datetime_value = datetime.datetime.strptime(raw_value, "%d/%m/%Y %H:%M")
        return [
            datetime_value.year,
            datetime_value.month,
            datetime_value.day,
            datetime_value.hour,
            datetime_value.minute,
            0,
        ]
    raise ValueError(f"Invalid data type: {data_type}")
