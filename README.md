# How to build

~~~~
$ pipenv --python 3.8

$ pipenv install --dev

$ pipenv run pyinstaller \
    --paths "$(pipenv --venv)" \
    --clean \
    --onefile \
    swarm-janitor.py
~~~~


# How to test

~~~~
$ pipenv run pytest --junitxml=junit/test-results.xml --cov=. --cov-report=xml --cov-report=html
~~~~


# How to use

~~~~
$ export AWS_ACCESS_KEY_ID='********************'
$ export AWS_SECRET_ACCESS_KEY='****************************************'
$ export AWS_DEFAULT_REGION='eu-west-1'
$ export SWARM_REGISTRY='************.dkr.ecr.eu-west-1.amazonaws.com'
$ export SWARM_INTERVAL_PRUNE_SYSTEM='10'
$ export SWARM_INTERVAL_REFRESH_AUTH='10'
$ export SWARM_PRUNE_IMAGES='true'
$ export SWARM_PRUNE_VOLUMES='true'
$ pipenv run ./swarm-janitor.py
~~~~


# How to clean up

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
