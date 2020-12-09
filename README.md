# Docker Swarm Janitor for Amazon Web Services (AWS)

Docker Swarm Janitor executes maintenance tasks for your Docker Swarm cluster which
* is deployed on Amazon EC2 auto-scaling groups (one for the manager nodes and one for the worker nodes),
* is using Amazon ECR as private Docker registry.


## Features

Docker Swarm Janitor is one light-weight daemon process deployed as some Docker image (see below) which
* executes `docker system prune --force [--all] [--volumes]` at the configured rate,
* executes `docker login` (into your ECR) and `docker service update --with-registry-auth` at the configured rate.
* lets nodes (spawned by your ASG) join the cluster automatically and prune dead nodes from the swarm.


## Usage

Include this command in your user data script:
~~~~
$ docker run \
  --env "AWS_DEFAULT_REGION=eu-west-1" \
  --env "SWARM_NODE_AZ=$(ec2metadata --availability-zone)" \
  --env "SWARM_REGISTRY=000000000000.dkr.ecr.eu-west-1.amazonaws.com" \
  --env "SWARM_DESIRED_ROLE=worker" \
  --env "SWARM_MANAGER_NAME_FILTER=foo-bar-manager" \
  --env "SWARM_INTERVAL_ASSUME_ROLE=50" \
  --env "SWARM_INTERVAL_LABEL_AZ=40" \
  --env "SWARM_INTERVAL_PRUNE_NODES=30" \
  --env "SWARM_INTERVAL_PRUNE_SYSTEM=86400" \
  --env "SWARM_INTERVAL_REFRESH_AUTH=3600" \
  --env "SWARM_PRUNE_IMAGES=true" \
  --env "SWARM_PRUNE_VOLUMES=true" \
  --detach \
  --health-cmd 'curl --fail --silent localhost:2380/health || exit 1' \
  --health-interval '60s' \
  --health-retries '1' \
  --health-start-period '10s' \
  --health-timeout '2s' \
  --memory '128m' \
  --memory-swap '-1' \
  --name 'swarm-janitor' \
  --network 'host' \
  --restart 'always' \
  --volume /var/run/docker.sock:/var/run/docker.sock \
  arvacims/swarm-janitor:1.2.2
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
$ export AWS_DEFAULT_REGION=eu-west-1
$ export SWARM_NODE_AZ=eu-west-1a
$ export SWARM_REGISTRY=000000000000.dkr.ecr.eu-west-1.amazonaws.com
$ export SWARM_DESIRED_ROLE=worker
$ export SWARM_MANAGER_NAME_FILTER=foo-bar-manager
$ export SWARM_INTERVAL_ASSUME_ROLE=50
$ export SWARM_INTERVAL_LABEL_AZ=40
$ export SWARM_INTERVAL_PRUNE_NODES=30
$ export SWARM_INTERVAL_PRUNE_SYSTEM=120
$ export SWARM_INTERVAL_REFRESH_AUTH=90
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
