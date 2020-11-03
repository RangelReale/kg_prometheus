from typing import Mapping

from kubragen.kdatahelper import KDataHelper_Volume
from kubragen.option import OptionDef, OptionDefFormat, OptionDefaultValue
from kubragen.options import Options


class PrometheusOptions(Options):
    def define_options(self):
        return {
            'basename': OptionDef(required=True, default_value='prometheus', allowed_types=[str]),
            'namespace': OptionDef(required=True, default_value='prometheus', allowed_types=[str]),
            'config': {
                'prometheus_config': OptionDef(required=True, allowed_types=[str]),
                'service_port': OptionDef(required=True, default_value=9090, allowed_types=[int]),
                'authorization': {
                    'serviceaccount_create': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                    'serviceaccount_use': OptionDef(allowed_types=[str]),
                    'roles_create': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                    'roles_bind': OptionDef(required=True, default_value=True, allowed_types=[bool]),
                },
            },
            'container': {
                'init-chown-data': OptionDef(required=True, default_value='debian:9', allowed_types=[str]),
                'prometheus': OptionDef(required=True, default_value='prom/prometheus:v2.21.0', allowed_types=[str]),
            },
            'kubernetes': {
                'volumes': {
                    'data': OptionDef(required=True, format=OptionDefFormat.KDATA_VOLUME,
                                      allowed_types=[Mapping, *KDataHelper_Volume.allowed_kdata()]),
                },
                'resources': {
                    'statefulset': OptionDef(allowed_types=[Mapping]),
                }
            },
        }
