import dature
from dature.type_aliases import FieldMapping, TypeLoaderMap

from shvatka.common.config.models.paths import Paths

CONFIG_FILE_NAME = "config.yml"


def config_source(
    paths: Paths,
    field_mapping: FieldMapping | None = None,
    type_loaders: TypeLoaderMap | None = None,
) -> dature.Yaml11Source:
    return dature.Yaml11Source(
        file=paths.config_path / CONFIG_FILE_NAME,
        name_style="lower_kebab",
        field_mapping=field_mapping,
        type_loaders=type_loaders,
        expand_env_vars="disabled",
        search_system_paths=False,
    )
