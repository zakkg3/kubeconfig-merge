#!/usr/bin/env python

import glob
import os
import shutil
import datetime
import time
import yaml


def ysl(fn):
    with open(os.path.expanduser(fn), 'r') as fd:
        return yaml.safe_load(fd.read())


def prefix_username(prefix, config):
    for user in config['users']:
        user_name = user['name']
        prefixed_name = f"{prefix}-{user['name']}"
        user['name'] = prefixed_name
        for context in config['contexts']:
            if context['context']['user'] == user_name:
                context['context']['user'] = prefixed_name


def merge_configs():
    current = ysl('~/.kube/config')
    new = {
        'apiVersion': 'v1',
        'kind': 'Config',
        'current-context': current.get('current-context', None),
        'preferences': current.get('preferences', {}),
        'clusters': [],
        'contexts': [],
        'users': [],
    }
    new['current-context'] = current['current-context']
    config_dir = os.path.expanduser('~/.kube/config.d')
    db = {
        'users': {},
        'contexts': {},
        'clusters': {},
    }
    for config_file in glob.glob(f'{config_dir}/*'):
        config = ysl(config_file)
        config_file_name = os.path.basename(config_file)
        config_name = os.path.splitext(config_file_name)[0]
        prefix_username(config_name, config)
        for key in 'clusters', 'contexts', 'users':
            db[key][config_name] = config[key]

    new['clusters'] = [i for l in db['clusters'].values() for i in l]
    new['contexts'] = [i for l in db['contexts'].values() for i in l]
    new['users'] = [i for l in db['users'].values() for i in l]

    return new


if __name__ == '__main__':
    # Backup of current config file.
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d--%H:%M:%S')
    config_file = os.path.expanduser('~/.kube/config')
    backup_file = os.path.expanduser('~/.kube/config-')+st
    print (f'Config {config_file} - Backed up to {backup_file}')
    
    try:
        shutil.copy(config_file, backup_file)
    except FileNotFoundError:
        pass

    new_config = merge_configs()
    with open(os.path.expanduser('~/.kube/config'), 'w') as fd:
        yaml.dump(new_config, fd, sort_keys=False)
