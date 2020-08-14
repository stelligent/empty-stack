# empty-stack
This repository was created to support a blog article about removing errors on CloudFormation stack creation.
By creating a stack with no infrastructure (an empty stack), then updating the stack with infrastructure, the stack will never be in a state where a stack cannot be updated. Thus, all errors are moved from the creation process to the update process, which currently has a much more robust rollback process.

The `slt.sh` file is to assist with linting and security best practices. `slt` stands for Scan and Lint Template.

## Installation
Download requirements:
```
pip install -r requirements.txt
```

## Example usage

Example usage without parameters file:
```
python3 empty-stack.py --name test-vpc --template vpc.yaml
```

Example usage with parameters file:
```
python3 empty-stack.py --name test-vpc --template vpc.yaml --parameters params.json
```

Example usage to just create the stack without infrastructure:
```
python3 empty-stack.py --name test-vpc
```

Example usage with aws-vault:
```
aws-vault exec your_profile -- python3 empty-stack.py --name test-vpc
```

## Further documentation

* Please see [boto3's documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html) on where credentials are pulled from.
* cfn-lint: [github](https://github.com/aws-cloudformation/cfn-python-lint)
* cfn_nag: [github](https://github.com/stelligent/cfn_nag) and [blog article](https://stelligent.com/2018/03/23/validating-aws-cloudformation-templates-with-cfn_nag-and-mu/)
