"""Validated, immutable theme interchange model."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from types import MappingProxyType
from typing import Mapping


SCHEMA_VERSION = 1
MAX_JSON_BYTES = 64 * 1024
COLOR_TOKENS = (
    "background", "sidebar", "surface", "surface_alt", "player_background",
    "text_primary", "text_secondary", "text_disabled", "accent", "accent_hover",
    "accent_foreground", "border", "selection", "focus", "success", "warning",
    "error", "slider_track", "slider_fill", "card_background", "card_hover",
    "menu_background", "cover_start", "cover_middle", "cover_end", "cover_foreground",
    "hero_start", "hero_middle", "hero_end",
)

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
_ROOT_KEYS = {"schema_version", "id", "name", "author", "colors"}


def _has_control(text: str) -> bool:
    return any(ord(char) < 32 or 0x7F <= ord(char) <= 0x9F or 0xD800 <= ord(char) <= 0xDFFF
               for char in text)


class ThemeValidationError(ValueError):
    """Raised when a theme definition violates the public theme contract."""


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ThemeValidationError(f"Chave JSON duplicada: {key}.")
        result[key] = value
    return result


def _check_json_depth(raw: str, limit: int = 2) -> None:
    depth = 0
    in_string = False
    escaped = False
    for char in raw:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
            if depth > limit:
                raise ThemeValidationError("O JSON do tema excede a profundidade permitida.")
        elif char in "]}":
            depth -= 1
            if depth < 0:
                raise ThemeValidationError("JSON inválido para um tema.")
    if in_string or depth != 0:
        raise ThemeValidationError("JSON inválido para um tema.")


@dataclass(frozen=True, slots=True)
class ThemeDefinition:
    id: str
    name: str
    colors: Mapping[str, str]
    author: str | None = None

    def __post_init__(self):
        if not isinstance(self.id, str) or not _ID_RE.fullmatch(self.id):
            raise ThemeValidationError("O identificador deve usar letras minúsculas, números e hífens.")
        if not isinstance(self.name, str):
            raise ThemeValidationError("O nome do tema deve ser texto.")
        name = self.name.strip()
        if not name or len(name) > 60 or _has_control(name):
            raise ThemeValidationError("O nome deve ter de 1 a 60 caracteres imprimíveis.")
        if self.author is not None and (
            not isinstance(self.author, str) or not self.author.strip()
            or len(self.author.strip()) > 80
            or _has_control(self.author)
        ):
            raise ThemeValidationError("O autor deve ter até 80 caracteres imprimíveis.")
        if not isinstance(self.colors, Mapping):
            raise ThemeValidationError("As cores devem ser informadas em um objeto.")
        unknown = set(self.colors) - set(COLOR_TOKENS)
        missing = set(COLOR_TOKENS) - set(self.colors)
        if unknown:
            raise ThemeValidationError(f"Token de cor desconhecido: {sorted(unknown)[0]}.")
        if missing:
            raise ThemeValidationError(f"Token de cor ausente: {sorted(missing)[0]}.")
        normalized = {}
        for token in COLOR_TOKENS:
            value = self.colors[token]
            if not isinstance(value, str) or not _HEX_RE.fullmatch(value):
                raise ThemeValidationError(f"A cor {token} deve usar o formato #RRGGBB.")
            normalized[token] = value.upper()
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "author", self.author.strip() if self.author is not None else None)
        object.__setattr__(self, "colors", MappingProxyType(normalized))

    @classmethod
    def from_json(cls, data: str | bytes | bytearray) -> "ThemeDefinition":
        if isinstance(data, str):
            raw = data
            try:
                encoded = raw.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise ThemeValidationError("O tema deve conter texto UTF-8 válido.") from exc
        elif isinstance(data, (bytes, bytearray)):
            encoded = bytes(data)
            try:
                raw = encoded.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ThemeValidationError("O tema deve conter texto UTF-8 válido.") from exc
        else:
            raise ThemeValidationError("O tema deve ser recebido como JSON em texto ou bytes.")
        if len(encoded) > MAX_JSON_BYTES:
            raise ThemeValidationError("O arquivo de tema excede o limite de 64 KiB.")
        _check_json_depth(raw)
        try:
            document = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
        except ThemeValidationError:
            raise
        except (json.JSONDecodeError, RecursionError) as exc:
            raise ThemeValidationError("JSON inválido para um tema.") from exc
        if not isinstance(document, dict):
            raise ThemeValidationError("A raiz do JSON deve ser um objeto.")
        unknown = set(document) - _ROOT_KEYS
        if unknown:
            raise ThemeValidationError(f"Campo não permitido no tema: {sorted(unknown)[0]}.")
        missing = {"schema_version", "id", "name", "colors"} - set(document)
        if missing:
            raise ThemeValidationError(f"Campo obrigatório ausente: {sorted(missing)[0]}.")
        if type(document["schema_version"]) is not int or document["schema_version"] != SCHEMA_VERSION:
            raise ThemeValidationError("Versão de contrato de tema não suportada.")
        if "author" in document and not isinstance(document["author"], str):
            raise ThemeValidationError("O campo author deve ser texto quando informado.")
        if not isinstance(document["colors"], dict):
            raise ThemeValidationError("O campo colors deve ser um objeto.")
        return cls(
            id=document["id"], name=document["name"], colors=document["colors"],
            author=document.get("author"),
        )

    def to_json(self) -> str:
        document = {
            "schema_version": SCHEMA_VERSION,
            "id": self.id,
            "name": self.name,
        }
        if self.author is not None:
            document["author"] = self.author
        document["colors"] = {token: self.colors[token] for token in COLOR_TOKENS}
        return json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
