from typing import List, Optional, Sequence

from kubragen import KubraGen
from kubragen.builder import Builder
from kubragen.configfile import ConfigFileRenderMulti, ConfigFileRender_RawStr, ConfigFileRender_Yaml
from kubragen.data import ValueData
from kubragen.exception import InvalidParamError, InvalidNameError
from kubragen.helper import LiteralStr
from kubragen.kdatahelper import KDataHelper_Volume
from kubragen.object import ObjectItem, Object
from kubragen.types import TBuild, TBuildItem

from .configfile import PrometheusConfigFile
from .option import PrometheusOptions


class PrometheusBuilder(Builder):
    """
    Prometheus builder.

    Based on `prometheus-community/helm-charts <https://github.com/prometheus-community/helm-charts>`_.

    .. list-table::
        :header-rows: 1

        * - build
          - description
        * - BUILD_ACCESSCONTROL
          - creates service account, roles, and roles bindings
        * - BUILD_CONFIG
          - creates ConfigMap
        * - BUILD_SERVICE
          - creates StatefulSet and Services

    .. list-table::
        :header-rows: 1

        * - build item
          - description
        * - BUILDITEM_SERVICE_ACCOUNT
          - ServiceAccount
        * - BUILDBUILDITEM_CLUSTER_ROLEITEM_ROLE
          - ClusterRole
        * - BUILDITEM_CLUSTER_ROLE_BINDING
          - ClusterRoleBinding
        * - BUILDITEM_CONFIG
          - ConfigMap
        * - BUILDITEM_STATEFULSET
          - StatefulSet
        * - BUILDITEM_SERVICE
          - Service

    .. list-table::
        :header-rows: 1

        * - object name
          - description
          - default value
        * - config
          - ConfigMap
          - ```<basename>-config```
        * - service
          - Service
          - ```<basename>```
        * - service-account
          - ServiceAccount
          - ```<basename>```
        * - cluster-role
          - ClusterRole
          - ```<basename>```
        * - cluster-role-binding
          - ClusterRoleBinding
          - ```<basename>```
        * - statefulset
          - StatefulSet
          - ```<basename>```
        * - pod-label-all
          - label *app* to be used by selection
          - ```<basename>```
    """
    options: PrometheusOptions
    configfile: Optional[str]
    _namespace: str

    SOURCE_NAME = 'kg_prometheus'

    BUILD_ACCESSCONTROL = TBuild('accesscontrol')
    BUILD_CONFIG = TBuild('config')
    BUILD_SERVICE = TBuild('service')

    BUILDITEM_SERVICE_ACCOUNT = TBuildItem('service-account')
    BUILDITEM_CLUSTER_ROLE = TBuildItem('cluster-role')
    BUILDITEM_CLUSTER_ROLE_BINDING = TBuildItem('cluster-role-binding')
    BUILDITEM_CONFIG = TBuildItem('config')
    BUILDITEM_STATEFULSET = TBuildItem('statefulset')
    BUILDITEM_SERVICE = TBuildItem('service')

    def __init__(self, kubragen: KubraGen, options: Optional[PrometheusOptions] = None):
        super().__init__(kubragen)
        if options is None:
            options = PrometheusOptions()
        self.options = options
        self.configfile = None

        self._namespace = self.option_get('namespace')

        if self.option_get('config.authorization.serviceaccount_create') is not False:
            serviceaccount_name = self.basename()
        else:
            serviceaccount_name = self.option_get('config.authorization.serviceaccount_use')
            if serviceaccount_name == '':
                serviceaccount_name = None

        if self.option_get('config.authorization.roles_create') is not False:
            role_name = self.basename()
        else:
            role_name = None

        if self.option_get('config.authorization.roles_bind') is not False:
            if serviceaccount_name is None:
                raise InvalidParamError('To bind roles a service account is required')
            if role_name is None:
                raise InvalidParamError('To bind roles the role must be created')
            rolebinding_name = self.basename()
        else:
            rolebinding_name = None

        self.object_names_init({
            'config': self.basename('-config'),
            'service': self.basename(),
            'service-account': serviceaccount_name,
            'cluster-role': role_name,
            'cluster-role-binding': rolebinding_name,
            'statefulset': self.basename(),
            'pod-label-app': self.basename(),
        })

    def option_get(self, name: str):
        return self.kubragen.option_root_get(self.options, name)

    def configfile_get(self) -> str:
        if self.configfile is None:
            configfile = self.option_get('config.prometheus_config')
            if configfile is None:
                configfile = PrometheusConfigFile()
            if isinstance(configfile, str):
                self.configfile = configfile
            else:
                configfilerender = ConfigFileRenderMulti([
                    ConfigFileRender_Yaml(),
                    ConfigFileRender_RawStr()
                ])
                self.configfile = configfilerender.render(configfile.get_value(self))
        return self.configfile

    def basename(self, suffix: str = ''):
        return '{}{}'.format(self.option_get('basename'), suffix)

    def namespace(self):
        return self._namespace

    def build_names(self) -> Sequence[TBuild]:
        return [self.BUILD_ACCESSCONTROL, self.BUILD_CONFIG, self.BUILD_SERVICE]

    def build_names_required(self) -> Sequence[TBuild]:
        ret = [self.BUILD_CONFIG, self.BUILD_SERVICE]
        if self.option_get('config.authorization.serviceaccount_create') is not False or \
                self.option_get('config.authorization.roles_create') is not False:
            ret.append(self.BUILD_ACCESSCONTROL)
        return ret

    def builditem_names(self) -> Sequence[TBuildItem]:
        return [
            self.BUILDITEM_SERVICE_ACCOUNT,
            self.BUILDITEM_CLUSTER_ROLE,
            self.BUILDITEM_CLUSTER_ROLE_BINDING,
            self.BUILDITEM_CONFIG,
            self.BUILDITEM_STATEFULSET,
            self.BUILDITEM_SERVICE,
        ]

    def internal_build(self, buildname: TBuild) -> Sequence[ObjectItem]:
        if buildname == self.BUILD_ACCESSCONTROL:
            return self.internal_build_accesscontrol()
        elif buildname == self.BUILD_CONFIG:
            return self.internal_build_config()
        elif buildname == self.BUILD_SERVICE:
            return self.internal_build_service()
        else:
            raise InvalidNameError('Invalid build name: "{}"'.format(buildname))

    def internal_build_accesscontrol(self) -> Sequence[ObjectItem]:
        ret = []

        if self.option_get('config.authorization.serviceaccount_create') is not False:
            ret.extend([
                Object({
                    'apiVersion': 'v1',
                    'kind': 'ServiceAccount',
                    'metadata': {
                        'name': self.object_name('service-account'),
                        'namespace': self.namespace(),
                    }
                }, name=self.BUILDITEM_SERVICE_ACCOUNT, source=self.SOURCE_NAME, instance=self.basename()),
            ])

        if self.option_get('config.authorization.roles_create') is not False:
            ret.extend([
                Object({
                    'apiVersion': 'rbac.authorization.k8s.io/v1',
                    'kind': 'ClusterRole',
                    'metadata': {
                        'name': self.object_name('cluster-role'),
                    },
                    'rules': [{
                        'apiGroups': [''],
                        'resources': [
                            'nodes',
                            'nodes/metrics',
                            'services',
                            'endpoints',
                            'pods'
                        ],
                        'verbs': ['get', 'list', 'watch']
                    },
                    {
                        'apiGroups': ['extensions'],
                        'resources': ['ingresses'],
                        'verbs': ['get', 'list', 'watch']
                    },
                    {
                        'nonResourceURLs': ['/metrics', '/metrics/cadvisor'],
                        'verbs': ['get']
                    }]
                }, name=self.BUILDITEM_CLUSTER_ROLE, source=self.SOURCE_NAME, instance=self.basename()),
            ])

        if self.option_get('config.authorization.roles_bind') is not False:
            ret.extend([
                Object({
                    'apiVersion': 'rbac.authorization.k8s.io/v1',
                    'kind': 'ClusterRoleBinding',
                    'metadata': {
                        'name': self.object_name('cluster-role-binding'),
                    },
                    'subjects': [{
                        'kind': 'ServiceAccount',
                        'name': self.object_name('service-account'),
                        'namespace': self.namespace(),
                    }],
                    'roleRef': {
                        'apiGroup': 'rbac.authorization.k8s.io',
                        'kind': 'ClusterRole',
                        'name': self.object_name('cluster-role'),
                    }
                }, name=self.BUILDITEM_CLUSTER_ROLE_BINDING, source=self.SOURCE_NAME, instance=self.basename())
            ])

        return ret

    def internal_build_config(self) -> Sequence[ObjectItem]:
        ret = [
            Object({
                'apiVersion': 'v1',
                'kind': 'ConfigMap',
                'metadata': {
                    'name': self.object_name('config'),
                    'namespace': self.namespace(),
                },
                'data': {
                    'prometheus.yml': LiteralStr(self.configfile_get()),
                },
            }, name=self.BUILDITEM_CONFIG, source=self.SOURCE_NAME, instance=self.basename())
        ]
        return ret

    def internal_build_service(self) -> Sequence[ObjectItem]:
        ret = [Object({
            'kind': 'Service',
            'apiVersion': 'v1',
            'metadata': {
                'name': self.object_name('service'),
                'namespace': self.namespace(),
            },
            'spec': {
                'selector': {
                    'app': self.object_name('pod-label-app')
                },
                'ports': [{
                    'protocol': 'TCP',
                    'port': self.option_get('config.service_port'),
                    'targetPort': 9090
                }]
            }
        }, name=self.BUILDITEM_SERVICE, source=self.SOURCE_NAME, instance=self.basename()), Object({
            'apiVersion': 'apps/v1',
            'kind': 'StatefulSet',
            'metadata': {
                'name': self.object_name('statefulset'),
                'namespace': self.namespace(),
                'labels': {
                    'app': self.object_name('pod-label-app'),
                },
            },
            'spec': {
                'serviceName': self.object_name('service'),
                'selector': {
                    'matchLabels': {
                        'app': self.object_name('pod-label-app'),
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': self.object_name('pod-label-app'),
                        }
                    },
                    'spec': {
                        'serviceAccountName': ValueData(value=self.object_name('service-account'),
                                                        enabled=self.object_name('service-account') is not None),
                        'initContainers': [{
                            'name': 'init-chown-data',
                            'image': self.option_get('container.init-chown-data'),
                            'imagePullPolicy': 'Always',
                            'command': ['chown', '-R', '65534:65534', '/data'],
                            'volumeMounts': [{
                                'name': 'prometheus-data-volume',
                                'mountPath': '/data'
                            }]
                        }],
                        'containers': [{
                            'name': 'prometheus-server',
                            'image': self.option_get('container.prometheus'),
                            'args': ['--config.file=/etc/prometheus/prometheus.yml',
                                     '--storage.tsdb.path=/data'],
                            'volumeMounts': [{
                                'name': 'prometheus-config-volume',
                                'mountPath': '/etc/prometheus'
                            },
                            {
                                'name': 'prometheus-data-volume',
                                'mountPath': '/data'
                            }],
                            'ports': [{
                                'containerPort': 9090
                            }],
                            'readinessProbe': {
                                'httpGet': {
                                    'path': '/-/ready',
                                    'port': 9090
                                },
                                'initialDelaySeconds': 30,
                                'timeoutSeconds': 30
                            },
                            'livenessProbe': {
                                'httpGet': {
                                    'path': '/-/healthy',
                                    'port': 9090
                                },
                                'initialDelaySeconds': 30,
                                'timeoutSeconds': 30
                            },
                            'resources': ValueData(value=self.option_get('kubernetes.resources.statefulset'),
                                                   disabled_if_none=True),
                        }],
                        'volumes': [
                            {
                                'name': 'prometheus-config-volume',
                                'configMap': {
                                    'name': self.object_name('config'),
                                }
                            },
                            KDataHelper_Volume.info(base_value={
                                'name': 'prometheus-data-volume',
                            }, value=self.option_get('kubernetes.volumes.data')),
                        ]
                    }
                }
            }
        }, name=self.BUILDITEM_STATEFULSET, source=self.SOURCE_NAME, instance=self.basename())]
        return ret
