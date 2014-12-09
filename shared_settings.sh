#!/bin/bash

export BU_SCRIPT_DIR="${PROJECT_ROOT}/build_tool/bu.scripts"
export JAR_SEARCH_PATH="${HOME}/.moolcache/jars"
export JAVA_DEFAULT_VERSION="1.7"
export PEP8_BINARY="${PEP8_PATH} --max-line-length=80 --ignore=E111"
export PYLINT_RC_FILE="${BU_SCRIPT_DIR}/pylint.rc"
export SCALA_DEFAULT_VERSION="2.8"

init_working_dirs() {
  BUILD_ROOT_MOD=$(echo ${BUILD_ROOT} | sed "s|/|_|g")
  export BUILD_OUT_DIR="/tmp/mool.temp/${BUILD_ROOT_MOD}/outdir"
  export BUILD_WORK_DIR="/tmp/mool.temp/${BUILD_ROOT_MOD}/workdir"

  echo '${BUILD_OUT_DIR}='"${BUILD_OUT_DIR}"
  echo '${BUILD_WORK_DIR}='"${BUILD_WORK_DIR}"
}
