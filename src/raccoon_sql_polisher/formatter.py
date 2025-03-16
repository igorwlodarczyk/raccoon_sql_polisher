import argparse
from pathlib import Path
from antlr4 import *
from colorama import init, Fore, Style
from raccoon_sql_polisher.lexer.PostgreSQLLexer import PostgreSQLLexer
from raccoon_sql_polisher.parser.PostgreSQLParser import PostgreSQLParser
from raccoon_sql_polisher.parser.PostgreSQLParserListener import (
    PostgreSQLParserListener,
)


class Formatter(PostgreSQLParserListener):
    def __init__(
        self, output_file: Path, number_of_newlines_after_stmt: int = 2, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.formatted_code = ""
        self.__number_of_newlines_after_stmt = number_of_newlines_after_stmt
        self.output_file = output_file

    # Dev tools
    @staticmethod
    def print_tree(ctx):
        print(ctx.toStringTree(recog=PostgreSQLParser))

    def get_leaf_nodes(self, ctx):
        if ctx.getChildCount() == 0:
            return [ctx]
        leaves = []
        for i in range(ctx.getChildCount()):
            leaves.extend(self.get_leaf_nodes(ctx.getChild(i)))
        return leaves

    # General
    @staticmethod
    def check_context(ctx, expected_context):
        parent_context = ctx.parentCtx
        is_in_where_clause = False

        while parent_context is not None:
            if isinstance(parent_context, expected_context):
                is_in_where_clause = True
                break
            parent_context = parent_context.parentCtx
        return is_in_where_clause

    def exitStmt(self, ctx: PostgreSQLParser.StmtContext):
        self.formatted_code += ";"
        self.formatted_code += "\n" * self.__number_of_newlines_after_stmt

    def exitRoot(self, ctx: PostgreSQLParser.RootContext):
        self.formatted_code = self.formatted_code[
            : -self.__number_of_newlines_after_stmt + 1
        ]
        with open(self.output_file, "w") as output:
            output.write(self.formatted_code)
        print(
            f"{Style.BRIGHT}{Fore.LIGHTWHITE_EX}raccoonified {self.output_file.name} 🦝🦝🦝{Style.RESET_ALL}"
        )

    def enterTarget_list(self, ctx: PostgreSQLParser.Target_listContext):
        columns = [
            child.getText().lower()
            for child in ctx.getChildren()
            if child.getText() != ","
        ]

        self.formatted_code += " " + ", ".join(columns)

    def enterSimple_select_pramary(
        self, ctx: PostgreSQLParser.Simple_select_pramaryContext
    ):
        self.formatted_code += ctx.getChild(0).getText().upper()

    def enterSelectstmt(self, ctx: PostgreSQLParser.SelectstmtContext):
        # print(ctx.toStringTree(recog=PostgreSQLParser))
        ...

    def enterFrom_clause(self, ctx: PostgreSQLParser.From_clauseContext):
        self.formatted_code += "\n" + ctx.getChild(0).getText().upper()

    def enterTable_ref(self, ctx: PostgreSQLParser.Table_refContext):
        self.formatted_code += f" {ctx.getText()}"

    def enterWhere_clause(self, ctx: PostgreSQLParser.Where_clauseContext):
        self.formatted_code += "\n" + ctx.getChild(0).getText().upper()

    def enterA_expr_and(self, ctx: PostgreSQLParser.A_expr_andContext):
        expected_context = PostgreSQLParser.Where_clauseContext
        is_in_where_clause = self.check_context(ctx, expected_context)

        if is_in_where_clause:
            nodes = self.get_leaf_nodes(ctx)
            for node in nodes:
                node_text = node.getText()
                if node_text in ("OR", "AND", "NOT"):
                    node_text = node_text.upper()
                else:
                    node_text = node_text.lower()
                self.formatted_code += " " + node_text


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


def format_sql_file(sql_file_path: Path):
    with open(sql_file_path, "r") as file:
        file_content = file.read()
    input_stream = InputStream(file_content)
    lexer = PostgreSQLLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = PostgreSQLParser(token_stream)

    tree = parser.root()

    listener = Formatter(sql_file_path)

    walker = ParseTreeWalker()
    walker.walk(listener, tree)


def main():
    parser = __create_parser()
    args = parser.parse_args()

    sql_files = __get_sql_files_to_format(args.path)
    for file in sql_files:
        format_sql_file(file)
