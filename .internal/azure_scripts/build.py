#! /usr/bin/env python3

from collections import OrderedDict, namedtuple
from argparse import ArgumentParser
import datetime
import os
import shutil
import json

SOLUTION_TEMPLATE_EX = '-solution-template'
MAIN_TEMPLATE = 'mainTemplate.json'
CREATE_UI_DEFINITION = 'createUiDefinition.json'
BUILD = 'BUILD'
NESTED_TEMPLATES_FOLDER = '/nestedtemplates'
JSON_INDENT_NUMBER = 2
QA = 'qa'
PROD = 'prod'
VNET_SUBNET_NEW = 'vnet-1-subnet-new.json'
VNET_SUBNET_EXISTING = 'vnet-1-subnet-existing.json'

NESTED_TEMPLATES = {
    "marketplace-management":
        [VNET_SUBNET_NEW, VNET_SUBNET_EXISTING, 'vnet-1-subnet-dualstack-new.json'],
    "marketplace-ha":
        ['vnet-2-subnet-ha2-new.json', 'vnet-2-subnet-ha2-existing.json', 'existing-nsg-RoleAssignment.json'],
    "marketplace-mds":
        [VNET_SUBNET_NEW, VNET_SUBNET_EXISTING, 'vnet-1-subnet-dualstack-new.json'],
    "marketplace-single":
        ['vnet-new.json', 'vnet-existing.json', 'vnet-2-subnet-dualstack-new.json'],
    "marketplace-single-waap":
        ['vnet-new.json', 'vnet-existing.json'],
    "marketplace-vmss":
        ['vnet-2-subnet-ha-new.json', 'vnet-2-subnet-ha-existing.json',
         'load-balancers.json', 'azure-func-sami.json', 'application-gateway.json', 'vnet-2-subnet-dualstack-new.json'],
    "marketplace-vmss-waap":
        ['vnet-2-subnet-ha-new.json', 'vnet-2-subnet-ha-existing.json',
         'load-balancers-waap.json'],
    "marketplace-checkme": [],
    "marketplace-gateway-load-balancer":
        [
            VNET_SUBNET_NEW,
            VNET_SUBNET_EXISTING,
            'gateway-load-balancers.json'
        ],
}

TEMPLATE_PID = {
    "marketplace-ha":
        {
            'qa': 'pid-550f7610-d681-428c-b21a-129913723328-partnercenter',
            'prod': 'pid-6f13b00a-7546-4ab2-be9f-c66815cc6c8b-partnercenter'
        },
    "marketplace-management":
        {
            'qa': 'pid-550f7610-d681-428c-b21a-129913723328-partnercenter',
            'prod': 'pid-6f13b00a-7546-4ab2-be9f-c66815cc6c8b-partnercenter'
        },
    "marketplace-mds":
        {
            'qa': 'pid-550f7610-d681-428c-b21a-129913723328-partnercenter',
            'prod': 'pid-6f13b00a-7546-4ab2-be9f-c66815cc6c8b-partnercenter'
        },
    "marketplace-single":
        {
            'qa': 'pid-550f7610-d681-428c-b21a-129913723328-partnercenter',
            'prod': 'pid-6f13b00a-7546-4ab2-be9f-c66815cc6c8b-partnercenter'
        },
    "marketplace-vmss":
        {
            'qa': 'pid-550f7610-d681-428c-b21a-129913723328-partnercenter',
            'prod': 'pid-6f13b00a-7546-4ab2-be9f-c66815cc6c8b-partnercenter'
        },
    "marketplace-gateway-load-balancer":
        {
            'qa': 'pid-550f7610-d681-428c-b21a-129913723328-partnercenter',
            'prod': 'pid-6f13b00a-7546-4ab2-be9f-c66815cc6c8b-partnercenter'
        }
}


def open_file(file_path):
    """
    Open sequence of files
    :params file_path: Absolute path to the file
    """
    data = namedtuple('open_file_data', ['status', 'file_pointer', 'file_json'])
    # Check if the file exists and the file path is absolute
    if not os.path.exists(file_path) or not os.path.isabs(file_path):
        return data(status=False, file_pointer=None, file_json=None)

    file_pointer = open(file_path, 'r+')  # Open the file in R/W mode
    file_data = file_pointer.read()

    # Load the json
    file_json = json.loads(file_data, object_pairs_hook=OrderedDict)

    return data(status=True, file_pointer=file_pointer, file_json=file_json)


def close_file(file_pointer, file_json):
    """
    Close sequence of files
    :params file_pointer: A pointer rto the file
    :params file_json: Json data of the file
    """
    file_pointer.seek(0)  # Go to the start of the file
    file_pointer.truncate(0)  # Clear the file

    file_data = json.dumps(file_json, indent=JSON_INDENT_NUMBER, separators=(',', ': '))

    file_pointer.write(file_data)
    file_pointer.close()


