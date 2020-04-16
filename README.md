# Docker Swarm Janitor

Docker Swarm Janitor for deployments on Amazon Web Services (AWS) EC2 auto-scaling groups.


## Usage

In production environments, use an instance profile instead of the access key.
~~~~
$ docker run \
    --env "AWS_ACCESS_KEY_ID=********************" \
    --env "AWS_SECRET_ACCESS_KEY=****************************************" \
    --env "AWS_DEFAULT_REGION=eu-west-1" \
    --env "SWARM_REGISTRY=************.dkr.ecr.eu-west-1.amazonaws.com" \
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
$ export SWARM_INTERVAL_PRUNE_SYSTEM=10
$ export SWARM_INTERVAL_REFRESH_AUTH=10
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
