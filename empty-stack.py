import boto3
import click
import logging
import sys

def setup_logging(log_stream=sys.stdout, log_level=logging.INFO):
  log = logging.getLogger(__name__)
  out_hdlr = logging.StreamHandler(log_stream)
  out_hdlr.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
  out_hdlr.setLevel(logging.INFO)
  log.addHandler(out_hdlr)
  log.setLevel(log_level)
  return log

logger = setup_logging()
cfn = boto3.client('cloudformation')

def stack_exists(stack_name, token):
    if token:
        response = cfn.list_stacks(NextToken=token)
    else:
        response = cfn.list_stacks()
    if 'StackSummaries' in response:
        stacks = response['StackSummaries']
        for stack in stacks:
            if stack['StackName'] == stack_name:
                if stack['StackStatus'] != 'DELETE_COMPLETE':
                    logger.info(f'Found existing stack with name: {stack_name}')
                    return True
    if 'NextToken' in response:
        return stack_exists(stack_name, response['NextToken'])
    else:
        return False

def create_empty_stack(stack_name):
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
    response = cfn.create_stack(
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
    logger.info(f'Successfully created stack: {stack_name}')
    return 0

def delete_stack(stack_name):
    cfn.delete_stack(
        StackName=stack_name
    )
    waiter = cfn.get_waiter('stack_delete_complete')
    waiter.wait(
        StackName=stack_name,
        WaiterConfig={
            'Delay': 10,
            'MaxAttempts': 180
        }
    )
    logger.info(f'Successfully deleted stack: {stack_name}')
    return 0

def update_stack(stack_name, template, parameters):
    cfn.update_stack(
        StackName=stack_name,
        TemplateBody=template,
        Parameters=parameters
    )
    waiter = cfn.get_waiter('stack_update_complete')
    waiter.wait(
        StackName=stack_name,
        WaiterConfig={
            'Delay': 10,
            'MaxAttempts': 180
        }
    )
    logger.info(f'Successfully updated stack: {stack_name}')
    return 0

def parse_params(params_file):
    params = []
    if params_file:
        import json
        logger.info(f'Parsing parameters from file: {params_file}')
        with open(params_file) as file:
            read_data = file.read()
            params = json.loads(read_data)
    return params

if __name__ == '__main__':
    @click.command()
    @click.option("--name", "stack_name", required=True, help="Name of stack to update.")
    @click.option("--template", required=False, help="Cloudformation template file location.")
    @click.option("--parameters", "params_file", required=False, help="Parameter file to use with the CloudFormation template.")
    # @click.option("--delete", required=False, expose_value=False, is_flag=True, help="Flag to delete the stack.")
    def cli(stack_name, template, params_file):
        if not stack_exists(stack_name, None):
            logger.info(f'Creating stack with name: {stack_name}')
            create_empty_stack(stack_name)
        params = parse_params(params_file)
        if template:
            logger.info(f'Reading template from file: {template}')
            with open(template) as file:
                read_data = file.read()
            logger.info(f'Updating stack: {stack_name}')
            update_stack(stack_name, read_data, params)
    cli()
