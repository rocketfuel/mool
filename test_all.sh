#!/bin/bash

set -e
set -o pipefail

export PROJECT_ROOT=$(git rev-parse --show-toplevel)
if [ "${PROJECT_ROOT}" = "" ]; then
  echo "Configuration error."
  exit 1
fi

${PROJECT_ROOT}/build_tool/mool_test_drivers/test_all.sh
${PROJECT_ROOT}/code_root/test_all.sh
echo 'Done!'
