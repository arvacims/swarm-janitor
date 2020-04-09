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
