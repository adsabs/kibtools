
import os
import sys

PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)

import re
import json
import glob
import shutil
import unittest
import dashboard

from stub_data import stub_data
from httpretty import HTTPretty

class MockElasticsearch(object):
    """
    Mock of Elasticsearch
    """
    def __init__(self, response, regex='.*'):
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
            re.compile(regex),
            body=request_callback,
            content_type='application/json'
        )

        HTTPretty.register_uri(
            HTTPretty.POST,
            re.compile(regex),
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

    cluster = dict(
        ip_address='elasticsearch',
        port='80',
        index='.kibana',
    )

    def test_parse_visualizations(self):
        """
        Tests the parsing of visualizations
        """
        ret = dashboard.parse_visualizations(
            stub_data['_search/dashboard']['hits']['hits'][0]['_source']
        )

        self.assertEqual(len(ret), 1)

    def test_get_dashboard(self):
        """
        Tests the collection of the top level dashboard
        """
        stub_response = dict(
            status_code=200,
            response=stub_data['_search/dashboard']
        )
        with MockElasticsearch(stub_response):
            response = dashboard.get_dashboards(cluster=self.cluster)

        self.assertEqual(len(response), 2)
        self.assertIn('name', response[0].keys())
        self.assertIn('source', response[0].keys())
        self.assertIn('visualizations', response[0].keys())

    def test_get_visualizations(self):
        """
        Tests the collection of the Visualizations
        """
        stub_response = dict(
            status_code=200,
            response=stub_data['_search/visualization']
        )
        with MockElasticsearch(stub_response):
            response = dashboard.get_visualizations(cluster=self.cluster)

        self.assertEqual(len(response), 1)
        self.assertIn('name', response[0].keys())
        self.assertIn('source', response[0].keys())
        self.assertIn('searches', response[0].keys())

    def test_get_searches(self):
        """
        Tests the collection of the Searches
        """
        stub_response = dict(
            status_code=200,
            response=stub_data['_search/search']
        )
        with MockElasticsearch(stub_response):
            response = dashboard.get_searches(cluster=self.cluster)

        self.assertEqual(len(response), 1)
        self.assertIn('name', response[0].keys())
        self.assertIn('source', response[0].keys())

    def test_save_all_types(self):
        """
        Tests the saving of the dashboard types
        """

        # Give the output path
        output_path = '{0}/test_out/'.format(os.getcwd())

        stub_dashboard = dict(
            status_code=200,
            response=stub_data['_search/dashboard']
        )
        stub_visualization = dict(
            status_code=200,
            response=stub_data['_search/visualization']
        )

        stub_search = dict(
            status_code=200,
            response=stub_data['_search/search']
        )

        with \
                MockElasticsearch(
                    response=stub_dashboard,
                    regex='.*dashboard/_search$'
                ) as MD, \
                MockElasticsearch(
                    response=stub_visualization,
                    regex='.*visualization/_search$'
                ) as MV, \
                MockElasticsearch(
                    response=stub_search,
                    regex='.*search/_search$'
                ) as MS:
                    dashboard.save_all_types(
                        cluster=self.cluster,
                        output_directory=output_path
                    )

        # Check the folder and files were made
        for save_type in ['search', 'visualization', 'dashboard']:
            path = '{0}{1}'.format(output_path, save_type)
            self.assertTrue(os.path.isdir(path))
            self.assertTrue(len(glob.glob('{0}/*'.format(path))) > 0)

        # Clean up
        shutil.rmtree(output_path)

    def test_push_object(self):
        """
        Tests that you can push an object to elasticsearch
        """
        stub_response = dict(
            status_code=200,
            response={'msg': 'success'}
        )
        with MockElasticsearch(response=stub_response):
            ret = dashboard.push_object(
                cluster=self.cluster,
                push_name='GET',
                push_type='search',
                push_source=stub_data[
                    '_search/search']['hits']['hits'][0]['_source']
            )

        self.assertEqual(ret.status_code, 200)
