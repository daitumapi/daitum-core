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

"""
TBD
"""

from daitum_model import DataType, Formula, MapDataType, ObjectDataType


def _LOOKUP(
    data_type: ObjectDataType, table_id: str, field_id: str, condition: str, reverse_search: str
) -> Formula:
    return Formula(data_type, f"LOOKUP({table_id}, {field_id}, {condition}, {reverse_search})")


def _MATCH(value: str, array: str, reverse_search: str) -> Formula:
    return Formula(DataType.INTEGER, f"MATCH({value}, {array}, {reverse_search})")


def _ROWS(table_id: str) -> Formula:
    return Formula(DataType.INTEGER, f"ROWS({table_id})")


def _SUM(data_type: DataType, *values: str) -> Formula:
    return Formula(data_type, f"SUM({','.join(values)})")


def _POWER(data_type: DataType, mantissa: str, exponent: str) -> Formula:
    return Formula(data_type, f"POWER({mantissa}, {exponent})")


def _IF(
    data_type: DataType | ObjectDataType | MapDataType,
    condition: str,
    true_branch: str,
    false_branch: str,
) -> Formula:
    return Formula(data_type, f"IF({condition}, {true_branch}, {false_branch})")


def _FIND(
    data_type: DataType,
    match_string: str,
    search_string: str,
    start_index: str | None = None,
) -> Formula:
    expression = (
        f"FIND({match_string}, {search_string}, {start_index})"
        if start_index is not None
        else f"FIND({match_string}, {search_string})"
    )
    return Formula(data_type, expression)


def _LEFT(data_type: DataType, input_string: str, index: str) -> Formula:
    return Formula(data_type, f"LEFT({input_string}, {index})")


def _RIGHT(data_type: DataType, input_string: str, index: str) -> Formula:
    return Formula(data_type, f"RIGHT({input_string}, {index})")


def _PREV(data_type: DataType | ObjectDataType | MapDataType, field_id: str) -> Formula:
    return Formula(data_type, f"PREV({field_id})")


def _NEXT(data_type: DataType | ObjectDataType | MapDataType, field_id: str) -> Formula:
    return Formula(data_type, f"NEXT({field_id})")


def _TEXT(data_type: DataType, field: str, formatting: str | None = None) -> Formula:
    expression = f"TEXT({field}, {formatting})" if formatting else f"TEXT({field})"
    return Formula(data_type, expression)


def _BLANK(data_type: DataType | ObjectDataType | MapDataType) -> Formula:
    return Formula(data_type, "BLANK()")


def _ISBLANK(field_string: str) -> Formula:
    return Formula(DataType.BOOLEAN, f"ISBLANK({field_string})")


def _IFBLANK(
    data_type: DataType | ObjectDataType | MapDataType,
    field: str,
    blank_branch: str,
) -> Formula:
    return Formula(data_type, f"IFBLANK({field}, {blank_branch})")


def _FILTER(
    data_type: DataType | ObjectDataType | MapDataType,
    table: str,
    filter_condition: str,
) -> Formula:
    return Formula(data_type, f"FILTER({table}, {filter_condition})")


def _MIN(data_type: DataType, *fields: str) -> Formula:
    formula_str = f"MIN({', '.join(fields)})"
    return Formula(data_type, formula_str)


def _MAX(data_type: DataType, *fields: str) -> Formula:
    formula_str = f"MAX({', '.join(fields)})"
    return Formula(data_type, formula_str)


def _OR(data_type: DataType, *fields: str) -> Formula:
    formula_str = f"OR({', '.join(fields)})"
    return Formula(data_type, formula_str)


def _AND(data_type: DataType, *fields: str) -> Formula:
    formula_str = f"AND({', '.join(fields)})"
    return Formula(data_type, formula_str)


def _NOT(data_type: DataType, field: str) -> Formula:
    return Formula(data_type, f"NOT({field})")


def _BITMASK(field: str) -> Formula:
    return Formula(DataType.INTEGER, f"BITMASK({field})")


def _VALUES(data_type: DataType, field: str) -> Formula:
    return Formula(data_type, f"VALUES({field})")


def _CONTAINS(array: str, field: str) -> Formula:
    return Formula(DataType.BOOLEAN, f"CONTAINS({array}, {field})")


def _INDEX(data_type: DataType | ObjectDataType, array: str, index: str) -> Formula:
    return Formula(data_type, f"INDEX({array}, {index})")


def _SIZE(array: str) -> Formula:
    return Formula(DataType.INTEGER, f"SIZE({array})")


def _PLUSDAYS(data_type: DataType, date: str, days: str) -> Formula:
    return Formula(data_type, f"PLUSDAYS({date}, {days})")


def _ROUND(data_type: DataType, value: str) -> Formula:
    return Formula(data_type, f"ROUND({value})")


