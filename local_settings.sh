#!/bin/bash
# The hard-coded paths in this file should be changed before the build can pass.

export CC_COMPILER='/usr/bin/g++ -Wall'
export PROTOBUF_DIR="/wherever/protobuf-2.4.1"
export PROTO_COMPILER="${PROTOBUF_DIR}/src/protoc"
export JAVA_PROTOBUF_JAR="${PROTOBUF_DIR}/java/target/protobuf-java-2.4.1.jar"
export PYTHON_PROTOBUF_DIR="${PROTOBUF_DIR}/python/build/lib"
export PEP8_PATH="/wherever/pep8"
export SCALA_HOME_2_8="/wherever/scala-2.8.2.final"
export SCALA_HOME_2_11="/wherever/scala-2.11.4"
