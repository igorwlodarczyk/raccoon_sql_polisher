import argparse
import random
from enum import Enum
from pathlib import Path
from antlr4 import *
from colorama import init, Fore, Style
from raccoon_sql_polisher.lexer.PostgreSQLLexer import PostgreSQLLexer
from raccoon_sql_polisher.parser.PostgreSQLParser import PostgreSQLParser
from raccoon_sql_polisher.parser.PostgreSQLParserListener import (
    PostgreSQLParserListener,
)


class NodeType(Enum):
    KEYWORD = "Keyword"
    REGULAR = "Regular"
    DOT = "Dot"
    COMMA = "Comma"
    LEFT_PARENTHESIS = "Left parenthesis"
    RIGHT_PARENTHESIS = "Right parenthesis"
    STRING = "String"


class Formatter(PostgreSQLParserListener):
    def __init__(
            self,
            number_of_newlines_after_stmt: int = 2,
            ugly: bool = False,
            indent_after_keyword: bool = False,
            newline_after_comma: bool = False,
            indent: bool = False,
            *args,
            **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.formatted_code = ""
        self.__number_of_newlines_after_stmt = number_of_newlines_after_stmt
        self.prev_node_type = None
        self.ugly = ugly
        self.indent_after_keyword = indent_after_keyword
        self.create_table_stmt = False
        self.column_constraints = False
        self.newline_after_comma = newline_after_comma
        self.inside_select_clause = False
        self.indent = indent
        self.indent_str = "    "
        self.indent_level = 0
        self.new_line = True
        self.prev_node_text = ""
        self.inside_values_clause = False

    def get_leaf_nodes(self, ctx):
        if ctx.getChildCount() == 0:
            return [ctx]
        leaves = []
        for i in range(ctx.getChildCount()):
            leaves.extend(self.get_leaf_nodes(ctx.getChild(i)))
        return leaves

    @staticmethod
    def determine_node_type(node):
        node_type = NodeType.REGULAR
        keywords = [
            PostgreSQLParser.Having_clauseContext,
            PostgreSQLParser.Target_labelContext,
            PostgreSQLParser.Join_typeContext,
            PostgreSQLParser.Table_refContext,
            PostgreSQLParser.Join_qualContext,
            PostgreSQLParser.Group_clauseContext,
            PostgreSQLParser.Group_clauseContext,
            PostgreSQLParser.Using_clauseContext,
            PostgreSQLParser.Where_or_current_clauseContext,
            PostgreSQLParser.A_expr_andContext,
            PostgreSQLParser.DeletestmtContext,
            PostgreSQLParser.SelectstmtContext,
            PostgreSQLParser.InsertstmtContext,
            PostgreSQLParser.UpdatestmtContext,
            PostgreSQLParser.Where_clauseContext,
            PostgreSQLParser.Simple_select_pramaryContext,
            PostgreSQLParser.From_clauseContext,
            PostgreSQLParser.CreatestmtContext,
            PostgreSQLParser.Character_cContext,
            PostgreSQLParser.ColconstraintelemContext,
            PostgreSQLParser.Character_cContext,
            PostgreSQLParser.ColconstraintelemContext,
            PostgreSQLParser.ColconstraintelemContext,
            PostgreSQLParser.ConstdatetimeContext,
            PostgreSQLParser.ColconstraintelemContext,
            PostgreSQLParser.Values_clauseContext,
        ]
        node_parent = node.parentCtx
        if isinstance(
                node_parent, PostgreSQLParser.Func_applicationContext
        ) or node.getText() in ("(", ")"):
            if node.getText() == "(":
                node_type = NodeType.LEFT_PARENTHESIS
            else:
                node_type = NodeType.RIGHT_PARENTHESIS
        elif node.getText().startswith("'") and node.getText().endswith("'"):
            node_type = NodeType.STRING
        elif node.getText().lower() in ["avg", "count", "nosw"]:
            node_type = NodeType.KEYWORD
        elif node.getText() == ".":
            node_type = NodeType.DOT
        elif node.getText() == ",":
            node_type = NodeType.COMMA
        elif any(isinstance(node_parent, keyword) for keyword in keywords):
            node_type = NodeType.KEYWORD
        return node_type

    @staticmethod
    def random_case(text: str) -> str:
        return "".join(
            char.upper() if random.choice([True, False]) else char.lower()
            for char in text
        )

    def format_node(self, node) -> str:
        node_type = self.determine_node_type(node)
        node_text = node.getText()
        formatted_node_text = node_text
        if node_text.strip() == "":
            return ""

        if node_type is NodeType.KEYWORD:
            if node_text.upper() == "SELECT":
                self.inside_select_clause = True
            if node_text.upper() == "VALUES":
                self.inside_select_clause = False
                self.inside_values_clause = True
            elif node_text.upper() in ("FROM", "WHERE", "GROUP", "ORDER", "HAVING", "LIMIT", "OFFSET", "SET"):
                self.inside_select_clause = False
                self.inside_values_clause = False

        if not self.column_constraints:
            if node_type is NodeType.KEYWORD:
                if node_text.upper() == "VALUES":
                    formatted_node_text = "\n" + node_text.upper() + " "
                elif self.prev_node_type is None:
                    formatted_node_text = node_text.upper()
                elif (
                        self.prev_node_type is NodeType.REGULAR
                        or self.prev_node_type is NodeType.STRING
                ):
                    formatted_node_text = "\n" + node_text.upper()
                else:
                    formatted_node_text = " " + node_text.upper()
            elif node_type is NodeType.COMMA:
                if self.newline_after_comma and self.inside_select_clause:
                    formatted_node_text = node_text + "\n"
                else:
                    formatted_node_text = node_text + ""
            elif node_type is NodeType.DOT:
                formatted_node_text = node_text
            elif node_type is NodeType.LEFT_PARENTHESIS:
                if self.create_table_stmt:
                    self.column_constraints = True
                    formatted_node_text = " " + node_text + "\n"
                elif self.prev_node_type is NodeType.KEYWORD:
                    formatted_node_text = node_text
                else:
                    formatted_node_text = " " + node_text
            elif node_type is NodeType.RIGHT_PARENTHESIS:
                formatted_node_text = node_text
            elif node_type is NodeType.STRING:
                if self.prev_node_type is NodeType.LEFT_PARENTHESIS:
                    formatted_node_text = node_text
                else:
                    formatted_node_text = " " + node_text
            elif node_type is NodeType.REGULAR:
                if (
                        self.prev_node_type is NodeType.DOT
                        or self.prev_node_type is NodeType.LEFT_PARENTHESIS
                ):
                    formatted_node_text = node_text.lower()
                elif (
                        self.indent_after_keyword
                        and self.prev_node_type is NodeType.KEYWORD
                ):
                    formatted_node_text = "\n\t" + node_text.lower()
                else:
                    formatted_node_text = " " + node_text.lower()
        else:
            if node_type is NodeType.REGULAR:
                if self.prev_node_type is NodeType.LEFT_PARENTHESIS:
                    formatted_node_text = node_text.lower()
                elif self.prev_node_type is NodeType.REGULAR:
                    formatted_node_text = " " + node_text.lower()
                elif self.prev_node_type is NodeType.COMMA:
                    formatted_node_text = "\n" + node_text.lower()
                elif self.prev_node_type is NodeType.KEYWORD:
                    formatted_node_text = " " + node_text.lower()
                else:
                    formatted_node_text = node_text.lower()

            elif node_type is NodeType.KEYWORD:
                formatted_node_text = " " + node_text.upper()
            elif node_type is NodeType.LEFT_PARENTHESIS:
                formatted_node_text = node_text
            elif node_type is NodeType.RIGHT_PARENTHESIS:
                formatted_node_text = node_text
            elif node_type is NodeType.STRING:
                formatted_node_text = " " + node_text

        if self.ugly and node_type is not NodeType.STRING:
            formatted_node_text = self.random_case(formatted_node_text)
        self.prev_node_type = node_type
        if self.indent:
            upper_node_text = node_text.upper()

            if node_type is NodeType.KEYWORD:
                if upper_node_text in ("SELECT", "WHERE", "GROUP", "ORDER",
                                       "HAVING", "LIMIT", "OFFSET", "VALUES",
                                       "INSERT", "UPDATE", "CREATE", "SET",
                                       ):
                    formatted_node_text = "\n" + upper_node_text
                    self.indent_level = 1
                    self.new_line = True

                elif upper_node_text == "DELETE":
                    formatted_node_text = "DELETE"
                    self.indent_level = 1
                    self.new_line = False

                elif upper_node_text == "FROM":
                    if self.prev_node_type is NodeType.KEYWORD and self.prev_node_text.upper() == "DELETE":
                        formatted_node_text = " FROM"
                        self.new_line = False
                    else:
                        formatted_node_text = "\nFROM"
                        self.indent_level = 1
                        self.new_line = True

                elif upper_node_text in ("LEFT", "RIGHT", "INNER", "OUTER"):
                    formatted_node_text = "\n" + (self.indent_str * self.indent_level) + upper_node_text
                    self.new_line = False

                elif upper_node_text == "JOIN":
                    formatted_node_text = " JOIN" if not self.new_line else "\n" + (
                                self.indent_str * self.indent_level) + "JOIN"
                    self.indent_level = 1
                    self.new_line = False

                elif upper_node_text == "ON":
                    formatted_node_text = " ON"
                    self.new_line = False

                elif upper_node_text in ("AND", "OR"):
                    formatted_node_text = "\n" + (self.indent_str * self.indent_level) + upper_node_text
                    self.new_line = False

            elif node_type is NodeType.COMMA:
                if self.newline_after_comma and self.inside_select_clause:
                    if not self.indent:
                        formatted_node_text = node_text + "\n"
                    else:
                        formatted_node_text = node_text
                    self.new_line = True
                else:
                    formatted_node_text = node_text + " "
                    self.new_line = False


            elif node_type is NodeType.LEFT_PARENTHESIS:
                formatted_node_text = node_text
                self.indent_level += 1
                self.new_line = False

            elif node_type is NodeType.RIGHT_PARENTHESIS:
                formatted_node_text = node_text
                self.indent_level = max(self.indent_level - 1, 1)
                self.new_line = False

            elif self.new_line and node_type not in (NodeType.KEYWORD, NodeType.COMMA):
                formatted_node_text = "\n" + (self.indent_str * self.indent_level) + node_text.strip()
                self.new_line = False
            else:
                if self.prev_node_type is NodeType.DOT or node_type is NodeType.DOT:
                    formatted_node_text = node_text.strip()
                else:
                    formatted_node_text = " " + node_text.strip()

                self.new_line = False

        if self.indent and self.inside_values_clause:
            if node_text == "(":
                formatted_node_text = "\n" + (self.indent_str) + node_text
                self.new_line = False
            elif node_text == ")":
                formatted_node_text = node_text
                self.new_line = False
            elif node_text == ",":
                formatted_node_text = node_text + (self.indent_str)
                self.new_line = False

        self.prev_node_text = node_text
        self.prev_node_type = node_type

        return formatted_node_text

    def enterStmt(self, ctx: PostgreSQLParser.StmtContext):
        leaves = self.get_leaf_nodes(ctx)
        if "CREATE" in leaves[0].getText().upper():
            self.create_table_stmt = True
        for leaf in leaves:
            self.formatted_code += self.format_node(leaf)

    def exitStmt(self, ctx: PostgreSQLParser.StmtContext):
        self.formatted_code += ";"
        if self.create_table_stmt:
            self.formatted_code = (
                    self.formatted_code[:-2] + "\n" + self.formatted_code[-2:]
            )
        self.formatted_code += "\n" * self.__number_of_newlines_after_stmt
        self.prev_node_type = None
        self.create_table_stmt = False
        self.column_constraints = False

    def exitRoot(self, ctx: PostgreSQLParser.RootContext):
        self.formatted_code = self.formatted_code[
                              : -self.__number_of_newlines_after_stmt + 1
                              ]

    def get_formatted_code(self):
        return self.formatted_code


def __create_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Raccoon SQL Polisher: "
            "A formatter for PostgreSQL SQL queries that "
            "enhances readability and enforces a consistent coding style."
        )
    )
    parser.add_argument(
        "path",
        help="Path to the file or directory containing the SQL code to be formatted.",
    )
    parser.add_argument(
        "--ugly",
        help=(
            "Randomly changes the case of letters (upper/lower) in the formatted SQL code. "
            "If set, this option enables the effect. "
            "(action='store_true')"
        ),
        action="store_true",
    )
    parser.add_argument(
        "--newline-after-comma",
        help="Inserts newline after each comma in SELECT clause.",
        action="store_true",
    )
    parser.add_argument(
        "--indent",
        help="Indent SQL statements for better readability.",
        action="store_true",
    )

    return parser


