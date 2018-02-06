#!/usr/bin/python

import json
import itertools
import sys
import string
import random

try:
    import boto3

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


def get_caller_reference():
    ts = int(time.time())
    choice_str = string.ascii_uppercase
    caller_reference = ''.join(random.choice(choice_str) for _ in range(10)) + str(ts)
    return caller_reference


def create_calculated(module, route53):
    result_health_check = {}
    try:
        result_health_check = route53.create_health_check(
            CallerReference=get_caller_reference(),
            HealthCheckConfig={
                'Type': 'CALCULATED',
                'HealthThreshold': module.params.get('threshold'),
                'ChildHealthChecks': module.params.get('health_check_ids'),
            })

    except Exception, e:
        module.fail_json(msg=str(e))
    changed = True

    module.exit_json(changed=changed, result=result_health_check)


def tags(module, route53):
    result_health_check = {}
    try:

        tags = []
        for k, v in module.params.get('tags').items():
            tags.append({'Key': k, 'Value': v})

        result_health_check = route53.change_tags_for_resource(
            ResourceType='healthcheck',
            ResourceId=module.params.get('health_check_id'),
            AddTags=tags
        )

    except Exception, e:
        module.fail_json(msg=str(e))
    changed = True

    module.exit_json(changed=changed, result=result_health_check)


def create_https(module, route53):
    result_health_check = {}

    try:

        result_health_check = route53.create_health_check(
            CallerReference=get_caller_reference(),
            HealthCheckConfig={
                'Port': module.params.get('port'),
                'Type': 'HTTPS',
                'ResourcePath': module.params.get('resource_path'),
                'FullyQualifiedDomainName': module.params.get('fqdn'),
                'RequestInterval': module.params.get('request_interval'),
                'FailureThreshold': module.params.get('threshold'),
            })

    except Exception, e:
        module.fail_json(msg=str(e))
    changed = True

    module.exit_json(changed=changed, result=result_health_check)


def main():
    argument_spec = dict(
        threshold=dict(type='int', default=None, required=False),
        action=dict(default=None, required=True, choices=['create_calculated', 'tags', 'create_https']),
        health_check_ids=dict(type='list', default=None, required=False),
        health_check_id=dict(type='str', default=None, required=False),
        tags=dict(type='dict', default=None, required=False),
        port=dict(type='int', default=None, required=False),
        resource_path=dict(type='str', default=None, required=False),
        fqdn=dict(type='str', default=None, required=False),
        request_interval=dict(type='int', default=None, required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[],
    )

    if not HAS_BOTO3:
        module.fail_json(msg='This module requires boto3, please install it')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    route53 = boto3_conn(module,
                         conn_type='client',
                         resource='route53',
                         region=region,
                         endpoint=ec2_url,
                         **aws_connect_kwargs)

    action = module.params.get('action')
    if action == 'create_calculated':
        create_calculated(module=module, route53=route53)
    elif action == 'tags':
        tags(module=module, route53=route53)
    elif action == 'create_https':
        create_https(module=module, route53=route53)


from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
