#!/bin/bash

############################### IMPORTANT ###############################
# It is required to have correct paths set in this file. These are used
# by mool for building your projects.
#
# If you are an EXPERT, feel free to modify the values assigned here.
#                                   OR
# Don't worry, try installer/install_mooltool.py script and that should
# setup required packages and then this script should work reading these
# values from your installation location (.rfmool/mool_init.sh).
########################################################################

export REPOSITORY_ROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

set_local_misc() {
  export CC_COMPILER='/usr/bin/g++ -Wall'

  export JAVA_DEFAULT_VERSION="1.7"
  export JAR_SEARCH_PATH="${REPOSITORY_ROOT}/.rfmool/jars"
  export JAVA_HOME="/wherever/java_home"

  export SCALA_DEFAULT_VERSION="2.8"
  export SCALA_HOME_2_8="/wherever/scala-2.8.2.final"
  export SCALA_HOME_2_10="/wherever/scala-2.10.4"
  export SCALA_HOME_2_11="/wherever/scala-2.11.4"

  export PROTOBUF_DIR="/wherever/protobuf-2.5.0"
  export PROTO_COMPILER="/wherever/protobuf-2.5.0"
  export JAVA_PROTOBUF_JAR="${PROTOBUF_DIR}/java/target/protobuf-java-2.5.0.jar"
  export PYTHON_PROTOBUF_DIR="${PROTOBUF_DIR}/python/build/lib"
}


if [ -e "${REPOSITORY_ROOT}/.rfmool/moolrc" ]; then
    source ${REPOSITORY_ROOT}/.rfmool/moolrc && mool_init
elif [ -e "${HOME}/.rfmool/moolrc" ]; then
    source ${HOME}/.rfmool/moolrc && mool_init
elif [ -e "${MOOL_INSTALL_LOCATION}/moolrc" ]; then
    source ${MOOL_INSTALL_LOCATION}/moolrc && mool_init
else
    set_local_misc
fi
