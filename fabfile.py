# -*- coding:  utf-8 -*-
"""
http.fabfile
~~~~~~~~~~~~

HTTP Request & Response service fabric commands file

:copyright: (c) 2011 by Alexandr Sokolovskiy (alex@obout.ru).
:license: BSD, see LICENSE for more details.
"""

import os

from __future__ import with_statement

import yaml
from fabric.api import *
from fabric.contrib.console import confirm
from fabric.contrib.files import upload_template, exists
from fabric.operations import require
from fabric.utils import warn


_rel = os.path.join


def _auto_params(b):
    "Set env from given args and kwargs"
    def _kwargs(f):
        def wrapper(*args, **kwargs):
            env.update(**kwargs)
            for name in args:
                if name in b: env[name] = True
                else: env[name] = prompt("Enter project %s: " % name)
            res = f()
            env.update(**kwargs)
            print env
        return wrapper
    return _kwargs


env.local_root = os.path.normpath(os.path.dirname(__file__))
env.default_config_file_path = _rel(env.local_root, '.config')


def testing(debug = None, config = None):
    "Run in testing mode"

    env.debug = True if debug else False
    env.production = False

    env.projects_path = _rel('/tmp/www/')
    env.config_file_path = config if config else _rel(env.local_root, '.debug_config')
    _import_config()

    env.project_path =  _rel(env.projects_path, env.project_name)
    env.releases = _rel(env.project_path, 'releases')
    env.current = _rel(env.releases, 'current')
    env.previous = _rel(env.releases, 'previous')
    env.configs = _rel(env.current, 'configs')

    print('Testing deployment for %(project_name)s' % env)


def production(debug = None, config = None):
    "Set production config"

    env.debug = True if debug else False
    env.production = True
    env.projects_path = _rel('/var/www/')
    env.config_file_path = config if config else env.default_config_file_path
    _import_config()


    env.project_path =  _rel(env.projects_path, env.project_name)
    env.releases = _rel(env.project_path, 'releases')
    env.current = _rel(env.releases, 'current')
    env.previous = _rel(env.releases, 'previous')
    env.configs = _rel(env.current, 'configs')
    env.local_repository = _rel(env.project_path, 'repository')

    import time
    env.release_time = time.strftime('%Y%m%d%H%M%S')
    env.release = _rel(env.releases, env.release_time)
    env.nginx_conf = '/etc/nginx/sites-enabled/%s.conf' % env.project_name
    env.monit_conf =  '/etc/monit/conf.d/%s.conf' % env.project_name

    env.project_venv = _rel(env.current, 'venv')
    print('Production deployment for %(project_name)s' % env)



def _import_config():
    "Import and set custom settings from file"

    require('config_file_path', provided_by = [production, testing])
    print("Tring to load %s" % env.config_file_path)
    if os.path.exists(env.config_file_path):
        config_file =  open(env.config_file_path, 'r')
        config = yaml.load(config_file.read())
        config_file.close()
        env.update(config)
    else:
        warn('Can\'t load config file. %s does\'t exists' % env.config_file_path)
    from pprint import pprint
    pprint(env)

def deploy():
    "Deployment project for given mode"
    require('project_path', provided_by = [production, testing])
    if not exists(env.project_path):
        setup()
    clone_project()
    create_environment()
    update_configs()
    _released_time()
    run('chown www-data:www-data -R %s/' % env.current)
    if confirm("Reload webservers?"):
        reload_webserver()
    else:
        print("Exec \"fab production reload_webserver\" for complete deployment")
    #print("Summary time for release: \n\t %s" % start - datetime.now())


def minor_update():
    "Deployment project for given mode"
    require('project_path', 'current', 'releases', 'release_time', provided_by = [production, testing])
    if exists(env.project_path):
        print("Try to minor update project")
        checkout()

        run("cp -rf %(local_repository)s/* %(current)s/" % env)
        run('rm -rf %(current)s/.git*' % env)
        with cd(env.current):
            run('mkdir -p %(configs)s' % env)
        update_configs()
        run('chown www-data:www-data -R %(current)s/' % env)
        _released_time()
        if confirm("Reload webservers?"):
            reload_webserver()
        else:
            print("Exec \"fab production reload_webserver\" for complete deployment")
    else:
        deploy()


def chown():
    """Add permissions for www-data
    """
    run('chown www-data:www-data -R %(current)s/' % env)

def _released_time():
    "Echo timestamp to file"

    with cd(env.current):
        run("echo '%s' > RELEASED" % env.release_time)


def remove_current():
    "Remove project from given servers"

    require('project_path', provided_by = [testing, production])
    if confirm("Do you want remove -> %(project_name)s?" % env):
        run('rm -rf %(current)s' % env)
        down()

def drop():
    "Remove project path with releases and configs"
    require('project_path', provided_by = [testing, production])
    if confirm("Do you want drop -> %(project_name)s?" % env):
        run('rm -rf %(project_path)s' % env)
        down()


def down():
    "Down off project"

    require('nginx_conf', provided_by = [testing, production])
    if confirm("Do you want down project?"):
        run('rm -f %s' % env.nginx_conf)
        run('rm -f %s' % env.monit_conf)
        reload_webserver()

def start_upgrade():
    "Set configs for upgrade"
    require('project_name', 'templates', 'nginx_conf', provided_by = [testing, production])
    print("Creating nginx conf: %s" % env.nginx_conf)
    upload_template('upgrading.template', env.nginx_conf, env, use_jinja = True, template_dir = _rel(env.local_root, env.templates))
    run("rm -rf %(nginx_conf)s.bak" % env)
    reload_webserver()