def get_files_for_solution(solution, nested_templates_path):
    """
    Get all the necessary files for the solution
    """
    # Get the mainTemplate.json and createUIDefinition.json files from the solution folder
    current_directory_files = [f for f in os.listdir(os.getcwd()) if os.path.isfile(f)
                               and (MAIN_TEMPLATE == f or CREATE_UI_DEFINITION == f)]

    # Get all the nested templates for the solution from the nested template folder
    nested_templates_files = [f for f in os.listdir(nested_templates_path) if
                              os.path.isfile(os.path.join(nested_templates_path, f))
                              and (solution in NESTED_TEMPLATES)
                              and (f in NESTED_TEMPLATES[solution])]

    files = current_directory_files + nested_templates_files
    return files  # Return a list of the files


def edit_and_copy_files(files, nested_templates_path, branch, preview):
    """
    Copy each file from the list to the BUILD folder and change the suitable values
    """
    for f in files:
        if CREATE_UI_DEFINITION == f:  # For the createUIDefinition.json copy the file than change the visible value
            shutil.copy(f, BUILD)
            change_ui_visible(os.path.join(os.getcwd(), BUILD, CREATE_UI_DEFINITION), branch)

        elif MAIN_TEMPLATE == f:  # For the mainTemplate.json copy the file than set new attributes
            shutil.copy(f, BUILD)
            add_attributes(os.getcwd() + '/' + BUILD + '/', f, branch=branch,
                           template_name=os.path.basename(os.getcwd()), preview=preview)

        else:  # For the nested template file copy the file into BUILD/nestedtemplates folder
            shutil.copy(nested_templates_path + '/' + f, BUILD + NESTED_TEMPLATES_FOLDER)
            add_attributes(os.getcwd() + '/' + BUILD + NESTED_TEMPLATES_FOLDER + '/', f, branch=branch,
                           template_name=os.path.basename(os.getcwd()), preview=preview)


def add_attributes(path, file, branch, template_name, preview):
    """
    Change file attributes
    """
    complete_file = path + file
    if not os.path.exists(complete_file):  # Check if the file is existing
        print(f'File {complete_file} is not exists')
        return

    print("Adding attributes for " + file)
    open_file_data = open_file(complete_file)  # Open the file
    if not open_file_data.status:  # Check if was able to open the file
        print(f'Got error trying to open file: {complete_file}')
        return

    for r in open_file_data.file_json['resources']:  # For each resource
        if r['type'] == 'Microsoft.Resources/deployments':  # Check if it type deployments
            if template_name in TEMPLATE_PID and r['name'].startswith('pid-'):
                r['name'] = TEMPLATE_PID[template_name][branch]  # Set the name to the pid value

    # Add -preview tag to the imageOffer variable if preview is True
    if preview and 'variables' in open_file_data.file_json and 'imageOffer' in open_file_data.file_json['variables']:
        image_offer = open_file_data.file_json['variables']['imageOffer'][:-2]
        image_offer += ', \'-preview\')]'

        open_file_data.file_json['variables']['imageOffer'] = image_offer

    # Rewrite the file with the new attributes
    close_file(open_file_data.file_pointer, open_file_data.file_json)


def set_visibility(branch, c):
    """
    helper functions for change_ui_visible
    """
    if branch == 'prod':
        c['visible'] = False
    elif branch == 'qa':
        c['visible'] = True


def change_ui_visible(file, branch):
    """
    Change the key 'visible' in the file createUiDefinition.json to true or false
    """
    # Open the file
    open_file_data = open_file(file)
    if not open_file_data.status:  # Check if was able to open the file
        print(f'Got error trying to open file: {file}')
        return

    for r in open_file_data.file_json['parameters']['steps']:
        if r['name'].startswith('chkp') or r['name'] == 'autoprovision':
            for c in r['elements']:  # Search for the useCustomImageUri element
                if c['name'] == 'useCustomImageUri':
                    # Change the visible parameter according to the branch
                    set_visibility(branch, c)

                    break

    # Close the file
    close_file(open_file_data.file_pointer, open_file_data.file_json)


def test(path, file):
    # TODO
    print("Running automation tests from Azure/azure-quickstart-templates")


def create_zip():
    """
    Create zip folder inside the BUILD folder
    """
    print("Creating zip....")
    new_folder_name = (os.path.basename(os.getcwd())).split('-', 1)[1]
    file_format = 'zip'
    src_folder = f'{os.getcwd()}/{BUILD}'
    dst_folder = f'{src_folder}/{new_folder_name + SOLUTION_TEMPLATE_EX}'

    # 1 - Copy all the files from src_folder to dst_folder
    shutil.copytree(src_folder, dst_folder)
    # 2 - Create a zip from the new created folder
    shutil.make_archive(dst_folder, file_format, dst_folder)
    # 3 - remove unzipped folder name
    shutil.rmtree(dst_folder)


