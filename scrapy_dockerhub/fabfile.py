import re
import json
import sys
from os import listdir, getcwd
from os.path import dirname, join, exists
from tempfile import mkdtemp

from fabric.api import run, env, cd, quiet, lcd, local
from fabric.contrib.project import rsync_project

from scrapy_dockerhub.pprint_table import pprint_table


env.project_path = join(env.projects_path, env.project)


def prepare_dockerfile(force=False):
    if not exists('Dockerfile') or force:
        with open(join(dirname(__file__), 'Dockerfile.template')) as src:
            with open('Dockerfile', 'w') as dst:
                dst.write(src.read())


def prepare_server():
    has_docker = False
    with quiet():
        has_docker = run('docker --version').succeeded
    if not has_docker:
        run('sudo apt-get install -y docker.io')
    run('mkdir -p {} {} {} {} {}'.format(
        env.project_path, env.items_path, env.logs_path, env.jobs_path,
        env.files_path))


def upload():
    '''TODO: allow to upload via git'''
    rsync_project(remote_dir=env.project_path,
                  local_dir='./', delete=True,
                  exclude=['.git', '*.pyc', 'dist', 'build', '.scrapy'])


def _fixme_build_extension():
    '''There is probably better way to install extension, eg. via git'''
    cwd = getcwd()
    with lcd(join(dirname(__file__), '..')):
        local('rm -rf __dist')
        local('python setup.py sdist -d __dist')
        local('mv __dist/*.tar.gz {}/scrapy-dockerhub.tar.gz'.format(cwd))


def _fixme_cleanup_extension():
    local('rm -f scrapy-dockerhub.tar.gz')


def build_docker_image():
    with(cd(env.project_path)):
        run('sudo docker build -t scrapy-{} .'.format(env.project))


def deploy():
    prepare_dockerfile()
    prepare_server()
    _fixme_build_extension()
    upload()
    _fixme_cleanup_extension()
    build_docker_image()


def schedule(spider, args=''):
    jobs_dir = join(env.jobs_path, env.project, spider)
    with quiet():
        run('mkdir -p {}'.format(jobs_dir))
        all_jobs = run('ls -1 {}'.format(jobs_dir))
    jobs = map(int, re.findall('\d+', all_jobs))
    if jobs:
        latest_job = max(jobs)
    else:
        latest_job = 0
    job = latest_job + 1
    job_path = join(jobs_dir, str(job))

    run('touch {}'.format(job_path))

    items_dir = join(env.items_path, env.project, spider)
    run('mkdir -p {}'.format(items_dir))
    items_path = join(items_dir, str(job) + '.jl')
    run('touch {}'.format(items_path))

    logs_dir = join(env.logs_path, env.project, spider)
    run('mkdir -p {}'.format(logs_dir))
    logs_path = join(logs_dir, str(job) + '.log')
    run('touch {}'.format(logs_path))

    files_dir = join(env.files_path, env.project, spider, str(job))
    run('mkdir -p {}'.format(files_dir))

    run('sudo docker run -d -t -i '
        '--name scrapy---{project}---{spider}---{job} '
        '-v {job_path}:/data/job '
        '-v {items_path}:/data/items.jl '
        '-v {logs_path}:/data/log.log '
        '-v {files_dir}:/data/files '
        'scrapy-{project} '
        'scrapy crawl {spider} {args}'
        '-s FILES_DIR=/data/files '
        '-s JOB_PATH=/data/job '
        '-o /data/items.jl '
        '--logfile /data/log.log'
        .format(job_path=job_path,
                items_path=items_path,
                logs_path=logs_path,
                files_dir=files_dir,
                project=env.project,
                spider=spider,
                job=job,
                args=args))


def stop(spider, job):
    run('sudo docker stop -t 120 scrapy---{project}---{spider}---{job}'
        .format(project=env.project,
                spider=spider,
                job=job))


def jobs():
    local_jobs_dir = mkdtemp()
    # Download all job infos  TODO: is there better way?
    with quiet():
        rsync_project(remote_dir=env.jobs_path + '/',
                      local_dir=local_jobs_dir,
                      upload=False)
    table = []
    table.append(['project', 'spider', 'job', 'state', 'items', 'requests',
                  'errors'])

    running = set()
    with quiet():
        docker_ps = run('sudo docker ps | grep scrapy---')
        for line in docker_ps.splitlines():
            container_id = line.split()[-1]
            _, project, spider, job = container_id.split('---')
            running.add((project, spider, job))

    for project in sorted(listdir(local_jobs_dir)):
        project_path = join(local_jobs_dir, project)
        for spider in sorted(listdir(project_path)):
            spider_path = join(project_path, spider)
            for job in sorted(map(int, listdir(spider_path)), reverse=True):
                job = str(job)
                items = '-'
                requests = '-'
                errors = '-'
                state = 'unknown'
                job_path = join(spider_path, job)
                with open(job_path) as f:
                    try:
                        job_info = json.load(f)
                    except ValueError:
                        pass
                    else:
                        stats = job_info['stats']
                        if 'finish_reason' in stats:
                            state = 'done ({})'.format(stats['finish_reason'])
                        elif (project, spider, job) in running:
                            state = 'running'
                        items = stats.get('item_scraped_count', 0)
                        requests = stats.get('response_received_count', 0)
                        errors = stats.get('log_count/ERROR', 0)
                table.append([project, spider, job, state, items, requests,
                              errors])

    pprint_table(sys.stdout, table)


def logs(spider, job):
    logfile = join(env.logs_path, env.project, spider, job + '.log')
    run('tail -f {}'.format(logfile))
