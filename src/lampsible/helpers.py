import os
from sys import path as sys_path
from yaml import safe_load
from ansible_runner import run_command


def find_package_project_dir():
    for path_str in sys_path:
        try:
            try_path = os.path.join(path_str, 'lampsible', 'project')
            assert os.path.isdir(try_path)
            return try_path
        except AssertionError:
            pass
    raise RuntimeError("Got no user supplied --project-dir, and could not find one in expected package location. Your Lampsible installation is likely broken. However, if you are running this code directly from source, this is expected behavior. You probably forgot to pass the '--project-dir' flag. The directoy you're looking for is 'src/lampsible/project/'.")


def ensure_ansible_galaxy_dependencies(galaxy_requirements_file):
    with open(galaxy_requirements_file, 'r') as stream:
        required_collections = []
        tmp_collections = safe_load(stream)['collections']
        for tmp_dict in tmp_collections:
            required_collections.append(tmp_dict['name'])

    # TODO There might be a more elegant way to do this - Right now,
    # we're expecting required_collections to always be a tuple,
    # and searching for requirements in a big string, but yaml/dict
    # would be better.
    installed_collections = run_command(
        executable_cmd='ansible-galaxy',
        cmdline_args=[
            'collection',
            'list',
            '--collections-path',
            os.path.join(USER_HOME_DIR, '.ansible'),
        ],
        quiet=True
    )[0]
    missing_collections = []
    for required in required_collections:
        if required not in installed_collections:
            missing_collections.append(required)
    if len(missing_collections) == 0:
        return 0
    else:
        return install_galaxy_collections(missing_collections)


def install_galaxy_collections(collections):
    ok_to_install = input("\nI have to download and install the following Ansible Galaxy dependencies into {}:\n- {}\nIs this OK (yes/no)? ".format(
        os.path.join(USER_HOME_DIR, '.ansible/'),
        '\n- '.join(collections)
    )).lower()
    while ok_to_install != 'yes' and ok_to_install != 'no':
        ok_to_install = input("Please type 'yes' or 'no': ")
    if ok_to_install == 'yes':
        print('\nInstalling Ansible Galaxy collections...')
        run_command(
            executable_cmd='ansible-galaxy',
            cmdline_args=['collection', 'install'] + collections,
        )
        print('\n... collections installed.')
        return 0
    else:
        print('Cannot run Ansible plays without Galaxy requirements. Aborting.')
        return 1
