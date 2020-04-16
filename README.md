# Docker Swarm Janitor (for deployments on Amazon Web Services (AWS) EC2 auto-scaling groups)


## Usage

~~~~
# In production environments, use an instance profile instead of these environment variables.
$ export AWS_ACCESS_KEY_ID='********************'
$ export AWS_SECRET_ACCESS_KEY='****************************************'

# Configure the application.
$ export AWS_DEFAULT_REGION='eu-west-1'
$ export SWARM_REGISTRY='000000000000.dkr.ecr.eu-west-1.amazonaws.com'
$ export SWARM_INTERVAL_PRUNE_SYSTEM='10'
$ export SWARM_INTERVAL_REFRESH_AUTH='10'
$ export SWARM_PRUNE_IMAGES='true'
$ export SWARM_PRUNE_VOLUMES='true'

# Run the application
$ pipenv run ./swarm-janitor.py
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
