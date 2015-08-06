mool: The mool build tool.
==========================

#### What is it?

* It is a collection of scripts that help building code written in C++, Python,
Scala or Java.
* It is very similar to the following tools:

1. [Twitter pants](http://pantsbuild.github.io/)
2. [Facebook buck](http://facebook.github.io/buck/)

The current implementation has been extended from another implementation of
[mooltool](https://github.com/anirban001/mooltool).

#### Installation
Checkout latest code from this repository and run following command from repo
root:
`python2.7 installer/install_mooltool.py`

Above command takes some time and creates a complete working setup in your
current working directory. For more installation options run installer script
with `--help` option.

All the tests should pass at the end of installation!

#### Usage
Once installation is done, you can immediately start using by:

```bash
# Set project root to repository root directory. This is used by shared_settings.
export PROJECT_ROOT=$(git rev-parse --show-toplevel)
# Load all general settings. This also exposes init_working_dirs() function.
source shared_settings.sh
# Load all installation specific or user settings. Check contents of
# local_setting.sh for more details on this.
source local_settings.sh
# Set build root, initialize temporary directories.
export BUILD_ROOT=${PROJECT_ROOT}/code_root
init_working_dirs
# Lets build a rule now.
bu do_test mool.java.com.rocketfuel.ei.common.RpcTest
```
Above steps should work and you can create a handy bash script with above commands.

#### Installation help
It requires following prerequisites:
* Java >= 1.7.0
* Python >= 2.7.3
* g++
* openssl >= 1.0.0

**Environment variables:**
* JAVA_HOME: In case you have more than one JDKs installed or you have java installation in custom path, you can appropriately set *JAVA_HOME* environment variable.
* OPENSSL_INSTALL_PATH: Latest OpenSSL version is required to compiled thrift from source. You can check your current version using `openssl -v`. In case you have openssl installation in custom path, set environment variable *OPENSSL_INSTALL_PATH*.
