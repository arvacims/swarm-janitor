# Docker Swarm Janitor for Amazon Web Services (AWS)

Docker Swarm Janitor executes maintenance tasks for your Docker Swarm cluster which
* is deployed on Amazon EC2 auto-scaling groups (one for the manager nodes and one for the worker nodes),
* is using Amazon ECR as private Docker registry.


## Features (production ready)

Docker Swarm Janitor is a light-weight daemon process deployed as Docker image (see below) which
* executes `docker system prune --force [--all] [--volumes]` at the configured rate,
* executes `docker login` (into your ECR) and `docker service update --with-registry-auth` at the configured rate.


## Features (announced)

Docker Swarm Janitor automatically
* discovers manager nodes,
* retrieves join tokens, and
* ensures all nodes (re-)join the cluster.


## Usage

In production environments, use an instance profile instead of the access key.
~~~~
$ docker run \
    --env "AWS_ACCESS_KEY_ID=********************" \
    --env "AWS_SECRET_ACCESS_KEY=****************************************" \
    --env "AWS_DEFAULT_REGION=eu-west-1" \
    --env "SWARM_REGISTRY=************.dkr.ecr.eu-west-1.amazonaws.com" \
    --env "SWARM_DESIRED_ROLE=worker" \
    --env "SWARM_MANAGER_NAME_FILTER=foo-bar-manager" \
    --env "SWARM_INTERVAL_PRUNE_SYSTEM=86400" \
    --env "SWARM_INTERVAL_REFRESH_AUTH=36000" \
    --env "SWARM_PRUNE_IMAGES=true" \
    --env "SWARM_PRUNE_VOLUMES=true" \
    --detach \
    --health-cmd 'curl --fail --silent localhost:2380/health || exit 1' \
    --health-interval '30s' \
    --health-retries '1' \
    --health-start-period '15s' \
    --health-timeout '5s' \
    --memory '128m' \
    --memory-swap '-1' \
    --name 'swarm-janitor' \
    --publish '2380:2380' \
    --restart 'always' \
    --volume /var/run/docker.sock:/var/run/docker.sock \
    swarm-janitor:latest
~~~~


## Developer setup

Setup the project using Pipenv.
~~~~
$ pipenv --python 3.8
$ pipenv install --dev
~~~~

Run the automated tests and generate the coverage report.
~~~~
$ pipenv run pytest --junitxml=junit/test-results.xml --cov=. --cov-report=xml --cov-report=html
~~~~

Run the application from source.
~~~~
$ export AWS_ACCESS_KEY_ID=********************
$ export AWS_SECRET_ACCESS_KEY=****************************************
$ export AWS_DEFAULT_REGION=eu-west-1
$ export SWARM_REGISTRY=************.dkr.ecr.eu-west-1.amazonaws.com
$ export SWARM_DESIRED_ROLE=worker
$ export SWARM_MANAGER_NAME_FILTER=foo-bar-manager
$ export SWARM_INTERVAL_PRUNE_SYSTEM=300
$ export SWARM_INTERVAL_REFRESH_AUTH=300
$ export SWARM_PRUNE_IMAGES=false
$ export SWARM_PRUNE_VOLUMES=false
$ pipenv run ./swarm-janitor.py
~~~~

Build the Docker image.
~~~~
$ docker build --tag swarm-janitor:latest .
~~~~

Build the stand-alone executable.
~~~~
$ pipenv run pyinstaller \
    --paths "$(pipenv --venv)" \
    --clean \
    --onefile \
    swarm-janitor.py
~~~~

Afterwards, clean up.
~~~~
$ rm -rf \
    .coverage \
    .pytest_cache \
    build/ \
    coverage.xml \
    dist/ \
    htmlcov/ \
    junit/ \
    swarm-janitor.spec
~~~~
