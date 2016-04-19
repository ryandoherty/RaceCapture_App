#!/usr/bin/python
import os
local_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.dirname(os.path.join(local_dir, '../../'))
ios_requirements_file_path = os.path.join(root_dir, 'ios_requirements.txt')

if os.path.isfile(ios_requirements_file_path):
    os.remove(ios_requirements_file_path)

exclude_list = open(os.path.join(local_dir, 'ios_pip_exclude.txt'), 'r').read().split('\n')
req_list = open(os.path.join(root_dir, 'requirements.txt'), 'r').read().split('\n')

exclude_list = [name for name in exclude_list if len(name) > 0]


def included(package_name):
    include = True
    for excluded in exclude_list:
        if package_name.startswith(excluded):
            include = False
            break

    return include

ios_requirements_file = open(ios_requirements_file_path, 'w')


include_list = filter(included, req_list)

ios_requirements_file.write("\n".join(include_list))
ios_requirements_file.close()
