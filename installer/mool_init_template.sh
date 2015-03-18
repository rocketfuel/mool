#!/bin/bash
set_misc() {
  export CC_COMPILER='/usr/bin/g++ -Wall'

  export JAVA_DEFAULT_VERSION="1.7"
  export JAVA_HOME="VAR_JAVA_HOME"
  export JAR_SEARCH_PATH="VAR_JAR_SEARCH_PATH"

  export SCALA_DEFAULT_VERSION="VAR_SCALA_DEFAULT_VERSION"
  export SCALA_HOME_2_8="VAR_SCALA_HOME_2_8"
  export SCALA_HOME_2_11="VAR_SCALA_HOME_2_11"

  export PROTO_COMPILER="VAR_PROTO_COMPILER"
  export JAVA_PROTOBUF_JAR="VAR_JAVA_PROTOBUF_JAR"
  export PYTHON_PROTOBUF_DIR="VAR_PYTHON_PROTOBUF_DIR"
}

set_misc
