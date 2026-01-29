#! /usr/bin/env python3

from argparse import ArgumentParser
import subprocess
import os


IGNORE_FOLDERS = ['.vscode', '.git', '.idea', 'icons', 'scripts', 'nestedtemplates', 'testdrive-r8010', 'marketplace-checkme',
                  'marketplace-cluster', 'marketplace-shift', 'marketplace-single-waap', 'marketplace-stack-ha',
                  'marketplace-stack-management', 'marketplace-stack-single', 'marketplace-vmss-waap', 'deprecated',
                  '.spectral', 'china']
BUILD_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build.py')
QA = 'qa'
PROD = 'prod'


def build(solution, nested_templates, branch, template_version, preview):
    """
    Build template for specific folder
    """
    # Create command line with required fags
    command = ['python3', f'{BUILD_FILE}', '-b', f'{branch}', '-sn', f'{solution}']

    # Add optional flags if set
    if nested_templates != '':
        command.append('-ntp')
        command.append(f'{nested_templates}')

    if template_version != '' and template_version is not None:
        command.append('-tv')
        command.append(f'{template_version}')

    if preview:
        command.append('-pre')

    # Run the command line using subprocess
    output = subprocess.run(command, capture_output=True)

    # Get the subprocess exit code
    if output.returncode == 0:  # If subprocess succeed print it output
        print(output.stdout.decode())

    elif output.returncode != 0:  # If failed raise ChildProcessError
        raise ChildProcessError(f'Process failed due to error:\n{output.stderr.decode()}')


def build_all(solution_folder, nested_templates, branch, template_version, preview):
    """
    For each folder in the requested folder directory
    """
    # Get all the sub folders in the solutions folder
    subfolders = [fol for fol in os.listdir(solution_folder) if os.path.isdir(os.path.join(solution_folder, fol))
                  and fol not in IGNORE_FOLDERS]

    for subfolder in subfolders:  # For each sub folder
        try:
            print(f'\nBuild template for {subfolder}')
            build(solution=os.path.join(solution_folder, subfolder), nested_templates=nested_templates,
                  branch=branch, template_version=template_version, preview=preview)  # Run the build command

        except ChildProcessError as ex:  # Except error from the subprocess
            print(ex)  # Print the error and return exit code -1
            return -1

    return 0  # If every subprocess succeed return exit code 0


def validate_template_version(version):
    """
    Validate the format of the version
    """
    if version is None:
        return True

    version = str(version)
    if len(version) != 8 or not version.isdigit():
        return False

    return True


def parse_args():
    """
    Parse the program arguments
    """
    parser = ArgumentParser(description="Build all Templates")
    parser.add_argument("-b", "--branch", required=False,
                        help="QA or PROD.")
    parser.add_argument("-sn", "--solution", required=False,
                        help="The solution absolute path to the solution directory.")
    parser.add_argument("-ntp", "--nestedtemplates", required=False,
                        help="Nested templates directory absolute path.")
    parser.add_argument("-tv", "--templateversion", required=False,
                        help="Template version number.")
    parser.add_argument("-pre", "--preview", required=False, action='store_true',
                        help="Preview image offer.")

    return parser.parse_args()


def validate_args(branch, solution, nested_templates, template_version):
    """
    Validate all the arguments
    """
    if branch != QA and branch != PROD:  # Check if the branch parameter is valid
        print('Argument \'branch\' must be wither one of the following: qa or prod.')
        return False

    if os.path.isfile(solution):  # Check if the sn parameter is valid
        print('Argument \'-sn\' must be path to a folder.')
        return False

    if nested_templates is not None and os.path.isfile(nested_templates):  # Check if the ntp parameter is valid
        print('Argument \'-ntp\' must be path to a folder.')
        return False

    if not os.path.exists(solution):  # Check if the solutions folder exist
        print(f'Path to folder {solution} is not exists')
        return False

    # Check if the template version is valid
    if not validate_template_version(template_version):
        print('Version is invalid.')
        return False

    return True


def main():
    """
    Main function
    """
    args = parse_args()

    # Insert default values to each argument if it not has been determined
    branch = args.branch.lower() if args.branch is not None else QA
    if args.solution is not None:
        solution_folder = args.solution
    else:
        solution_folder = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'azure', 'templates'))
    nested_templates = args.nestedtemplates
    template_version = args.templateversion
    preview = args.preview if args.preview else False

    # Check if the flags are valid
    is_valid = validate_args(branch, solution_folder, nested_templates, template_version)
    if not is_valid:
        return

    # Build all the templates
    is_error = build_all(solution_folder, nested_templates, branch, template_version, preview)

    # Print message to the user that depend on the finishing status
    if is_error == 0:
        print('\nProgram finished successfully.')

    elif is_error == -1:
        print('\nStopping the program due to an error.')


if __name__ == '__main__':
    main()
