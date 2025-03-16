import pytest
from raccoon_sql_polisher.formatter import format_sql_file


@pytest.mark.parametrize(
    "input_query, expected_formatted_query",
    [
        (
            f"sElect \nname, age from users WHERE age>10 AND name = 'igor'",
            "SELECT name, age\n" "FROM users\n" "WHERE age > 10 AND name = 'igor';\n",
        )
    ],
)
def test_formatter(input_query, expected_formatted_query, tmp_path):
    sql_file = tmp_path / "input.sql"
    with open(sql_file, "w") as file:
        file.write(input_query)

    format_sql_file(sql_file)

    with open(sql_file, "r") as output_file:
        formatted_code = output_file.read()
        assert formatted_code == expected_formatted_query
