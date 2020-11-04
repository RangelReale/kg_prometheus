# KubraGen Builder: Prometheus

[![PyPI version](https://img.shields.io/pypi/v/kg_prometheus.svg)](https://pypi.python.org/pypi/kg_prometheus/)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/kg_prometheus.svg)](https://pypi.python.org/pypi/kg_prometheus/)

kg_prometheus is a builder for [KubraGen](https://github.com/RangelReale/kubragen) that deploys 
a [Prometheus](https://prometheus.io/) server in Kubernetes.

[KubraGen](https://github.com/RangelReale/kubragen) is a Kubernetes YAML generator library that makes it possible to generate
configurations using the full power of the Python programming language.

## Example

```python
from kubragen import KubraGen
from kubragen.consts import PROVIDER_GOOGLE, PROVIDERSVC_GOOGLE_GKE
from kubragen.object import Object
from kubragen.option import OptionRoot
from kubragen.options import Options
from kubragen.output import OutputProject, OD_FileTemplate, OutputFile_Kubernetes, OutputFile_ShellScript, \
    OutputDriver_Print
from kubragen.provider import Provider

from kg_prometheus import PrometheusBuilder, PrometheusOptions, PrometheusConfigFile, PrometheusConfigFileOptions

kg = KubraGen(provider=Provider(PROVIDER_GOOGLE, PROVIDERSVC_GOOGLE_GKE), options=Options({
    'namespaces': {
        'mon': 'app-monitoring',
    },
}))

out = OutputProject(kg)

shell_script = OutputFile_ShellScript('create_gke.sh')
out.append(shell_script)

shell_script.append('set -e')

#
# OUTPUTFILE: app-namespace.yaml
#
file = OutputFile_Kubernetes('app-namespace.yaml')

file.append([
    Object({
        'apiVersion': 'v1',
        'kind': 'Namespace',
        'metadata': {
            'name': 'app-monitoring',
        },
    }, name='ns-monitoring', source='app', instance='app')
])

out.append(file)
shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

shell_script.append(f'kubectl config set-context --current --namespace=app-monitoring')

#
# SETUP: prometheus
#
prometheus_config_file = PrometheusConfigFile(options=PrometheusConfigFileOptions({
    'config': {
        'extra_config': {
            'global': {
                'scrape_interval': '1m',
            }
        },
    },
    'scrape': {
        'prometheus': {
            'enabled': True,
            'extra_config': {
                'scrape_interval': '15s',
            },
        }
    }
}))

prometheus_config = PrometheusBuilder(kubragen=kg, options=PrometheusOptions({
    'namespace': OptionRoot('namespaces.mon'),
    'basename': 'myprometheus',
    'config': {
        'prometheus_config': prometheus_config_file,
    },
    'kubernetes': {
        'volumes': {
            'data': {
                'persistentVolumeClaim': {
                    'claimName': 'prometheus-storage-claim'
                }
            }
        },
        'resources': {
            'statefulset': {
                'requests': {
                    'cpu': '150m',
                    'memory': '300Mi'
                },
                'limits': {
                    'cpu': '300m',
                    'memory': '450Mi'
                },
            },
        },
    }
}))

prometheus_config.ensure_build_names(prometheus_config.BUILD_ACCESSCONTROL, prometheus_config.BUILD_CONFIG,
                                     prometheus_config.BUILD_SERVICE)

#
# OUTPUTFILE: prometheus-config.yaml
#
file = OutputFile_Kubernetes('prometheus-config.yaml')
out.append(file)

file.append(prometheus_config.build(prometheus_config.BUILD_ACCESSCONTROL, prometheus_config.BUILD_CONFIG))

shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

#
# OUTPUTFILE: prometheus.yaml
#
file = OutputFile_Kubernetes('prometheus.yaml')
out.append(file)

file.append(prometheus_config.build(prometheus_config.BUILD_SERVICE))

shell_script.append(OD_FileTemplate(f'kubectl apply -f ${{FILE_{file.fileid}}}'))

#
# Write files
#
out.output(OutputDriver_Print())
# out.output(OutputDriver_Directory('/tmp/build-gke'))
```

Output:

```text
****** BEGIN FILE: 001-app-namespace.yaml ********
apiVersion: v1
kind: Namespace
metadata:
  name: app-monitoring

****** END FILE: 001-app-namespace.yaml ********
****** BEGIN FILE: 002-prometheus-config.yaml ********
apiVersion: v1
kind: ServiceAccount
metadata:
  name: myprometheus
  namespace: app-monitoring
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: myprometheus
rules:
- apiGroups: ['']
  resources: [nodes, nodes/metrics, services, endpoints, pods]
  verbs: [get, list, watch]
- apiGroups: [extensions]
  resources: [ingresses]
  verbs: [get, list, watch]
- nonResourceURLs: [/metrics, /metrics/cadvisor]
  verbs: [get]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: myprometheus
subjects:
- kind: ServiceAccount
  name: myprometheus
  namespace: app-monitoring
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: myprometheus
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: myprometheus-config
  namespace: app-monitoring
data:
  prometheus.yml: |
    scrape_configs:
    - job_name: 'prometheus'
      static_configs:
      - targets: ['localhost:9090']
      scrape_interval: 15s
    global: {scrape_interval: 1m}

****** END FILE: 002-prometheus-config.yaml ********
****** BEGIN FILE: 003-prometheus.yaml ********
kind: Service
apiVersion: v1
metadata:
  name: myprometheus
  namespace: app-monitoring
spec:
  selector:
    app: myprometheus
  ports:
<...more...>
****** END FILE: 003-prometheus.yaml ********
****** BEGIN FILE: create_gke.sh ********
#!/bin/bash

set -e
kubectl apply -f 001-app-namespace.yaml
kubectl config set-context --current --namespace=app-monitoring
kubectl apply -f 002-prometheus-config.yaml
kubectl apply -f 003-prometheus.yaml

****** END FILE: create_gke.sh ********
```

## Credits

based on

[prometheus-community/helm-charts](https://github.com/prometheus-community/helm-charts)

## Author

Rangel Reale (rangelspam@gmail.com)
