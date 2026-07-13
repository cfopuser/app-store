from dataclasses import dataclass
from typing import Any, Callable

from .apkmirror import APKMirrorSource
from .aptoide import AptoideSource
from .apkpure import APKPureSource
from .apkpure_mobile import APKPureMobileSource
from .github import GitHubSource
from .apkcombo import APKComboSource
from .whatsapp_official import WhatsAppOfficialSource
from .custom_fallback import CustomFallbackSource
from .uptodown import UptodownSource
@dataclass(frozen=True)
class SourceDefinition:
    factory: Callable[[dict], Any]
    lookup_field: str = "package_name"


SOURCE_DEFINITIONS: dict[str, SourceDefinition] = {
    "whatsapp_official": SourceDefinition(factory=lambda _cfg: WhatsAppOfficialSource()),
    "apkmirror": SourceDefinition(factory=lambda _cfg: APKMirrorSource()),
    "aptoide": SourceDefinition(factory=lambda _cfg: AptoideSource()),
    "apkcombo": SourceDefinition(factory=lambda _cfg: APKComboSource()),
    "apkpure": SourceDefinition(
        factory=lambda cfg: APKPureSource(
            file_type=cfg.get("apkpure_file_type", "XAPK"),
            version=cfg.get("apkpure_version", "latest"),
        )
    ),
    "apkpure_mobile": SourceDefinition(factory=lambda _cfg: APKPureMobileSource()),
    "github": SourceDefinition(
        factory=lambda cfg: GitHubSource(
            asset_regex=cfg.get("github_asset_regex")
        ),
        lookup_field="repo",
    ),
    "custom_fallback": SourceDefinition(
        factory=lambda cfg: CustomFallbackSource(uptodown_subdomain=cfg.get("uptodown_subdomain")),
        lookup_field="package_name"
    ),
    "uptodown": SourceDefinition(
        factory=lambda cfg: UptodownSource(uptodown_subdomain=cfg.get("uptodown_subdomain")),
        lookup_field="package_name"
    ),
}


def create_source(source_name: str, app_config: dict) -> tuple[str, Any, str]:
    normalized = (source_name or "apkmirror").lower()
    source_def = SOURCE_DEFINITIONS.get(normalized)
    if source_def is None:
        normalized = "apkmirror"
        source_def = SOURCE_DEFINITIONS[normalized]

    lookup_value = app_config.get(source_def.lookup_field)
    if not lookup_value:
        raise ValueError(
            f"'{source_def.lookup_field}' field is required for source '{normalized}'."
        )

    return normalized, source_def.factory(app_config), lookup_value
