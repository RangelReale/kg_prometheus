from kubragen import KubraGen
from kubragen.consts import PROVIDER_GOOGLE, PROVIDERSVC_GOOGLE_GKE
from kubragen.object import Object
from kubragen.option import OptionRoot
from kubragen.options import Options
from kubragen.output import OutputProject, OD_FileTemplate, OutputFile_Kubernetes, OutputFile_ShellScript, \
    OutputDriver_Print
from kubragen.provider import Provider

from kg_prometheus import PrometheusBuilder, PrometheusOptions, PrometheusConfigFile, PrometheusConfigFileOptions, \
    PrometheusConfigFileExt_Kubernetes

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
        'merge_config': {
            'global': {
                'scrape_interval': '1m',
            }
        },
    },
    'scrape': {
        'prometheus': {
            'enabled': True,
            'merge_config': {
                'scrape_interval': '15s',
            },
        }
    }
}), extensions=[
    PrometheusConfigFileExt_Kubernetes(insecure_skip_verify=True),
])

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
