from typing import Mapping

from kubragen.configfile import ConfigFile
from kubragen.kdatahelper import KDataHelper_Volume
from kubragen.option import OptionDef, OptionDefFormat
from kubragen.options import Options


class PrometheusOptions(Options):
    """
    Options for the Prometheus builder.

    .. list-table::
        :header-rows: 1

        * - option
          - description
          - allowed types
          - default value
        * - basename
          - object names prefix
          - str
          - ```rabbitmq```
        * - namespace
          - namespace
          - str
          - ```rabbitmq```
        * - config |rarr| prometheus_config
          - prometheus.yml file
          - :class:`kubragen.configfile.ConfigFile`
          - :class:`kg_prometheus.PrometheusConfigFile`
        * - config |rarr| service_port
          - service port
          - int
          - ```9090```
        * - config |rarr| authorization |rarr| serviceaccount_create
          - whether to create a service account
          - bool
          - ```True```
        * - config |rarr| authorization |rarr| serviceaccount_use
          - service account to use if not creating
          - str
          -
        * - config |rarr| authorization |rarr| roles_create
          - whether create roles
          - bool
          - ```True```
        * - config |rarr| authorization |rarr| roles_bind
          - whether to bind roles to service account
          - bool
          - ```True```
        * - container |rarr| init-chown-data
          - init-chown-data container image
          - str
          - ```debian:<version>```
        * - container |rarr| prometheus
          - rabbitmq container image
          - str
          - ```prom/prometheus:<version>```
        * - kubernetes |rarr| volumes |rarr| data
          - Kubernetes data volume
          - dict, :class:`KData_Value`, :class:`KData_ConfigMap`, :class:`KData_Secret`
          -
        * - kubernetes |rarr| resources |rarr| statefulset
          - Kubernetes StatefulSet resources
          - dict
          -
    """
    def define_options(self):
        """
        Declare the options for the Prometheus builder.

        :return: The supported options
        """
        return {
            'basename': OptionDef(required=True, default_value='prometheus', allowed_types=[str]),
            'namespace': OptionDef(required=True, default_value='prometheus', allowed_types=[str]),
            'config': {
                'prometheus_config': OptionDef(required=True, allowed_types=[str, ConfigFile]),
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
