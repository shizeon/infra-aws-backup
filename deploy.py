#!/usr/bin/env python3

# Standard Libraries
import argparse
import logging
import os
import subprocess
import sys

# Extra Libraries
try:
    import yaml
    import boto3
    import botocore.exceptions
except ModuleNotFoundError:
    print("Please install external modules before proceeding: `pip install -r requirements.txt`")
    sys.exit(1)


__version__ = '1.0.0'

# Setup Constants from environment
LOGLEVEL = os.environ.get('LOGLEVEL', 'ERROR').upper()

# Setup logging library
logging.basicConfig(
    level=LOGLEVEL,
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(LOGLEVEL)


def parse_cli() -> argparse.Namespace:
    """_summary_

    Returns:
        argparse.Namespace: _description_
    """

    # CLI Parsing
    parser = argparse.ArgumentParser(
        usage='%(prog)s',
        description='Package Deployment'
    )
    parser.add_argument(
        '-v', '--version',
        help='Version of script',
        action='store_true',
        dest='version'
    )
    parser.add_argument(
        '--plan-only',
        help='Run deployment in planning mode',
        dest='plan', action='store_true'
    )
    parser.add_argument(
        '--deploy',
        help='Run full deployment',
        dest='deploy', action='store_true'
    )
    parser.add_argument(
        '--destroy',
        help='Remove and destroy deployment',
        dest='destroy', action='store_true'
    )
    parser.add_argument(
        '--create-backend',
        help='Create Terraform tfbackend file',
        dest='create_backend', action='store_true'
    )
    return parser.parse_args()


def main() -> None:
    """Execute Primary Deploy"""
    pass


def check_installed_dependencies():
    pass


def plan_only():
    _init_terraform()
    _print_header("Planning Terraform Execution")

    # TODO: #terraform plan -lock=false -var aws_region=$AWS_DEFAULT_REGION
    try:
        terraform_work_dir = _get_config()['terraform'].get('root_module')
        subprocess.run(
            ["terraform", "plan", "-lock=false"],
            check=True,
            cwd=terraform_work_dir
        )

    except Exception as e:
        raise SystemExit(f"Error: Unable to run terraform with message: {e}")


def deploy() -> None:
    """Do a full terraform plan then apply

    Raises:
        SystemExit: Reason why we couldn't continue
    """
    _init_terraform()
    _print_header("Deploying Terraform")
    # terraform plan -lock=false -var aws_region=$AWS_DEFAULT_REGION
    terraform_work_dir = _get_config()['terraform'].get('root_module')

    try:
        print("Building Terraform plan.")
        plan_result = subprocess.run(
            ["terraform", "plan", "-detailed-exitcode",
                "-out=tfplan", "-input=false", "-lock=false"],
            check=False,  # Handle detailed-exitcode
            cwd=terraform_work_dir,
        )

        if plan_result.returncode == 1:
            raise RuntimeError(plan_result.stderr)
        elif plan_result.returncode == 0:
            print("\nNo changes detected, skipping apply.")
        elif plan_result.returncode == 2:
            _print_header("Changes in plan detected, applying plan.")
            subprocess.run(
                ["terraform", "apply", "-input=false", "-lock=true", "tfplan"],
                check=True,
                cwd=terraform_work_dir,
            )
        else:
            # Unknown exit code, bail
            print("Exit code from terraform plan was an unknown %d" % plan_result.returncode)
            raise RuntimeError(plan_result.stderr)
    except subprocess.CalledProcessError as e:
        raise SystemExit("Error: Unable to run '{:s}'. Exit: {:d}. See log for error".format(
            " ".join(e.cmd),
            e.returncode,
        ))
    except Exception as e:
        raise SystemExit(
            f"Uncaught Error: Unable to run terraform with message: {e}")
    finally:
        # Cleanup tfplan file
        local_plan_file = os.path.join(terraform_work_dir, 'tfplan')
        if os.path.exists(local_plan_file):
            os.remove(local_plan_file)

#
# Private functions
#


def _init_terraform():
    create_backend_file()

    _print_header("Initializing Terraform Backend")

    # Runs from project root
    try:
        _setup_environment_variables()
        subprocess.run(["tfenv", "install"], check=True)
        subprocess.run(["tfenv", "use"], check=True)
    except subprocess.CalledProcessError as e:
        raise SystemExit("Error: Unable to run '{:s}'. Exit: {:d}. See log for error".format(
            " ".join(e.cmd),
            e.returncode,
        ))

    # Remove any stored state
    terraform_work_dir = _get_config()['terraform'].get('root_module')

    try:
        # Cleanup local state
        local_state_file = os.path.join(
            terraform_work_dir, '.terraform', 'terraform.tfstate')
        if os.path.exists(local_state_file):
            os.remove(local_state_file)

        # Terraform init
        subprocess.run(["terraform", "-version"], check=True, cwd=terraform_work_dir)
        subprocess.run(
            # Need to construct this
            ["terraform", "init", "-backend-config=config.s3.tfbackend"],
            check=True,
            cwd=terraform_work_dir
        )
    except subprocess.CalledProcessError as e:
        raise SystemExit("Error: Unable to run '{:s}'. Exit: {:d}. See log for error".format(
            " ".join(e.cmd),
            e.returncode,
        ))
    except Exception as e:
        raise SystemExit(
            f"Uncaught Error: Unable to run terraform init with message: {e}")


def create_backend_file(force: bool = False) -> None:
    _print_header("Remote State backend configuration")
    # Get SSM Client
    ssm_client = boto3.client('ssm')

    # Read in configuration
    config = _get_config()

    backend_file = os.path.join(
        config["terraform"]['root_module'], config['terraform']['backend']['file'])
    if os.path.exists(backend_file) and force is False:
        print(f"Using existing backend path at {backend_file}. Contents: \n")
    else:
        print(f"Generating a new {backend_file} file. Contents: \n")
        with open(backend_file, 'w') as file:
            backend_config = config['terraform']['backend']

            # TODO: Do some error checking here
            try:
                bucket = ssm_client.get_parameter(Name=backend_config['state_bucket_key'])[
                    'Parameter']['Value']
                dynamodb_table = ssm_client.get_parameter(
                    Name=backend_config['state_lock_table'])['Parameter']['Value']
            except Exception as e:  # TODO Do better here
                raise e

            # Write out file
            file.write('bucket = "{}"\n'.format(bucket))
            file.write('key = "{}"\n'.format(backend_config.get('key')))
            file.write('region = "{}"\n'.format(
                os.getenv('AWS_DEFAULT_REGION')))
            file.write('dynamodb_table = "{}"\n'.format(dynamodb_table))
            file.write('encrypt = {}\n'.format(backend_config.get('encrypt')))

    with open(backend_file, 'r') as file:
        for line in file.readlines():
            print(f"  {line}", end="")


def _get_config() -> dict:
    # Read in configuration
    with open('deploy.py.yaml', 'r') as file:
        config = yaml.safe_load(file)
    return config


def _setup_environment_variables() -> None:

    # Check for interactive shell, if not, turn off colors
    if os.isatty(sys.stdout.fileno()):
        os.environ['TF_CLI_ARGS'] = ""
    else:
        os.environ['TF_CLI_ARGS'] = "-no-color"

    os.environ['TF_IN_AUTOMATION'] = "1"


def check_environment():

    error = False
    error_str = "Missing Environment Variables. Please set: \n"
    if os.getenv('AWS_DEFAULT_REGION') is None:
        error = True
        error_str += "  - AWS_DEFAULT_REGION\n"

    # See if we can login go AWS
    try:
        sts_client = boto3.client('sts')
        sts_response = sts_client.get_caller_identity()
        user_arn = sts_response['Arn']
    except botocore.exceptions.NoCredentialsError as error:
        print("Unable to login to AWS. Please setup proper credentials")
        raise error
    except Exception as error:
        raise error

    # Friendly print errors
    if error:
        print("")
        raise SystemExit(error_str)

    # Setup expected TF_VARS
    os.environ['TF_VAR_aws_region'] = os.getenv('AWS_DEFAULT_REGION')

    # Print out current configuration for logs
    _print_header("Configuration")
    print("  Environment")
    print("    AWS_DEFAULT_REGION={}".format(os.getenv('AWS_DEFAULT_REGION')))
    print("    TF_VAR_aws_region={}".format(os.getenv('TF_VAR_aws_region')))
    print("")
    print("  Identity")
    print("    AWS User={}".format(user_arn))


def _print_header(text: str) -> None:
    print("")
    print("*" * 80)
    print(text)
    print("*" * 80)
    print("")


if __name__ == '__main__':

    args = parse_cli()

    if args.version is True:
        print(f'Version: {__version__}')
    else:
        try:
            # Validate Environment Variables
            check_environment()

            if args.create_backend:
                create_backend_file(force=True)
            else:
                # Execute
                if args.plan:
                    plan_only()
                elif args.destroy:
                    print("TODO: TBD Running full destroy")
                elif args.deploy:
                    deploy()
                else:
                    print("No argument was passed. Defaulting to deploy")
                    deploy()

            _print_header("Completed Successfully")
        except KeyboardInterrupt:  # Do not do a stack trace on a ctrl-c
            pass
        except Exception as e:
            _print_header(f"ERROR: Completed Unsuccessfully: {e}")
            raise e
