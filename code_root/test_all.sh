#!/bin/bash
# Some common code that we found useful at Rocket Fuel.
set -e
set -o pipefail

# Initialize local machine specific environment variables.
source ${PROJECT_ROOT}/local_settings.sh

# Initialize shared settings.
source ${PROJECT_ROOT}/shared_settings.sh

# Rocket Fuel python code uses 4 spaces for indentation unlike mool, which
# uses 2 spaces for indentation. This can be cleaned up in a future release.
export PYLINT_RC_FILE=${PROJECT_ROOT}/build_tool/mool_test_drivers/pylint.rc

# Initialize parameters for current codebase.
export BUILD_ROOT="${PROJECT_ROOT}/code_root"
init_working_dirs

cd ${BUILD_ROOT}
${BU_SCRIPT_DIR}/bu do_clean
${BU_SCRIPT_DIR}/bu do_test mool.common.utils.ALL
