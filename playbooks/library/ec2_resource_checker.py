#!/usr/bin/python

import time

try:
    import boto3

    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False


class EC2ResourceChecker:
    """Resource Checker"""

    def __init__(self, client):
        self.__client = client
        self.__max_time_resource_checker_seconds = 1800  # 30 minutes

    # Call describe function by name and id parameter
    def __getattr__(self, name):

        function_name = '_' + name

        def selector(*args, **kwargs):

            result = False
            result_logs = []
            id = None

            for key in kwargs:

                if key == 'id':
                    id = kwargs.get(key)

            if id:

                result_logs.append('Start check resource ' + str(id))

                start_time = time.time()
                total_wait_time_sec = 0
                while not result and self.__max_time_resource_checker_seconds > total_wait_time_sec:
                    result = getattr(self, function_name)(id=id)

                    if not result:
                        result_logs.append('Resource ' + str(id) + ' does not exists! Wait 5 seconds and try again...')
                        time.sleep(5)
                    end_time = time.time()
                    total_wait_time_sec = round(end_time - start_time)
            else:
                raise Exception('Invalid arguments: id is required!')

            if not result:
                raise Exception('Resource ' + str(id) + ' does not exists!')

            return {'Checked': result, 'Logs': result_logs}

        return selector

    def _vpc(self, id):
        response = self.__client.describe_vpcs(

            Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [
                        id,
                    ]
                },
            ]
        )

        return len(response.get('Vpcs')) > 0

    def _network_acl(self, id):
        response = self.__client.describe_network_acls(
            Filters=[
                {
                    'Name': 'network-acl-id',
                    'Values': [
                        id,
                    ]
                },
            ])
        return len(response.get('NetworkAcls')) > 0

    def _dhcp_option(self, id):
        response = self.__client.describe_dhcp_options(
            Filters=[
                {
                    'Name': 'dhcp-options-id',
                    'Values': [
                        id,
                    ]
                },
            ])

        return len(response.get('DhcpOptions')) > 0

    def _route_table(self, id):
        response = self.__client.describe_route_tables(
            Filters=[
                {
                    'Name': 'route-table-id',
                    'Values': [
                        id,
                    ]
                },
            ])

        return len(response.get('RouteTables')) > 0

    def _security_group(self, id):
        response = self.__client.describe_security_groups(
            Filters=[
                {
                    'Name': 'group-id',
                    'Values': [
                        id,
                    ]
                },
            ])

        return len(response.get('SecurityGroups')) > 0

    def _internet_gateway(self, id):
        response = self.__client.describe_internet_gateways(
            Filters=[
                {
                    'Name': 'internet-gateway-id',
                    'Values': [
                        id,
                    ]
                },
            ])

        return len(response.get('InternetGateways')) > 0

    def _subnet(self, id):
        response = self.__client.describe_subnets(
            Filters=[
                {
                    'Name': 'subnet-id',
                    'Values': [id]
                },
                {
                    'Name': 'state',
                    'Values': ['available']
                }
            ])

        return len(response.get('Subnets')) > 0

    def _network_interface(self, id):
        response = self.__client.describe_network_interfaces(
            Filters=[
                {
                    'Name': 'network-interface-id',
                    'Values': [id]
                },
                {
                    'Name': 'status',
                    'Values': ['available']
                }
            ])

        return len(response.get('NetworkInterfaces')) > 0

    def _instance(self, id):
        response = self.__client.describe_instances(
            Filters=[
                {
                    'Name': 'instance-id',
                    'Values': [
                        id,
                    ]
                },
            ])

        return len(response.get('Reservations')) > 0


def main():
    argument_spec = dict(
        type=dict(default=None, required=True,
                  choices=['vpc', 'network_acl', 'dhcp_option', 'route_table', 'security_group', 'internet_gateway',
                           'subnet', 'network_interface', 'instance']),
        id=dict(type='str', default=None, required=True),
        region=dict(type='str', default=None, required=True),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[],
    )

    if not HAS_BOTO3:
        module.fail_json(msg='This module requires boto3, please install it!')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    ec2_client = boto3_conn(module,
                            conn_type='client',
                            resource='ec2',
                            region=module.params.get('region'),
                            endpoint=ec2_url,
                            **aws_connect_kwargs)

    ec2_resource_checker = EC2ResourceChecker(client=ec2_client)
    type = module.params.get('type')
    id = module.params.get('id')
    result_check = {}

    try:
        result_check = getattr(ec2_resource_checker, type)(id=id)
    except Exception, e:
        module.fail_json(msg=str(e))
    changed = True

    module.exit_json(changed=changed, result=result_check)


from ansible.module_utils.basic import *
from ansible.module_utils.ec2 import *

main()
