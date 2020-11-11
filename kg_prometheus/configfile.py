from typing import Any, Optional, Mapping, Sequence

from kubragen.configfile import ConfigFile, ConfigFileOutput, ConfigFileOutput_Dict, ConfigFile_Extend, \
    ConfigFileExtensionData, ConfigFileExtension
from kubragen.helper import QuotedStr
from kubragen.merger import Merger
from kubragen.option import OptionDef
from kubragen.options import OptionGetter, Options, option_root_get


class PrometheusConfigFileOptions(Options):
    """
    Options for Prometheus config file.

    .. list-table::
        :header-rows: 1

        * - option
          - description
          - allowed types
          - default value
        * - config.extra_config
          - extra config to add to config file
          - Mapping
          - ```{}```
        * - scrape.prometheus.enabled
          - whether prometheus scrape is enabled
          - bool
          - ```True```
        * - scrape.prometheus.job_name
          - prometheus scrape job name
          - str
          - ```prometheus```
        * - scrape.prometheus.extra_config
          - extra config to add to prometheus job
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
                'merge_config': OptionDef(default_value={}, allowed_types=[Mapping]),
            },
            'scrape': {
                'prometheus': {
                    'enabled': OptionDef(required=True, default_value=False, allowed_types=[bool]),
                    'job_name': OptionDef(default_value='prometheus', allowed_types=[str]),
                    'extra_config': OptionDef(default_value={}, allowed_types=[Mapping]),
                }
            },
        }


class PrometheusConfigFile(ConfigFile_Extend):
    """
    Prometheus main configuration file in YAML format.
    """
    options: PrometheusConfigFileOptions

    def __init__(self, options: Optional[PrometheusConfigFileOptions] = None,
                 extensions: Optional[Sequence[ConfigFileExtension]] = None):
        super().__init__(extensions)
        if options is None:
            options = PrometheusConfigFileOptions()
        self.options = options

    def option_get(self, name: str):
        return option_root_get(self.options, name)

    def init_value(self, options: OptionGetter) -> ConfigFileExtensionData:
        ret = ConfigFileExtensionData({})

        if self.option_get('scrape.prometheus.enabled'):
            Merger.merge(ret.data, {
                'scrape_configs': [Merger.merge({
                    'job_name': QuotedStr(self.option_get('scrape.prometheus.job_name')),
                    'static_configs': [{
                        'targets': [
                            'localhost:9090',
                        ]
                    }],
                }, self.option_get('scrape.prometheus.extra_config'))]
            })

        return ret

    def finish_value(self, options: OptionGetter, data: ConfigFileExtensionData) -> ConfigFileOutput:
        if self.option_get('config.merge_config') is not None:
            Merger.merge(data.data, self.option_get('config.merge_config'))
        return ConfigFileOutput_Dict(data.data)