def _FLOOR(data_type: DataType, value: str) -> Formula:
    return Formula(data_type, f"FLOOR({value})")


def _CEILING(data_type: DataType, value: str) -> Formula:
    return Formula(data_type, f"CEILING({value})")


def _MOD(data_type: DataType, field_1: str, field_2: str) -> Formula:
    return Formula(data_type, f"MOD({field_1}, {field_2})")


def _IFERROR(
    data_type: DataType | ObjectDataType | MapDataType, formula: str, error_branch: str
) -> Formula:
    return Formula(data_type, f"IFERROR({formula}, {error_branch})")


def _DAYSBETWEEN(data_type: DataType, first_date: str, second_date: str) -> Formula:
    return Formula(data_type, f"DAYSBETWEEN({first_date}, {second_date})")


def _YEAR(data_type: DataType, date: str) -> Formula:
    return Formula(data_type, f"YEAR({date})")


def _MONTH(data_type: DataType, date: str) -> Formula:
    return Formula(data_type, f"MONTH({date})")


def _DAY(data_type: DataType, date: str) -> Formula:
    return Formula(data_type, f"DAY({date})")


def _DATE(data_type: DataType, year: str, month: str, day: str) -> Formula:
    return Formula(data_type, f"DATE({year}, {month}, {day})")


def _DATETIME(
    data_type: DataType,
    date_parts: tuple[str, str, str],
    time_parts: tuple[str, str, str],
) -> Formula:
    year, month, day = date_parts
    hours, minutes, seconds = time_parts
    return Formula(data_type, f"DATETIME({year}, {month}, {day}, {hours}, {minutes}, {seconds})")


def _EOMONTH(data_type: DataType, date: str, months: str) -> Formula:
    return Formula(data_type, f"EOMONTH({date}, {months})")


def _BITAND(data_type: DataType, field_1: str, field_2: str) -> Formula:
    formula_str = f"BITAND({field_1}, {field_2})"
    return Formula(data_type, formula_str)


def _BITOR(data_type: DataType, field_1: str, field_2: str) -> Formula:
    formula_str = f"BITOR({field_1}, {field_2})"
    return Formula(data_type, formula_str)


def _TIME(data_type: DataType, hours: str, minutes: str, seconds: str) -> Formula:
    return Formula(data_type, f"TIME({hours}, {minutes}, {seconds})")


def _SETTIME(data_type: DataType, date: str, time: str) -> Formula:
    return Formula(data_type, f"SETTIME({date}, {time})")


def _PLUSMINUTES(data_type: DataType, time: str, minutes: str) -> Formula:
    return Formula(data_type, f"PLUSMINUTES({time}, {minutes})")


def _CHOOSE(
    data_type: DataType | ObjectDataType | MapDataType, index: str, *fields: str
) -> Formula:
    formula_str = f"CHOOSE({index}, {', '.join(fields)})"
    return Formula(data_type, formula_str)


def _ARRAY(data_type: DataType | ObjectDataType, ignore_null: str, *fields: str) -> Formula:
    formula_str = f"ARRAY({ignore_null}, {', '.join(fields)})"
    return Formula(data_type, formula_str)


def _ABS(data_type: DataType, value: str) -> Formula:
    return Formula(data_type, f"ABS({value})")


def _GET(data_type: DataType, map_string: str, key: str) -> Formula:
    return Formula(data_type, f"GET({map_string}, {key})")


def _EXP(data_type: DataType, value: str) -> Formula:
    return Formula(data_type, f"EXP({value})")


def _INTERSECTION(
    data_type: DataType | ObjectDataType | MapDataType, ignore_blanks: str, *arrays: str
) -> Formula:
    return Formula(data_type, f"INTERSECTION({ignore_blanks}, {', '.join(arrays)})")


def _UNION(
    data_type: DataType | ObjectDataType | MapDataType, ignore_blanks: str, *arrays: str
) -> Formula:
    return Formula(data_type, f"UNION({ignore_blanks}, {', '.join(arrays)})")


def _AVERAGE(*values: str) -> Formula:
    return Formula(DataType.DECIMAL, f"AVERAGE({','.join(values)})")


def _CHAR(data_type: DataType, value: str) -> Formula:
    return Formula(data_type, f"CHAR({value})")


def _DISTINCT(data_type: DataType | ObjectDataType, array: str) -> Formula:
    return Formula(data_type, f"DISTINCT({array})")


def _HOUR(data_type: DataType, time: str) -> Formula:
    return Formula(data_type, f"HOUR({time})")


def _HOURSBETWEEN(data_type: DataType, first_time: str, second_time: str) -> Formula:
    return Formula(data_type, f"HOURSBETWEEN({first_time}, {second_time})")


