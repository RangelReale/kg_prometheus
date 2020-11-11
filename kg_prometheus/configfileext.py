from kubragen.configfile import ConfigFileExtension, ConfigFile, ConfigFileExtensionData
from kubragen.data import ValueData
from kubragen.options import OptionGetter


class PrometheusConfigFileExt_Kubernetes(ConfigFileExtension):
    """
    Prometheus configuration extension for Kubernetes scrape config.

    Based on `prometheus/prometheus <https://github.com/prometheus/prometheus/blob/master/documentation/examples/prometheus-kubernetes.yml>`_.
    Based on `Driving Manual or Automatic: Docker Hub vs. Helm for Deploying Prometheus on Kubernetes <https://logz.io/blog/manual-automatic-kubernetes-prometheus-docker-hub-helm/>`_.
    """
    insecure_skip_verify: bool
    scrape_cadvisor: bool

    def __init__(self, insecure_skip_verify: bool = False, scrape_cadvisor: bool = True):
        """
        :param insecure_skip_verify: set insecure_skip_verify parameter for kubernetes tls_config
        :param scrape_cadvisor: whether to scrape cadvisor (not available in all kubernetes installations)
        """
        self.insecure_skip_verify = insecure_skip_verify
        self.scrape_cadvisor = scrape_cadvisor

    def process(self, configfile: ConfigFile, data: ConfigFileExtensionData, options: OptionGetter) -> None:
        if 'scrape_configs' not in data.data:
            data.data['scrape_configs'] = []
        data.data['scrape_configs'].extend([{
            'job_name': 'kubernetes-apiservers',
            'kubernetes_sd_configs': [{
                'role': 'endpoints'
            }],
            'scheme': 'https',
            'tls_config': {
                'ca_file': '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt',
                'insecure_skip_verify': self.insecure_skip_verify,
            },
            'bearer_token_file': '/var/run/secrets/kubernetes.io/serviceaccount/token',
            'relabel_configs': [{
                'source_labels': ['__meta_kubernetes_namespace',
                                  '__meta_kubernetes_service_name',
                                  '__meta_kubernetes_endpoint_port_name'],
                'action': 'keep',
                'regex': 'default;kubernetes;https'
            }]
        },
        {
            'job_name': 'kubernetes-nodes',
            'scheme': 'https',
            'tls_config': {
                'ca_file': '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt',
                'insecure_skip_verify': self.insecure_skip_verify,
            },
            'bearer_token_file': '/var/run/secrets/kubernetes.io/serviceaccount/token',
            'kubernetes_sd_configs': [{
                'role': 'node'
            }],
            'relabel_configs': [
                {
                    'action': 'labelmap',
                    'regex': '__meta_kubernetes_node_label_(.+)'
                },
            ]
        },
        {
            'job_name': 'kubernetes-pods',
            'kubernetes_sd_configs': [{
                'role': 'pod'
            }],
            'relabel_configs': [{
                'source_labels': ['__meta_kubernetes_pod_annotation_prometheus_io_scrape'],
                'action': 'keep',
                'regex': True
            },
            {
                'source_labels': ['__meta_kubernetes_pod_annotation_prometheus_io_path'],
                'action': 'replace',
                'target_label': '__metrics_path__',
                'regex': '(.+)'
            },
            {
                'source_labels': ['__address__',
                                  '__meta_kubernetes_pod_annotation_prometheus_io_port'],
                'action': 'replace',
                'regex': '([^:]+)(?::\\d+)?;(\\d+)',
                'replacement': '$1:$2',
                'target_label': '__address__'
            },
            {
                'action': 'labelmap',
                'regex': '__meta_kubernetes_pod_label_(.+)'
            },
            {
                'source_labels': ['__meta_kubernetes_namespace'],
                'action': 'replace',
                'target_label': 'kubernetes_namespace'
            },
            {
                'source_labels': ['__meta_kubernetes_pod_name'],
                'action': 'replace',
                'target_label': 'kubernetes_pod_name'
            }]
        },
        ValueData({
            'job_name': 'kubernetes-cadvisor',
            'scheme': 'https',
            'tls_config': {
                'ca_file': '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt',
                'insecure_skip_verify': self.insecure_skip_verify,
            },
            'bearer_token_file': '/var/run/secrets/kubernetes.io/serviceaccount/token',
            'kubernetes_sd_configs': [{
                'role': 'node',
            }],
            'relabel_configs': [
            {
                'action': 'labelmap',
                'regex': '__meta_kubernetes_node_label_(.+)'
            },
            {
                'target_label': '__address__',
                'replacement': 'kubernetes.default.svc:443'
            },
            {
                'source_labels': ['__meta_kubernetes_node_name'],
                'regex': '(.+)',
                'target_label': '__metrics_path__',
                'replacement': '/api/v1/nodes/${1}/proxy/metrics/cadvisor'
            }]
        }, enabled=self.scrape_cadvisor),
        {
            'job_name': 'kubernetes-service-endpoints',
            'kubernetes_sd_configs': [{
                'role': 'endpoints'
            }],
            'relabel_configs': [{
                'source_labels': ['__meta_kubernetes_service_annotation_prometheus_io_scrape'],
                'action': 'keep',
                'regex': True
            },
            {
                'source_labels': ['__meta_kubernetes_service_annotation_prometheus_io_scheme'],
                'action': 'replace',
                'target_label': '__scheme__',
                'regex': '(https?)'
            },
            {
                'source_labels': ['__meta_kubernetes_service_annotation_prometheus_io_path'],
                'action': 'replace',
                'target_label': '__metrics_path__',
                'regex': '(.+)'
            },
            {
                'source_labels': ['__address__',
                                  '__meta_kubernetes_service_annotation_prometheus_io_port'],
                'action': 'replace',
                'target_label': '__address__',
                'regex': '([^:]+)(?::\\d+)?;(\\d+)',
                'replacement': '$1:$2'
            },
            {
                'action': 'labelmap',
                'regex': '__meta_kubernetes_service_label_(.+)'
            },
            {
                'source_labels': ['__meta_kubernetes_namespace'],
                'action': 'replace',
                'target_label': 'kubernetes_namespace'
            },
            {
                'source_labels': ['__meta_kubernetes_service_name'],
                'action': 'replace',
                'target_label': 'kubernetes_name'
            }],
        }])
