#!/usr/bin/env python

"""
Modified from https://github.com/jim-davis/kibana-helper-scripts
"""

import os
import json
import requests

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
    GET all the saves visualizations

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

        for objects in save_all[save_type]:
            output_file = '{path}{sub_path}/{file}.json'.format(
                path=output_directory,
                sub_path=save_type,
                file=objects['name']
            )
            with open(output_file, 'w') as output_json:
                json.dump(objects['source'], output_json)

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

    response = requests.post(url, data=push_source)

    return response

if __name__ == '__main__':
    print ''
    # For each dashboard get the relevant dashboard