def reload_webserver():
    "Reloading webservers"
    require('current', provided_by = [testing, production])
    sudo('/etc/init.d/monit force-reload')
    sudo('/etc/init.d/nginx reload')
    with cd(env.current):
        sudo('%(current)s/manage.sh restart' % env)


def restart_webserver():
    "Restarting webservers"
    require('current', provided_by = [testing, production])
    sudo('/etc/init.d/monit restart')
    sudo('/etc/init.d/nginx restart')
    with cd(env.current):
        sudo('%(current)s/manage.sh restart' % env)


def stop_webserver():
    "Stop nginx and apache"
    require('current', provided_by = [testing, production])
    sudo('/etc/init.d/monit stop')
    sudo('/etc/init.d/nginx stop')
    with cd(env.current):
        sudo('%(current)s/manage.sh stop' % env)


def create_nginx():
    "Creating nginx config"
    require('project_name', 'templates', provided_by = [testing, production])
    print("Creating nginx conf: %s" % _rel(env.local_root, 'nginx.conf'))
    upload_template('nginx.template', _rel(env.configs, 'nginx.conf'),
                    env, use_jinja = True, template_dir = _rel(env.local_root, env.templates))



def create_monit():
    "Creating monit config for server"

    require('local_root', 'current', 'templates', provided_by = [testing, production])
    print("Creating  %s" % env.monit_conf)
    print("Creating monit conf: %s" % _rel(env.configs, 'monit.conf'))
    upload_template('monit.template', _rel(env.configs, 'monit.conf'),
                    env, use_jinja = True, template_dir = _rel(env.local_root, env.templates))


def update_configs():
    "Update server configs"
    print("Updating configs for current project")
    create_monit()
    create_nginx()
    update_symlinks()
    test_configs()


def clone_project():
    "Clone project to projects path"
    print("Try to clone project")
    require('project_path', 'current', 'releases', 'release_time', provided_by = [production, testing])
    create_previous()
    checkout()

    run("cp -rf %(local_repository)s %(release)s" % env)
    run('ln -snf %(release)s %(current)s' % env)
    run('rm -rf %(current)s/.git*' % env)
    with cd(env.current):
        run('mkdir -p %(configs)s' % env)
    run('chown www-data:www-data -R %(current)s/' % env)


def checkout():
    "Checkout given"
    require('local_repository', provided_by = [production, testing])
    pull()
    with cd(env.local_repository):
        run('git checkout %(branch)s' % env)
        run("git submodule update")


def create_previous():
    "Make symlink to previous release"

    require('current', 'previous', provided_by = [production, testing])
    print("Trying to create previous release")
    if exists(env.current):
        print("%(current)s exists. Creating previous." % env)
        run("mv -f %(current)s %(previous)s" % env)



def create_environment():
    "Creating project envoronment"
    with cd(env.current):
        run("./buildenv.sh")
        #run("virtualenv --python=python2.6 --clear venv")
        #run("./venv/bin/easy_install pip")
        #run("./venv/bin/pip install -E venv -r ./req.txt")


def setup():
    "Setup project structure"

    require('hosts', 'releases', 'project_repository', 'local_repository', 'project_path', provided_by = [production, testing])
    run('mkdir -p %(releases)s' % env)
    if exists(env.local_repository):
        if confirm('Remove current local project repository?'):
            run('rm -rf %(local_repository)s' % env)
            with cd(env.project_path):
                run("git clone %(project_repository)s %(local_repository)s" % env)
            with cd(env.local_repository):
                run("git submodule init; git submodule update")
        else:
            pull()
    else:
        with cd(env.project_path):
            run("git clone %(project_repository)s %(local_repository)s" % env)
        with cd(env.local_repository):
            run("git submodule init; git submodule update")
    run('chown www-data:www-data -R %(project_path)s' % env)


def reset():
    "Reset local repository"
    require('local_repository', provided_by = [production, testing])
    with cd(env.local_repository):
        run('git reset --hard')


def pull():
    "Get chenges from remote repository"
    require('local_repository', 'parent', 'branch', provided_by = [production, testing])
    with cd(env.local_repository):
        run("git pull %(parent)s %(branch)s" % env)


def rollback(release = None, llist = None):
    "Set previous successed release as current"
    require('releases', provided_by = [production, testing])
    print("Tring to rollback")
    with cd(env.releases):
        if llist:
            run('ls -la')
            return
        if release:
            create_previous()
            run('ln -snf %s %s' % (release, env.current))
        else:
            run("mv -f current _previous")
            run("mv -f previuos current")
            run("mv -f _previous previous")
        update_symlinks()
    if confirm("Reload webservers?"):
        reload_webserver()
    else:
        print("Exec \"fab production reload_webserver\" for complete deployment")


def update_symlinks():
    "Updating symlinks for current configs"

    print("Updating symlinks for current project")
    run('ln -sf %s %s' % (_rel(env.configs, 'nginx.conf'), env.nginx_conf))
    run('ln -sf %s %s' % (_rel(env.configs, 'monit.conf'), env.monit_conf))


def memcache():
    "Reset memcache"
    if "cache" in env:
        for s in env.cache:
            host, port = s.split(":")
            print("Starting: memcached -d -m 56 -u nobody -l %s -p %s -c 10 -P /var/run/memcache_%s.pid" % (host, port, host))
            sudo("memcached -d -m 56 -u nobody -l %s -p %s -c 10 -P /var/run/memcache_%s.pid" % (host, port, host))


def test_configs():
    "Test server configs"
    print("Test configs")
    run("nginx -t")
    run("/etc/init.d/monit syntax")


def cleanup():
    "Remove old releases."
    print("Remove old releases.")