def _INTEGER(data_type: DataType, value: str) -> Formula:
    return Formula(data_type, f"INTEGER({value})")


def _LEN(data_type: DataType, value: str) -> Formula:
    return Formula(data_type, f"LEN({value})")


def _ISERROR(data_type: DataType, value: str) -> Formula:
    return Formula(data_type, f"ISERROR({value})")


def _LOOKUPARRAY(
    data_type: DataType | ObjectDataType, array: str, match_array: str, result_array: str
) -> Formula:
    return Formula(data_type, f"LOOKUP_ARRAY({array}, {match_array}, {result_array})")


def _LOWER(data_type: DataType, value: str) -> Formula:
    return Formula(data_type, f"LOWER({value})")


def _MEDIAN(*values: str) -> Formula:
    return Formula(DataType.DECIMAL, f"MEDIAN({','.join(values)})")


def _MINUTE(data_type: DataType, time: str) -> Formula:
    return Formula(data_type, f"MINUTE({time})")


def _MONTHSBETWEEN(data_type: DataType, first_date: str, second_date: str) -> Formula:
    return Formula(data_type, f"MONTHSBETWEEN({first_date}, {second_date})")


def _SECOND(data_type: DataType, time: str) -> Formula:
    return Formula(data_type, f"SECOND({time})")


def _STDEV(*values: str) -> Formula:
    return Formula(DataType.DECIMAL, f"STDEV({','.join(values)})")


def _TEXTJOIN(delimiter: str, ignore_empty: str, *string_arrays: str) -> Formula:
    return Formula(
        DataType.STRING, f"TEXTJOIN({delimiter}, {ignore_empty}, {','.join(string_arrays)})"
    )


def _TRIM(data_type: DataType, value: str) -> Formula:
    return Formula(data_type, f"TRIM({value})")


def _UPPER(data_type: DataType, value: str) -> Formula:
    return Formula(data_type, f"UPPER({value})")


def _WEEKDAY(data_type: DataType, date: str, return_type: str | None = None) -> Formula:
    expression = f"WEEKDAY({date}, {return_type})" if return_type else f"WEEKDAY({date})"
    return Formula(data_type, expression)


def _WEIBULL(data_type: DataType, x: str, shape: str, scale: str, cumulative: str) -> Formula:
    return Formula(data_type, f"WEIBULL({x}, {shape}, {scale}, {cumulative})")


def _COUNT(array: str, value: str) -> Formula:
    return Formula(DataType.INTEGER, f"COUNT({array}, {value})")


def _COUNTBLANKS(array: str) -> Formula:
    return Formula(DataType.INTEGER, f"COUNTBLANKS({array})")


def _COUNTDUPLICATES(array: str, include_first_instance: str, ignore_blanks: str) -> Formula:
    return Formula(
        DataType.INTEGER, f"COUNTDUPLICATES({array}, {include_first_instance}, {ignore_blanks})"
    )


def _BITMASKSTRING(array: str) -> Formula:
    return Formula(DataType.STRING, f"BITMASKSTRING({array})")


def _DISTRIBUTE(value: str, array: str) -> Formula:
    return Formula(DataType.INTEGER_ARRAY, f"DISTRIBUTE({value}, {array})")


def _FINDDUPLICATES(array: str, include_first_instance: str, ignore_blanks: str) -> Formula:
    return Formula(
        DataType.BOOLEAN_ARRAY,
        f"FINDDUPLICATES({array}, {include_first_instance}, {ignore_blanks})",
    )


def _ROWVECTOR() -> Formula:
    return Formula(DataType.INTEGER_ARRAY, "ROWVECTOR()")


def _ARRAYMAX(data_type: DataType, *values: str) -> Formula:
    return Formula(data_type, f"ARRAYMAX({','.join(values)})")


def _ARRAYMIN(data_type: DataType, *values: str) -> Formula:
    return Formula(data_type, f"ARRAYMIN({','.join(values)})")


def _RANK(comparison_value: str, array: str, ascending: str) -> Formula:
    return Formula(DataType.INTEGER, f"RANK({comparison_value}, {array}, {ascending})")


def _TOTIMEZONE(is_array: bool, date_time: str, time_zone: str) -> Formula:
    return Formula(
        DataType.DATETIME_ARRAY if is_array else DataType.DATETIME,
        f"TOTIMEZONE({date_time}, {time_zone})",
    )


def _FROMTIMEZONE(is_array: bool, date_time: str, time_zone: str) -> Formula:
    return Formula(
        DataType.DATETIME_ARRAY if is_array else DataType.DATETIME,
        f"FROMTIMEZONE({date_time}, {time_zone})",
    )


def _TOMAP(data_type: MapDataType, array: str, table: str) -> Formula:
    return Formula(data_type, f"TOMAP({array}, {table})")
