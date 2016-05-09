#!/usr/bin/python

"""
IF YOU MOVE THIS FILE UPDATE THE PATHS!

iOS is complicated, we need to install some pip packages, but not all for various reasons
This script takes our top level requirements.txt file and generates a new one with the
blacklisted packages removed.
"""

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
