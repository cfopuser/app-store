from dataclasses import dataclass
from typing import Any, Callable

from .apkmirror import APKMirrorSource
from .aptoide import AptoideSource
from .apkpure import APKPureSource
from .github import GitHubSource


@dataclass(frozen=True)
class SourceDefinition:
    factory: Callable[[dict], Any]
    lookup_field: str = "package_name"


SOURCE_DEFINITIONS: dict[str, SourceDefinition] = {
    "apkmirror": SourceDefinition(factory=lambda _cfg: APKMirrorSource()),
    "aptoide": SourceDefinition(factory=lambda _cfg: AptoideSource()),
    "apkpure": SourceDefinition(
        factory=lambda cfg: APKPureSource(
            file_type=cfg.get("apkpure_file_type", "XAPK"),
            version=cfg.get("apkpure_version", "latest"),
        )
    ),
    "github": SourceDefinition(factory=lambda _cfg: GitHubSource(), lookup_field="repo"),
}


def create_source(source_name: str, app_config: dict) -> tuple[str, Any, str]:
    normalized = (source_name or "apkmirror").lower()
    source_def = SOURCE_DEFINITIONS.get(normalized, SOURCE_DEFINITIONS["apkmirror"])

    lookup_value = app_config.get(source_def.lookup_field)
    if not lookup_value:
        raise ValueError(
            f"'{source_def.lookup_field}' field is required for source '{normalized}'."
        )

    return normalized, source_def.factory(app_config), lookup_value