def get_nested_templates_folder(solution):
    """
    If the ntp flag is none create the path to the nestedtemplates folder
    """
    basename = os.path.basename(solution)
    base_path = solution.replace(basename, '')[:-1]
    nestedtemplates_folder = base_path + NESTED_TEMPLATES_FOLDER
    return nestedtemplates_folder


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


def change_template_version(file, version=None):
    """
    Change the version in the original template
    """
    if not os.path.exists(file):  # Check if the file is exist
        print(f'File {file} is not exists')
        return

    open_file_data = open_file(file)
    if not open_file_data.status:  # Check if was able to open the file
        print(f'Got error trying to open file: {file}')
        return

    if version is None:  # If the version is empty set the current date to the version number
        open_file_data.file_json['variables']['templateVersion'] = datetime.datetime.now().strftime("%Y%m%d")

    else:  # Else set the version to the version parameter
        open_file_data.file_json['variables']['templateVersion'] = version

    # Rewrite the file with the new data
    close_file(open_file_data.file_pointer, open_file_data.file_json)


def get_args():
    """
    Get the program argument
    """
    parser = ArgumentParser(description="Build Templates")  # Build parser object

    # Add arguments to the parser object
    parser.add_argument('-b', "--branch", required=True,
                        help="QA or PROD.")
    parser.add_argument("-sn", "--solution", required=True,
                        help="The solution absolute path to the solution directory.")
    parser.add_argument("-ntp", "--nestedtemplates", required=False,
                        help="Nested templates directory absolute path.")
    parser.add_argument("-tv", "--templateversion", required=False,
                        help="Template version number.")
    parser.add_argument("-pre", "--preview", required=False, action='store_true',
                        help="Preview image offer.")

    return parser.parse_args()  # Parse the arguments


def validate_args(branch, solution, nested_templates, template_version):
    """
    Validate all the arguments
    """
    if branch != QA and branch != PROD:  # Validate the pid type value
        print('Argument \'branch\' must be wither one of the following: qa or prod.')
        return False

    if os.path.isfile(solution):  # Check if the solution folder is valid
        print('Argument \'-sn\' must be path to a folder.')
        return False

    # Check if the ntp parameter is valid
    if nested_templates is not None and os.path.isfile(nested_templates):
        print('Argument \'-ntp\' must be path to a folder.')
        return False

    # Valid the template version value
    if not validate_template_version(template_version):
        print(f'Version is invalid. The version is {template_version}')
        return False

    return True


def build(branch, solution_folder, nested_templates_folder, basename, template_version, preview):
    """
    Build the solution for the template
    """
    os.chdir(solution_folder)  # Change the current directory to the solution folder
    if os.path.exists(BUILD):  # Delete the BUILD folder if its exists
        shutil.rmtree(BUILD)

    os.makedirs(BUILD)  # Create the BUILD folder
    os.makedirs(BUILD + NESTED_TEMPLATES_FOLDER)  # Create the nested template folder inside the BUILD folder

    # Change the template version in the original mainTemplate.json
    change_template_version(os.path.join(solution_folder, MAIN_TEMPLATE), template_version)

    files = get_files_for_solution(basename, nested_templates_folder)  # Get the files
    edit_and_copy_files(files, nested_templates_folder, branch, preview)
    create_zip()


def main():
    """
    Main function
    """
    args = get_args()  # Get the program argument

    branch = args.branch.lower()
    solution_folder = args.solution
    nested_templates_folder = args.nestedtemplates if (args.nestedtemplates is not None
                                                       and args.nestedtemplates != 'None') else None
    template_version = args.templateversion if (args.templateversion is not None
                                                and args.nestedtemplates != 'None') else None
    preview = args.preview

    # Check if the arguments are valid
    is_valid = validate_args(branch, solution_folder, nested_templates_folder, template_version)
    if not is_valid:
        return

    if nested_templates_folder is None:
        nested_templates_folder = get_nested_templates_folder(solution_folder)

    # Get the correct folders base on the arguments input
    if os.path.isabs(solution_folder):
        basename = os.path.basename(solution_folder)
        templates_path = os.path.dirname(solution_folder)

    else:
        basename = solution_folder
        templates_path = os.getcwd()

    if basename not in os.listdir(templates_path):  # Check if the solution folder is under the template folder
        print(f'Solution name {solution_folder} not found under {templates_path}. Please see build usage --help')
        return

    try:
        build(
            branch=branch,
            solution_folder=solution_folder,
            nested_templates_folder=nested_templates_folder,
            basename=basename,
            template_version=template_version,
            preview=preview
        )

    except (OSError, IndexError, json.JSONDecodeError) as ex:  # Catch the errors and than raise them again
        raise ex

    print("Finished building process successfully.")
    print("Please verify you run automatic tests from PowerShell before proceeding.")


if __name__ == '__main__':
    main()
    exit(0)
