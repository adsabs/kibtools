
import os
import sys

PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)

import re
import json
import glob
import shutil
import tarfile
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

        HTTPretty.register_uri(
            HTTPretty.PUT,
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

class MockElasticsearchStream(object):
    """
    Mock of Elasticsearch
    """
    def __init__(self, regex='.*'):
        """
        Constructor
        """
        def request_callback(request, uri, headers):
            """
            :param request: HTTP request
            :param uri: URI/URL to send the request
            :param headers: header of the HTTP request
            :return:
            """

            cluster = dict(
                ip_address='elasticsearch',
                port='80',
                index='.kibana',
            )
            output_path = '{0}/'.format(os.getcwd())
            helper_make_all(cluster=cluster, output_path=output_path)
            tmp_file = open('/tmp/tmp.tar.gz', 'rb')
            lines = tmp_file.read()
            tmp_file.close()

            return 200, headers, lines

        HTTPretty.register_uri(
            HTTPretty.GET,
            re.compile('dashboard'),
            body=request_callback,
            content_type='application/json',
            content_length=0,
            content_encoding='gzip',
            streaming=True,
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

def helper_make_all(cluster, output_path):
    """
    This makes the relevant stub files needed for the gzip, except this does
    not require any web interaction
    :param cluster: cluster details
    :param output_path: output path
    """
    os.mkdir('/tmp/test_out/')

    for es_type in ['search', 'visualization', 'dashboard']:
        sub_path = '/tmp/test_out/{0}'.format(es_type)

        os.mkdir(sub_path)

        with open('{0}/temp.json'.format(sub_path), 'w') as f_tmp:
            f_tmp.write('{"msg": "sucess"}')

    tar_file = '/tmp/tmp.tar.gz'.format(output_path)
    with tarfile.open(tar_file, 'w:gz') as out_tar:

        out_tar.add('/tmp/test_out/search'.format(output_path), arcname='search')
        out_tar.add('/tmp/test_out/visualization'.format(output_path), arcname='visualization')
        out_tar.add('/tmp/test_out/dashboard'.format(output_path), arcname='dashboard')

    shutil.rmtree('/tmp/test_out/')

def helper_extract_all(cluster, output_path):
    """
    Runs the extraction from elasticsearch to create files on disk
    """
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
                    cluster=cluster,
                    output_directory=output_path
                )

class TestDashboard(unittest.TestCase):

    cluster = dict(
        ip_address='elasticsearch',
        port='80',
        index='.kibana',
    )

    s3_details = dict(
        bucket='dashboard',
        host='s3.amazonaws.com',
        schema='http'
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
        output_path = '{0}/test_out/'.format(os.getcwd())
        helper_extract_all(cluster=self.cluster, output_path=output_path)

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

    def test_push_all_from_disk(self):
        """
        Tests that you can push all types to elasticsearch from disk
        """

        # First create some files on disk using the other routine
        # Not considered DRY yet as I only use this twice, plus the package
        # is rather small, so not worth generalising.
        output_path = '{0}/test_out/'.format(os.getcwd())
        helper_extract_all(cluster=self.cluster, output_path=output_path)

        # Push the files to elasticsearch
        stub_response = dict(
            status_code=200,
            response={'msg': 'success'}
        )
        try:
            with MockElasticsearch(response=stub_response):
                dashboard.push_all_from_disk(
                    cluster=self.cluster,
                    input_directory=output_path
                )
        except Exception as error:
            self.fail(error)
        finally:
            # Clean up files
            shutil.rmtree(output_path)

    def test_gzip_and_send_s3(self):
        """
        Tests that a gzip is made and sent to S3 and everything cleaned after
        """
        # First create some dummy content to work with
        output_path = '{0}/test_out/'.format(os.getcwd())
        helper_extract_all(cluster=self.cluster, output_path=output_path)

        # Run the gzip and send
        try:
            stub_response = dict(
                status_code=200,
                response={'msg': 'success'}
            )
            with MockElasticsearch(stub_response):
                response = dashboard.push_to_s3(
                    input_directory=output_path,
                    s3_details=self.s3_details
                )

            # Check response from S3
            self.assertEqual(response.status_code, 200)

            # Check there is a gzip on disk
            gb = glob.glob('{0}/*.gz'.format(output_path))
            self.assertTrue(
                len(gb) == 1
            )

        except Exception as error:
            self.fail(error)
        finally:
            # Clean up files
            shutil.rmtree(output_path)

    def test_pull_gzip_from_s3(self):
        """
        Tests that a gzip is pulled from S3 and unpacked
        """
        output_path = '{0}/test_out/'.format(os.getcwd())

        try:
            with MockElasticsearchStream():
                dashboard.pull_from_s3(
                    output_directory=output_path,
                    s3_details=self.s3_details
                )

            for sub_type in ['search', 'visualization', 'dashboard']:
                self.assertTrue(
                    os.path.isdir('{0}{1}'.format(output_path, sub_type))
                )
                gb = glob.glob('{0}{1}/*'.format(output_path, sub_type))
                self.assertTrue(
                    len(gb) > 0
            )
        except Exception as error:
            self.fail(error)
        finally:
            pass
            os.remove('/tmp/tmp.tar.gz')
            shutil.rmtree('{0}'.format(output_path))
