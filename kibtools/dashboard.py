#!/usr/bin/env python
# encoding: utf-8

"""
Kibana Dashboard Extractor/Loader

A small tool to extract dashboards, visualizations, and searches from kibana,
that are stored in the elasticsearch index. It is based on the Ruby scripts
created by @jim-davis:

Modified from https://github.com/jim-davis/kibana-helper-scripts

Modifications have been made such that the dashboard can be compressed to gzips
and sent to AWS S3 storage. The same can be done in reverse - the gzip can be
pulled from AWS S3 storage and unpacked to be loaded into the elasticsearch
index.

Note: it is assumed you are using a VPC for the AWS, and as such, no keys are
being passed when communicating with AWS S3. Instead, you must create the
relevant IAM for the instance that you run this script on. For more details see
the extensive Amazon S3 documentation:

http://docs.aws.amazon.com/AmazonS3/latest/dev/using-iam-policies.html
"""

import os
import glob
import json
import boto3
import config
import tarfile
import logging
import logging.config
import argparse
import requests

logging.config.dictConfig(config.LOGGING)
logger = logging.getLogger()

def parse_visualizations(dashboard):
    """
    Parse the visualizations from a dashboard
    :param dashboard: JSON dashboard response
    :return: list of visualization names
    """
    return [panel['id'] for panel in json.loads(dashboard['panelsJSON'])]

def get_dashboards(cluster):
    """
    GET all the saved dashboards

    :param cluster: cluster details
    :return: list of dictionaries
    """
    url = 'http://{ip_address}:{port}/{index}/dashboard/_search'.format(
        ip_address=cluster['ip_address'],
        port=cluster['port'],
        index=cluster['index'],
    )

    response = requests.get(url)
    dashboards = json.loads(response.text).get('hits', {}).get('hits', {})

    dashboards = [
        dict(name=db['_id'],
             source=db['_source'],
             visualizations=parse_visualizations(db['_source'])
             ) for db in dashboards
        ]

    return dashboards

def get_visualizations(cluster):
    """
    GET all the saved visualizations

    :param cluster: cluster details
    :return: list of dictionaries
    """
    url = 'http://{ip_address}:{port}/{index}/visualization/_search'.format(
        ip_address=cluster['ip_address'],
        port=cluster['port'],
        index=cluster['index'],
    )

    response = requests.get(url)
    visualizations = json.loads(response.text).get('hits', {}).get('hits', {})

    visualizations = [
        dict(name=viz['_id'],
             source=viz['_source'],
             searches=viz['_source']['savedSearchId']
             ) for viz in visualizations
        ]

    return visualizations

def get_searches(cluster):
    """
    GET all the saved searches

    :param cluster: cluster details
    :return: list of dictionaries
    """
    url = 'http://{ip_address}:{port}/{index}/search/_search'.format(
        ip_address=cluster['ip_address'],
        port=cluster['port'],
        index=cluster['index'],
    )

    response = requests.get(url)
    searches = json.loads(response.text).get('hits', {}).get('hits', {})

    searches = [
        dict(name=search['_id'],
             source=search['_source']
             ) for search in searches
        ]

    return searches

def save_all_types(cluster, output_directory):
    """
    Collect all the relevants types and save them to an output directory

    :param cluster: cluster details
    :param output_directory: path to output directory
    """

    # Make the output directory
    if not os.path.isdir(output_directory):
        os.mkdir(output_directory)

    save_all = dict(
        dashboard=get_dashboards(cluster=cluster),
        visualization=get_visualizations(cluster=cluster),
        search=get_searches(cluster=cluster)
    )

    logger.info('Saving dashboard content to: {0}'.format(output_directory))
    for save_type in save_all:

        # Skip this if there are no objects
        if len(save_all[save_type]) == 0:
            continue

        # If the folder does not exist
        sub_folder = '{path}/{sub_path}'.format(
            path=output_directory,
            sub_path=save_type
        )

        if not os.path.isdir(sub_folder):
            os.mkdir(sub_folder)

        logger.info('Saving files for type: {0}'.format(save_type))
        for objects in save_all[save_type]:
            output_file = '{path}{sub_path}/{file}.json'.format(
                path=output_directory,
                sub_path=save_type,
                file=objects['name']
            )
            with open(output_file, 'w') as output_json:
                json.dump(objects['source'], output_json)

            logger.info('...... file object: {0}'.format(objects['name']))

def push_object(cluster, push_type, push_name, push_source):
    """
    Push an object to the elasticsearch cluster

    :param cluster: cluster details
    :param push_type: type of the object: dashboard, visualization, search
    :param push_name: name of object
    :param push_source: source of object

    :return: response message from elasticsearch
    """
    url = 'http://{ip_address}:{port}/{index}/{type}/{name}'.format(
        ip_address=cluster['ip_address'],
        port=cluster['port'],
        index=cluster['index'],
        type=push_type,
        name=push_name
    )
    response = requests.post(url, data=json.dumps(push_source))
    return response

def push_all_from_disk(cluster, input_directory):
    """
    Look at the input_directory for expected folders:
      - search, visualization, dashboard
    And push any JSON file that exists inside to elasticsearch

    :param cluster: cluster details
    :param input_directory: directory that contains all types
    """

    if not os.path.isdir(input_directory):
        raise IOError('Folder does not exist')

    logger.info('Using folder: {0}'.format(input_directory))

    for push_type in ['search', 'visualization', 'dashboard']:
        sub_path = '{path}/{sub_path}'.format(
            path=input_directory,
            sub_path=push_type
        )
        if not os.path.isdir(sub_path):
            continue
        files = glob.glob('{0}/*'.format(sub_path))

        if len(files) == 0:
            continue

        logger.info('Pushing files for type: {0}'.format(push_type))
        for file_object in files:
            with open(file_object, 'r') as input_json_file:
                push_source = json.load(input_json_file)

            push_name = push_source['title']
            response = push_object(
                cluster=cluster,
                push_type=push_type,
                push_name=push_name,
                push_source=push_source
            )

            logger.info('....... file object: {0}'.format(push_name))
            logger.info('Response from ES: {0}'.format(response))

