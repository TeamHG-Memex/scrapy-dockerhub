Scrapy DockerHub
===

Deploy, run and monitor your Scrapy spiders.

It utilizes Fabric command line utility to manage remote Docker containers that run Scrapy spiders

Installation
---

To use it in your scrapy project, you only need to create `fabfile.py` in your project directory with following content:

    from fabric.api import env

    env.hosts = ['my.scrapy.server.net']
    env.project = 'my-project'
    env.projects_path = '~/scrapy/projects'
    env.items_path = '~/scrapy/items'
    env.logs_path = '~/scrapy/logs'
    env.jobs_path = '~/scrapy/jobs'
    env.files_path = '~/scrapy/files'

    from scrapy_dockerhub.fabfile import *


In order to manage deploy hosts and paths, please make appropriate changes to this file. All directories will be created automatically.

`Dockerfile` will be automatically generated during `deploy` command (see below), but you can generate it manually by using command `prepare_dockerfile`

If you need to add some building steps or dependencies, please adjust Dockerfile to your needs

Commands
---

`prepare_dockerfile(force=True)`
---
generates sample Dockerfile in current directory. if `force=True`, existing file will be replaced


`deploy()`
---
uploads project to remote server, builds Docker image


`schedule(spider, args)`
---
runs new container with Scrapy spider. `args` are appended to scrapy command line

Example:

    fab schedule:spider=dmoz.com


`stop(spider, job)`
---
stops Scrapy container

Example:

    fab stop:spider=dmoz.com,job=18


`jobs()`
---
list all jobs with their stats (number of requests, items, errors)

Example output:

    project          spider   job     state   items   requests   errors
    abstracts    nature.com    10   running      54        113        0
    abstracts    nature.com     9   running      82        163        0
    abstracts    nature.com     8   running   1,346      2,498        0


`logs(spider, job)`
---
view `tail -f` of spider log

Example:

	fag logs:spider=dmoz.com,job=66
