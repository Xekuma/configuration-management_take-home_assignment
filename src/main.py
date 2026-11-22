from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Union


SINGLE_LINE_COMMENT = "--"

NUMBER_RE = re.compile(r"[+-]?\d+")
RAW_IDENT_RE = re.compile(r"[_a-zA-Z][_a-zA-Z0-9]*")
VALID_NAME_RE = re.compile(r"^[_a-z]+$")
KEYWORDS = {"def": "DEF", "array": "ARRAY"}

Value = Union[int, list["Value"]]


class ConfigSyntaxError(Exception):
    def __init__(self, message: str, line: int, col: int) -> None:
        text = (
            f"Синтаксическая ошибка "
            f"(строка {line}, столбец {col}): {message}"
        )
        super().__init__(text)
        self.line = line
        self.col = col


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    line: int
    col: int


class Lexer:
    SINGLE_CHAR_TOKENS = {
        ":": "COLON",
        ";": "SEMICOLON",
        "(": "LPAREN",
        ")": "RPAREN",
        ",": "COMMA",
        "!": "BANG",
        "{": "LBRACE",
        "}": "RBRACE",
    }

    def __init__(self, text: str) -> None:
        self.text = text
        self.length = len(text)
        self.pos = 0
        self.line = 1
        self.col = 1

    def _advance(self, count: int = 1) -> None:
        for _ in range(count):
            if self.pos >= self.length:
                return
            if self.text[self.pos] == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            self.pos += 1

    def _is_word_boundary(self, index: int) -> bool:
        if index >= self.length:
            return True
        ch = self.text[index]
        return not (ch.isalnum() or ch == "_")

    def _starts_multiline(self) -> bool:
        return (
            self.text.startswith("=begin", self.pos)
            and self._is_word_boundary(self.pos + 6)
        )

    def _ends_multiline(self) -> bool:
        return (
            self.text.startswith("=end", self.pos)
            and self._is_word_boundary(self.pos + 4)
        )

    def _starts_single_comment(self) -> bool:
        return (
            bool(SINGLE_LINE_COMMENT)
            and self.text.startswith(SINGLE_LINE_COMMENT, self.pos)
        )

    def _skip_single_comment(self) -> None:
        while self.pos < self.length and self.text[self.pos] != "\n":
            self._advance()

    def _skip_multiline_comment(self) -> None:
        start_line, start_col = self.line, self.col
        self._advance(6)
        while self.pos < self.length:
            if self._ends_multiline():
                self._advance(4)
                return
            self._advance()
        raise ConfigSyntaxError(
            "Незакрытый многострочный комментарий (=begin без =end)",
            start_line,
            start_col,
        )

    def _read_number(self, match: re.Match[str]) -> Token:
        lexeme = match.group(0)
        end_pos = match.end()
        if end_pos < self.length:
            nxt = self.text[end_pos]
            if nxt.isalpha() or nxt == "_":
                msg = f"Некорректный формат числа рядом с '{lexeme}{nxt}'"
                raise ConfigSyntaxError(msg, self.line, self.col)
        token = Token("NUMBER", lexeme, self.line, self.col)
        self._advance(len(lexeme))
        return token

    def _read_identifier(self, match: re.Match[str]) -> Token:
        lexeme = match.group(0)
        if not VALID_NAME_RE.match(lexeme):
            msg = (
                f"Недопустимое имя '{lexeme}': "
                "разрешены только строчные латинские буквы и '_'"
            )
            raise ConfigSyntaxError(msg, self.line, self.col)
        kind = KEYWORDS.get(lexeme, "NAME")
        token = Token(kind, lexeme, self.line, self.col)
        self._advance(len(lexeme))
        return token

    def _next_token(self) -> Token | None:
        ch = self.text[self.pos]
        if ch.isspace():
            self._advance()
            return None
        if self._starts_multiline():
            self._skip_multiline_comment()
            return None
        if self._starts_single_comment():
            self._skip_single_comment()
            return None
        num_match = NUMBER_RE.match(self.text, self.pos)
        if num_match:
            return self._read_number(num_match)
        ident_match = RAW_IDENT_RE.match(self.text, self.pos)
        if ident_match:
            return self._read_identifier(ident_match)
        if ch in self.SINGLE_CHAR_TOKENS:
            kind = self.SINGLE_CHAR_TOKENS[ch]
            tok = Token(kind, ch, self.line, self.col)
            self._advance()
            return tok
        msg = f"Неожиданный символ {ch!r}"
        raise ConfigSyntaxError(msg, self.line, self.col)

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while self.pos < self.length:
            token = self._next_token()
            if token is not None:
                tokens.append(token)
        tokens.append(Token("EOF", "", self.line, self.col))
        return tokens


class Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.index = 0
        self.constants: dict[str, Value] = {}

    @property
    def current(self) -> Token:
        return self.tokens[self.index]

    def _advance(self) -> Token:
        tok = self.tokens[self.index]
        if self.index < len(self.tokens) - 1:
            self.index += 1
        return tok

    def _format_got(self, tok: Token) -> str:
        if tok.kind == "EOF":
            return "конец файла"
        return repr(tok.value)

    def _expect(self, kind: str, expected_desc: str) -> Token:
        tok = self.current
        if tok.kind != kind:
            got = self._format_got(tok)
            msg = f"Ожидалось {expected_desc}, получено {got}"
            raise ConfigSyntaxError(msg, tok.line, tok.col)
        return self._advance()

    def parse(self) -> list[Value]:
        values: list[Value] = []
        while self.current.kind != "EOF":
            if self.current.kind == "DEF":
                self._parse_const_decl()
            else:
                values.append(self._parse_value())
        return values

    def _parse_const_decl(self) -> None:
        self._expect("DEF", "'def'")
        name_tok = self._expect("NAME", "имя константы")
        self._expect("COLON", "':'")
        value = self._parse_value()
        self._expect("SEMICOLON", "';'")
        self.constants[name_tok.value] = value

    def _parse_value(self) -> Value:
        tok = self.current
        if tok.kind == "NUMBER":
            self._advance()
            return int(tok.value)
        if tok.kind == "ARRAY":
            return self._parse_array()
        if tok.kind == "BANG":
            return self._parse_const_eval()
        got = self._format_got(tok)
        msg = (
            "Ожидалось значение "
            f"(число, массив или константа), получено {got}"
        )
        raise ConfigSyntaxError(msg, tok.line, tok.col)

    def _parse_array(self) -> list[Value]:
        self._expect("ARRAY", "'array'")
        self._expect("LPAREN", "'('")
        items: list[Value] = []
        if self.current.kind != "RPAREN":
            items.append(self._parse_value())
            while self.current.kind == "COMMA":
                self._advance()
                items.append(self._parse_value())
        self._expect("RPAREN", "')'")
        return items

    def _parse_const_eval(self) -> Value:
        self._expect("BANG", "'!'")
        self._expect("LBRACE", "'{'")
        name_tok = self._expect("NAME", "имя константы")
        self._expect("RBRACE", "'}'")
        if name_tok.value not in self.constants:
            msg = f"Необъявленная константа '{name_tok.value}'"
            raise ConfigSyntaxError(msg, name_tok.line, name_tok.col)
        return self.constants[name_tok.value]


def _append_xml_value(parent: ET.Element, value: Value) -> None:
    if isinstance(value, int):
        elem = ET.SubElement(parent, "number")
        elem.text = str(value)
        return
    arr_elem = ET.SubElement(parent, "array")
    for item in value:
        _append_xml_value(arr_elem, item)


def translate(text: str) -> str:
    tokens = Lexer(text).tokenize()
    values = Parser(tokens).parse()
    root = ET.Element("config")
    for value in values:
        _append_xml_value(root, value)
    ET.indent(root, space="  ")
    raw = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return raw.decode("utf-8")


def _configure_stdio() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Транслятор учебного конфигурационного языка в XML."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Путь к входному конфигурационному файлу",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    args = _build_arg_parser().parse_args(argv)
    input_path = Path(args.input)
    try:
        source_text = input_path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        msg = f"Ошибка чтения файла '{input_path}': {exc}"
        print(msg, file=sys.stderr)
        return 1
    try:
        xml_output = translate(source_text)
    except ConfigSyntaxError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(xml_output)
    return 0


if __name__ == "__main__":
    sys.exit(main())