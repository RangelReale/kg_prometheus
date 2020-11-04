from typing import Any, Optional, Mapping

from kubragen.builder import Builder
from kubragen.configfile import ConfigFile, ConfigFileOutput, ConfigFileOutput_Dict
from kubragen.exception import InvalidParamError
from kubragen.merger import Merger
from kubragen.option import OptionDef
from kubragen.options import OptionGetter, Options, option_root_get


class PrometheusConfigFileOptions(Options):
    """
    Options for Prometheus config file.

    .. list-table::
        :header-rows: 1

        * - config.extra_config
          - extra config to add fo config file
          - Mapping
          - ```{}```
    """
    def define_options(self) -> Optional[Any]:
        """
        Declare the options for the Prometheus config file.

        :return: The supported options
        """
        return {
            'config': {
                'extra_config': OptionDef(default_value={}, allowed_types=[Mapping]),
            },
        }


class PrometheusConfigFile(ConfigFile):
    """
    Prometheus main configuration file in YAML format.
    """
    options: PrometheusConfigFileOptions

    def __init__(self, options: Optional[PrometheusConfigFileOptions] = None):
        if options is None:
            options = PrometheusConfigFileOptions()
        self.options = options

    def option_get(self, name: str):
        return option_root_get(self.options, name)

    def get_value(self, options: OptionGetter) -> ConfigFileOutput:
        ret = {}

        extra_config = self.option_get('config.extra_config')
        if extra_config is not None:
            Merger.merge(ret, extra_config)

        return ConfigFileOutput_Dict(ret)
