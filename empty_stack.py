"""
empty_stack.py creates an empty cloudformation stack, then updates the stack.

Creating the stack without infrastructure allows rollbacks that don't require
the stack to be deleted on an error.

Example usage:
  python3 empty_stack.py --name main_vpc --template vpc.yaml --parameters params.json
"""
import logging
import sys

import boto3
import optparse


def setup_logging(log_stream=sys.stdout, log_level=logging.INFO):
    """Sets up logging."""
    logging.basicConfig(level=options.log)
    log = logging.getLogger(__name__)
    out_hdlr = logging.StreamHandler(log_stream)
    out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    # out_hdlr.setLevel(logging.INFO)
    log.addHandler(out_hdlr)
    log.setLevel(log_level)
    return log

def stack_exists(stack_name, token):
    """Determines if CloudFormation stack exists with given name."""
    if token:
        response = cfn.list_stacks(NextToken=token)
    else:
        response = cfn.list_stacks()
    if 'StackSummaries' in response:
        stacks = response['StackSummaries']
        for stack in stacks:
            if stack['StackName'] == stack_name:
                if stack['StackStatus'] != 'DELETE_COMPLETE':
                    logger.info('Found existing stack with name: %s', stack_name)
                    return True
    if 'NextToken' in response:
        return stack_exists(stack_name, response['NextToken'])
    return False

def create_empty_stack(stack_name, cfn):
    """Create CloudFormation stack with no infrastructure."""
    json = """
    {
      'AWSTemplateFormatVersion' : '2010-09-09',
      'Conditions' : {
          'HasNot': { 'Fn::Equals' : [ 'a', 'b' ] }
      },
      'Resources' : {
          'NullResource' : {
              'Type' : 'Custom::NullResource',
              'Condition' : 'HasNot'
          }
      }
    }
    """
    cfn.create_stack(
        StackName=stack_name,
        TemplateBody=json
    )
    waiter = cfn.get_waiter('stack_create_complete')
    waiter.wait(
        StackName=stack_name,
        WaiterConfig={
            'Delay': 3,
            'MaxAttempts': 100
        }
    )
    logger.info(' Successfully created stack: %s', stack_name)
    return 0

def update_stack(stack_name, template, parameters, iam, cfn):
    """Update existing CloudFormation stack."""
    iam_capabilities = []
    if iam:
        iam_capabilities = ['CAPABILITY_NAMED_IAM']
    try:
        cfn.update_stack(
            StackName=stack_name,
            TemplateBody=template,
            Parameters=parameters,
            Capabilities=iam_capabilities
        )
        waiter = cfn.get_waiter('stack_update_complete')
        waiter.wait(
            StackName=stack_name,
            WaiterConfig={
                'Delay': 10,
                'MaxAttempts': 180
            }
        )
    except  Exception as e:
        a = str(e).split(':')
        end = len(a)
        if 'No updates' in a[end -1]:
            logger.info(stack_name+  " : " + a[end -1])
        else:
            logger.error(e)
            sys.exit(1)  
    logger.info(' Successfully updated stack: %s', stack_name)
    return 0

def update_stack_url(stack_name, templateURL, parameters, iam, cfn):
    """Update existing CloudFormation stack."""
    iam_capabilities = []
    if iam:
        iam_capabilities = ['CAPABILITY_NAMED_IAM']
    try: 
        cfn.update_stack(
            StackName=stack_name,
            TemplateURL=templateURL,
            Parameters=parameters,
            Capabilities=iam_capabilities
        )
        waiter = cfn.get_waiter('stack_update_complete')
        waiter.wait(
            StackName=stack_name,
            WaiterConfig={
                'Delay': 10,
                'MaxAttempts': 180
            }
        )
    except  Exception as e:
        a = str(e).split(':')
        end = len(a)
        if 'No updates' in a[end -1]:
            logger.info(stack_name+  " : " + a[end -1])
        else:
            logger.error(e)
            sys.exit(1)       
    logger.info('Successfully updated stack: %s', stack_name)
    return 0


def parse_params(params_file):
    """Parse parameters into list. If no params passed in, return empty list."""
    params = []
    if params_file:
        import json
        logger.info('Parsing parameters from file: %s', params_file)
        with open(params_file) as file:
            read_data = file.read()
            params = json.loads(read_data)
    return params

def cfn_conn(region):
    cfn = boto3.client('cloudformation', region_name=region)
    return cfn


if __name__ == '__main__':
    global options,cft
    argv = None
    parser = optparse.OptionParser(usage="%prog", version="%prog 1.0.0")
    parser.add_option("-n", "--name", dest="stack_name", type="string", help="Name of stack to update.")
    parser.add_option("-t", "--template", dest="template", default=False,type="string", help="Cloudformation template file location.")
    parser.add_option("-u", "--templateURL", dest="templateURL", type="string", help="Cloudformation template url location.")
    parser.add_option("-p", "--parameters", dest="params_file", type="string", help="Parameter file to use with the CloudFormation template.")
    parser.add_option("-i", "--iam", dest="iam", default=False, help="Add this flag to use iam capabilites.")
    parser.add_option("-r", "--region", dest="region", default="us-west-2", type="string", help="set aws region")
    parser.add_option("-l", "--log", dest="log", type="string",
                            default='WARNING', help="Set log level DEBUG,INFO,WARNING")
    if argv is None:
        argv = sys.argv
    (options, args) = parser.parse_args(args=argv[1:])
    logger = setup_logging(log_level=options.log)
    stack_name = options.stack_name
    template = options.template
    templateURL = options.templateURL
    params_file = options.params_file
    iam = options.iam
    region = options.region  

    def cli(stack_name, template, templateURL, params_file, iam, cfn):
        """Command Line Interface logic"""
        if not stack_exists(stack_name, None):
            logger.info(' Creating stack with name: %s', stack_name)
            create_empty_stack(stack_name, cfn)
        params = parse_params(params_file)
        if template:
            logger.info(' Reading template from file: %s', stack_name)
            with open(template) as file:
                read_data = file.read()
            if len(read_data) <= 51200:
                logger.info('Updating stack: %s', stack_name)
                update_stack(stack_name, read_data, params, iam, cfn)
            else:
                logger.error(" CFN Template file size is to large to use as a local file, please upload to s3 and use --templateURL instead")
        elif  templateURL != None:
            logger.info(' Using templateUrl from URL: %s', templateURL)
            update_stack_url(stack_name, templateURL, params, iam, cfn)     
        else:
            logger.error(' No Cloudformation templates selected!')

    # pylint: disable=no-value-for-parameter
    cfn = cfn_conn(region)
    sys.exit(cli(stack_name, template, templateURL, params_file, iam, cfn))