def __get_sql_files_to_format(path: str):
    p = Path(path)

    if p.is_dir():
        return list(p.rglob("*.sql"))
    elif p.is_file():
        return [p]
    else:
        raise FileNotFoundError(
            f"Path '{path}' does not exist or is not a valid file/directory. 💀"
        )


def format_sql_file(sql_file_path: Path, ugly: bool = False, newline_after_comma: bool = False, indent: bool = False):
    with open(sql_file_path, "r") as file:
        file_content = file.read()
    input_stream = InputStream(file_content)
    lexer = PostgreSQLLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = PostgreSQLParser(token_stream)

    tree = parser.root()

    listener = Formatter(ugly=ugly, newline_after_comma=newline_after_comma, indent=indent)

    walker = ParseTreeWalker()
    walker.walk(listener, tree)
    formatted_code = listener.get_formatted_code()
    with open(sql_file_path, "w") as output:
        output.write(formatted_code)
    print(
        f"{Style.BRIGHT}{Fore.LIGHTWHITE_EX}raccoonified {sql_file_path.name} 🦝🦝🦝{Style.RESET_ALL}"
    )


def main():
    init()
    parser = __create_parser()
    args = parser.parse_args()

    sql_files = __get_sql_files_to_format(args.path)
    for file in sql_files:
        format_sql_file(file, args.ugly,
                        args.newline_after_comma,
                        indent=args.indent)