def s3_upload_file(input_file, s3_bucket, s3_object):
    """
    Upload file to S3 storage. Similar to the s3.upload_file, however, that
    does not work nicely with moto, whereas this function does.

    :param input_file: file to upload
    :param s3_bucket: bucket to upload to
    :param s3_object: name of the object in the bucket
    """

    s3_resource = boto3.resource('s3')

    with open(input_file, 'rb') as f:
        binary = f.read()

    s3_resource.Bucket(s3_bucket).put_object(
        Key=s3_object,
        Body=binary
    )

def push_to_s3(input_directory, s3_details):
    """
    Push the files on disk to S3 storage

    :param input_directory: input directory
    :param s3_details: details about AWS S3
    """
    tar_file = '/tmp/dashboard.tar.gz'
    folders = glob.glob('{0}/*'.format(input_directory))
    with tarfile.open(tar_file, 'w:gz') as out_tar:
        for folder in folders:
            out_tar.add(folder, arcname=folder.split('/')[-1])
    logger.info('Made a gzipped tarbarball: {0}'.format(tar_file))

    s3_upload_file(tar_file, s3_details['bucket'], 'dashboard.tar.gz')

    logger.info('Pushing to S3 storage: {0}'.format(s3_details['bucket']))
    os.remove('/tmp/dashboard.tar.gz')

def s3_download_file(s3_bucket, s3_object, output_file):
    """
    Download file from S3 bucket. Similar to s3.download_file except that does
    not play nicely with moto, this however, does.

    :param s3_bucket: bucket to download from
    :param s3_object: object to download
    :param output_file: file to download to
    """

    s3_resource = boto3.resource('s3')
    body = s3_resource.Object(s3_bucket, s3_object).get()['Body']
    with open(output_file, 'wb') as f:
        for chunk in iter(lambda: body.read(1024), b''):
            f.write(chunk)

def pull_from_s3(output_directory, s3_details):
    """
    Pull files from S3 storage and unpack

    :param output_directory: output directory
    :param s3_details: details about AWS S3
    """

    logger.info('Pulling file from S3 storage: {0}'.format(s3_details['bucket']))
    s3_download_file(s3_details['bucket'], 'dashboard.tar.gz', '/tmp/dashboard.tar.gz')

    logger.info('Opening tar file to: {0}'.format(output_directory))
    tar_file = tarfile.open('/tmp/dashboard.tar.gz', 'r')
    tar_file.extractall(output_directory)

    os.remove('/tmp/dashboard.tar.gz')

if __name__ == '__main__':

    # Load the users preferences
    parser = argparse.ArgumentParser(description='Save kibana dashboard.')

    parser.add_argument(
        '-d',
        '--directory',
        dest='directory',
        required=True,
        help='directory to save/load the dashboard',
        type=str
    )
    parser.add_argument(
        '-a',
        '--action',
        dest='action',
        choices=['save', 'load'],
        required=True,
        help='save/load dashboard to/from file',
        type=str
    )
    parser.add_argument(
        '-s',
        '--s3',
        dest='s3',
        action='store_true',
        help='save/load the dashboard to/from AWS S3'
    )
    parser.add_argument(
        '--cluster-ip',
        dest='cluster_ip',
        default='elasticsearch',
        help='IP or DNS name of cluster',
        type=str
    )
    parser.add_argument(
        '--cluster-port',
        dest='cluster_port',
        default='9200',
        help='elasticsearch cluster port',
        type=str
    )
    parser.add_argument(
        '--cluster-index',
        dest='cluster_index',
        default='.kibana',
        help='elasticsearch kibana index name',
        type=str
    )
    parser.add_argument(
        '--s3-bucket',
        dest='s3_bucket',
        default='kibana-dash',
        help='S3 bucket name',
        type=str
    )
    parser.add_argument(
        '--s3-host',
        dest='s3_host',
        default='kibana-dash',
        help='S3 host name',
        type=str
    )
    parser.add_argument(
        '--s3-schema',
        dest='s3_schema',
        default='http',
        choices=['http', 'https'],
        help='S3 schema',
        type=str
    )

    args = parser.parse_args()

    # Create some dictionaries that are needed
    cluster = dict(
        ip_address=args.cluster_ip,
        port=args.cluster_port,
        index=args.cluster_index
    )

    s3_details = dict(
        bucket=args.s3_bucket,
        host=args.s3_host,
        schema=args.s3_schema
    )

    # If the user wants to save the dashboard
    if args.action == 'save':
        save_all_types(
            cluster=cluster,
            output_directory=args.directory
        )
        # If the dashboard should be saved to s3
        if args.s3:
            push_to_s3(
                input_directory=args.directory,
                s3_details=s3_details
            )
    # If the user wants to load the dashboard
    elif args.action == 'load':
        # If the dashboard should be loaded from s3
        if args.s3:
            pull_from_s3(
                output_directory=args.directory,
                s3_details=s3_details
            )
        push_all_from_disk(
            cluster=cluster,
            input_directory=args.directory
        )
