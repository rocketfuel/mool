#!/bin/bash
# The changes here are Rocket Fuel specific enhancements to the original build
# tool found in https://github.com/anirban001/mooltool.

# This script sets up common paths as environment variables for available
# utilities. Consequently, it makes sense to "source" this script.

set -e
set -o pipefail

# Initialize local machine specific environment variables.
source ${PROJECT_ROOT}/local_settings.sh

# Initialize shared settings.
source ${PROJECT_ROOT}/shared_settings.sh

# Check that the tool is consistent by running its inner unit tests.
${BU_SCRIPT_DIR}/test_scripts.sh

# Run some style checks on the end-to-end test code.
python_style_check() {
  echo "Style check for ${1}"
  pylint --rcfile=${PROJECT_ROOT}/build_tool/mool_test_drivers/pylint.rc \
     ${1} 2>/dev/null
  ${PEP8_BINARY} ${1}
}
cd ${PROJECT_ROOT}/build_tool
python_style_check ./mool_test_drivers/file_utils.py
python_style_check ./mool_test_drivers/tests_config.py
python_style_check ./mool_test_drivers/tests_driver.py

# Setup environment variables needed for running the end-to-end test code.
export BUILD_ROOT="${PROJECT_ROOT}/build_tool/mool_tests"
init_working_dirs
export MOOL_TESTS_LOG_FILE="/tmp/mool.temp/mool_tests_error.log"

function print_error_logs() {
  echo "------------------- ERROR LOGS -----------------------------"
  cat ${MOOL_TESTS_LOG_FILE}
  echo "---------------- MOOL TESTS FAILED -------------------------"
  exit 1
}

cd ${BUILD_ROOT}
${BU_SCRIPT_DIR}/bu do_clean
echo > ${MOOL_TESTS_LOG_FILE}

python2.7 \
    ${PROJECT_ROOT}/build_tool/mool_test_drivers/tests_driver.py \
    || print_error_logs
echo "All e2e tests passed."
