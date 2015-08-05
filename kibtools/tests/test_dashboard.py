
import os
import sys

PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)

import re
import json
import unittest
import dashboard
from httpretty import HTTPretty

class MockElasticsearch(object):
    """
    Mock of Elasticsearch
    """
    def __init__(self, response):
        """
        Constructor
        :param response: user response
        """
        self.response = response

        def request_callback(request, uri, headers):
            """
            :param request: HTTP request
            :param uri: URI/URL to send the request
            :param headers: header of the HTTP request
            :return:
            """
            return self.response['status_code'], \
                headers, \
                json.dumps(self.response['response'])

        HTTPretty.register_uri(
            HTTPretty.GET,
            re.compile('.*'),
            body=request_callback,
            content_type='application/json'
        )

    def __enter__(self):
        """
        Defines the behaviour for __enter__
        """
        HTTPretty.enable()

    def __exit__(self, *args):
        """
        Defines the behaviour for __exit__
        """
        HTTPretty.reset()
        HTTPretty.disable()


class TestDashboard(unittest.TestCase):

    response_search = dict(
        status_code=200,
        response={
    "_shards": {
        "failed": 0,
        "successful": 1,
        "total": 1
    },
    "hits": {
        "hits": [
            {
                "_id": "GET",
                "_index": ".kibana",
                "_score": 1.0,
                "_source": {
                    "columns": [
                        "_source"
                    ],
                    "description": "",
                    "hits": 0,
                    "kibanaSavedObjectMeta": {
                        "searchSourceJSON": "{\"index\":\"[logstash-]YYYY.MM.DD\",\"highlight\":{\"pre_tags\":[\"@kibana-highlighted-field@\"],\"post_tags\":[\"@/kibana-highlighted-field@\"],\"fields\":{\"*\":{}}},\"filter\":[],\"query\":{\"query_string\":{\"query\":\"GET\",\"analyze_wildcard\":true}}}"
                    },
                    "sort": [
                        "@timestamp",
                        "desc"
                    ],
                    "title": "GET",
                    "version": 1
                },
                "_type": "search"
            }
        ],
        "max_score": 1.0,
        "total": 1
    },
    "timed_out": False,
    "took": 1
}
    )

    cluster = dict(
        ip_address='elasticsearch',
        port='80',
        index='.kibana',
    )

    def test_get_object(self):

        with MockElasticsearch(self.response_search):
            ret = dashboard.get_objects(get_type='search', cluster=self.cluster)

        print ret

        self.assertIn(ret['_id'], 'GET')
