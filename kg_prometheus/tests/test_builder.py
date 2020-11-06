import unittest

from kubragen import KubraGen
from kubragen.jsonpatch import FilterJSONPatches_Apply, ObjectFilter, FilterJSONPatch
from kubragen.provider import Provider_Generic

from kg_prometheus import PrometheusBuilder, PrometheusOptions


class TestBuilder(unittest.TestCase):
    def setUp(self):
        self.kg = KubraGen(provider=Provider_Generic())

    def test_empty(self):
        prom_config = PrometheusBuilder(kubragen=self.kg)
        self.assertEqual(prom_config.object_name('config'), 'prometheus-config')
        self.assertEqual(prom_config.object_name('statefulset'), 'prometheus')

    def test_basedata(self):
        prom_config = PrometheusBuilder(kubragen=self.kg, options=PrometheusOptions({
            'namespace': 'myns',
            'basename': 'myprom',
            'kubernetes': {
                'volumes': {
                    'data': {
                        'emptyDir': {},
                    }
                }
            }
        }))
        self.assertEqual(prom_config.object_name('config'), 'myprom-config')
        self.assertEqual(prom_config.object_name('statefulset'), 'myprom')

        FilterJSONPatches_Apply(items=prom_config.build(prom_config.BUILD_SERVICE), jsonpatches=[
            FilterJSONPatch(filters=ObjectFilter(names=[prom_config.BUILDITEM_SERVICE]), patches=[
                {'op': 'check', 'path': '/metadata/name', 'cmp': 'equals', 'value': 'myprom'},
                {'op': 'check', 'path': '/metadata/namespace', 'cmp': 'equals', 'value': 'myns'},
            ]),
        ])
