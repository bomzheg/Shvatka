import dature
from dature.type_aliases import FieldMapping, TypeLoaderMap

from shvatka.common.config.models.paths import Paths

CONFIG_FILE_NAME = "config.yml"


def config_source(
    paths: Paths,
    prefix: str | None = None,
    field_mapping: FieldMapping | None = None,
    type_loaders: TypeLoaderMap | None = None,
) -> dature.Yaml11Source:
    """Build a dature source over the app's ``config.yml``.

    The whole app is configured by one file, so every loader below reads its own
    subtree of it: ``prefix`` is the dot-separated path of the section a loader
    owns (``"db"``, ``"api.auth"``, ...), and ``None`` means the file root.

    YAML 1.1 (not 1.2) is intentional — it is the dialect PyYAML implemented, so
    configs written for the previous parser keep resolving to the same values.
    Env var expansion stays off for the same reason: values such as a webhook
    secret may legitimately contain ``$``.
    """
    return dature.Yaml11Source(
        file=paths.config_path / CONFIG_FILE_NAME,
        prefix=prefix,
        name_style="lower_kebab",
        field_mapping=field_mapping,
        type_loaders=type_loaders,
        expand_env_vars="disabled",
        search_system_paths=False,
    )
