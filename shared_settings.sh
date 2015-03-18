#!/bin/bash

# NOTE: For most purposes you need not touch this file.

export BU_SCRIPT_DIR="${PROJECT_ROOT}/build_tool/bu.scripts"
export PEP8_BINARY="pep8 --max-line-length=80 --ignore=E111"
export PYLINT_RC_FILE="${BU_SCRIPT_DIR}/pylint.rc"

init_working_dirs() {
  BUILD_ROOT_MOD=$(echo ${BUILD_ROOT} | sed "s|/|_|g")
  export BUILD_OUT_DIR="/tmp/mool.temp/${BUILD_ROOT_MOD}/outdir"
  export BUILD_WORK_DIR="/tmp/mool.temp/${BUILD_ROOT_MOD}/workdir"

  echo '${BUILD_OUT_DIR}='"${BUILD_OUT_DIR}"
  echo '${BUILD_WORK_DIR}='"${BUILD_WORK_DIR}"
}
