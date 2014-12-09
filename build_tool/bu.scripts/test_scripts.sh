#!/usr/bin/env bash

# Ensure exit on first failure.
set -e
set -o pipefail


if [ "${BU_SCRIPT_DIR}" == "" ]; then
    echo 'Error: Environment has not been set up.'
    exit 1
fi

cd ${BU_SCRIPT_DIR}

for FF in $(ls ${BU_SCRIPT_DIR}/*.py); do
  pylint --rcfile=./pylint.rc ${FF} 2>/dev/null
  pep8 --max-line-length=80 --ignore=E111 ${FF}
done

py.test -s .
