# empty-stack

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
aws-vault exec test_profile -- python3 empty-stack.py --name test-vpc
```

## Further documentation

Please see [boto3's documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html) on where credentials are pulled from.
