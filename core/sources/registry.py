from dataclasses import dataclass
from typing import Any, Callable

from .apkmirror import APKMirrorSource
from .aptoide import AptoideSource
from .aurora import AuroraSource
from .apkpure import APKPureSource
from .apkpure_mobile import APKPureMobileSource
from .github import GitHubSource


@dataclass(frozen=True)
class SourceDefinition:
    factory: Callable[[dict], Any]
    lookup_field: str = "package_name"


SOURCE_DEFINITIONS: dict[str, SourceDefinition] = {
    "apkmirror": SourceDefinition(factory=lambda _cfg: APKMirrorSource()),
    "aptoide": SourceDefinition(factory=lambda _cfg: AptoideSource()),
    "aurora": SourceDefinition(
        factory=lambda cfg: AuroraSource(
            timeout=cfg.get("aurora_timeout", 30),
            locale=cfg.get("aurora_locale", "en_US"),
            timezone=cfg.get("aurora_timezone", "UTC"),
            device_codename=cfg.get("aurora_device_codename", "bacon"),
            dispenser_url=cfg.get("aurora_dispenser_url", "https://auroraoss.com/api/auth"),
            dispenser_user_agent=cfg.get("aurora_user_agent", "com.aurora.store-4.8.1-73"),
        )
    ),
    "apkpure": SourceDefinition(
        factory=lambda cfg: APKPureSource(
            file_type=cfg.get("apkpure_file_type", "XAPK"),
            version=cfg.get("apkpure_version", "latest"),
        )
    ),
    "apkpure_mobile": SourceDefinition(factory=lambda _cfg: APKPureMobileSource()),
    "github": SourceDefinition(factory=lambda _cfg: GitHubSource(), lookup_field="repo"),
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
