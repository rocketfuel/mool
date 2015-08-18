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

Environment variables useful for installation:
- **JAVA_HOME**: In case you have more than one JDKs installed or you have java
installation in custom path, you can appropriately set _JAVA_HOME_ environment
variable.

- **OPENSSL_INSTALL_PATH**: Latest OpenSSL version is required to compile thrift
from source. You can check your current version using `openssl -v`. In case you
have openssl installation in custom path, set environment variable
_OPENSSL_INSTALL_PATH_ which is picked up by install script.

---
# Documentation

### Key concepts:
- **BUILD_ROOT**:  Top level directory of your project or repository. Rules can
refer to other build rules only within the BUILD_ROOT. It is often recommended
to create all projects within a single BUILD_ROOT so that all the projects can
share code.

- **BLD** file: Build rules are kept in BLD files and you can have a BLD file
in any directory inside BUILD_ROOT except the BUILD_ROOT directory itself.

- **build rule**: A json dictionary which specifies how to build a given set of
source files. Each build rule has a rule name.

- **BU_SCRIPT_DIR**: All mool scripts (python code) are located in
[this](build_tool/bu.scripts) directory. `bu` command is an alias to
[bu](build_tool/bu.scripts/bu) script (bash) inside `BU_SCRIPT_DIR` directory.

- **BUILD_WORK_DIR**:  Each rule uses a dedicated working directory for all rule
building purposes. It creates a directory at
`${BUILD_WORK_DIR}/path/to/rule/rule_name` path for each rule before building
it.

- **BUILD_OUT_DIR**: Final output of all build rules goes in this directory. We
usually create symbolic links from appropriate path in BUILD_WORK_DIR to this
directory. Each rule's output goes in rule specific directory at
`${BUILD_OUT_DIR}/path/to/rule/rule_name` path.

- **SUBMITQ**: Each directory inside build root can have a file named
[`SUBMITQ`](build_tool/mool_tests/jroot/src/main/java/some/other/work/SUBMITQ)
which has a list of rules (separated by new line) to be built when anything
inside that directory is changed. `bu do_test_changes <path_to_change_list>`
command goes through the list of changed files and then picks up `SUBMITQ` file
from _all the directories in the path to changed file_.

### General Rule Format
BLD file format is mostly _JSON_ with _comments_. Each rule has a `rule_name`
which hold a dictionary of key/value pairs. Most rules have following skelton:
```python
"rule_name": {
    "rule_type": <java_lib/cc_bin/...>
    "srcs": [List of sources],
    "deps": [List of dependencies]
}
```

#### Supported Rule types:
- **c++**: `cc_lib`, `cc_bin`, `cc_test`
- **java**: `java_lib`, `java_bin`, `java_test`
- **python**: `py_lib`, `py_bin`, `py_test`
- **scala**: `scala_lib`, `scala_bin`, `scala_test`
- **clojure**: `clojure_lib`, `clojure_bin`, `clojure_test`
- **protobuf**: `cc_proto_lib`, `java_proto_lib`, `py_proto_lib`
- **thrift**: `cc_thrift_lib`, `java_thrift_lib`, `py_thrift_lib`
- **packaging**: `file_coll`, `release_package`

#### Dependency path:
You can specify dependencies on other rules and mool builds all rule
dependencies before building given rule. Dependencies can have a full path,
which is of the format `mool.path.to.bld.file.RuleName` or it can be a relative
path w.r.t given BLD file.

Examples:
* "mool.java.com.example.project.MyPrototype" refers to a rule named
`MyPrototype` described in file at path `${BUILD_ROOT}/java/com/example/project/BLD`.
* ".Slf4jApi" refers to build rule in same BLD file. Notice the **'.'** in the
beginning.
* ".resources.TestResources" refers to a build rule in file
`<current_directory>/resources/BLD` with name `TestResources`.

---

### 1. Java Build Rules.
Each `java_lib` and `java_bin` rule produces one out file (.jar) which is named
after `rule_name`.
```python
# Libraries.
"HelloWorld": {
    "rule_type": "java_lib",
    "srcs": ["HelloWorld.java"]
},

"StringMatcher": {
    "rule_type": "java_lib",
    "srcs": ["JavaStringMatcher.java"],
    "compileDeps": [".ApacheCommonStripped"]
},

"CommonsLang3": {
    "rule_type": "java_lib",
    "maven_specs": {
        "repo_url": "http://repo1.maven.org/maven2",
        "group_id": "org.apache.commons",
        "artifact_id": "commons-lang3",
        "version": "3.0"
        #"classifier": "some classifier"
    }
},

"ApacheCommmonStripped": {
    "rule_type": "java_lib",
    "deps": [
        # Refer to other rules in this file using relative path.
        ".CommonsLang3"
    ],
    "jar_include_paths": [
        "org/apache/commons/lang3/StringUtils.class"
    ]
},

# Binaries.
"HelloWorldRunnable": {
    "rule_type": "java_bin",
    "srcs": ["HelloWorld.java"],
    "main_class": "com.example.HelloWorld"
},

"HelloWorldUsingDep": {
    "rule_type": "java_bin",
    "deps": [".HelloWorld"],
    "main_class": "com.example.HelloWorld"
},

# Tests.
"HelloCheck": {
    "rule_type": "java_test",
    "srcs": ["TestHelloWorld.java"],
    "deps": [
        ".HelloWorld",
        # Add TestNg and JCommander libs as mool supports TestNG
        # tests only as of now.
        "mool.java.mvn.org.TestNg",
        "mool.java.mvn.com.buest.JCommander"
    ],
    "test_classes": ["com.example.HelloCheck"],
    # ["unit"] is used by default is none is specified.
    "test_groups": ["my_test_group"]
}

```

#### Details of Java rule keys
- **rule_name**: One of [`java_lib`, `java_bin`, `java_test`]
- **srcs**: Java source files present in the _same directory_ as BLD file
_(list)_
- **deps**: deps used for compiling and packed with final rule output _(list)_
- **compileDeps**: deps used only for compilation _(list)_
- **precompiled_deps**: external deps without a build rule, example:
`/user/home/path/to/jar` or `env.HOME/path/to/jar`. We expand
`env.<variable_name>` by looking up environment variables  _(list)_
- **compile_params**: arguments for javac compiler  _(list)_
- **runtime_params**: arguments for java binary, used for java_test  _(list)_
- **test_groups**: list of [TestNg](http://testng.org/doc/index.html) groups to
run tests on  _(list)_
- ~~**test_class**~~: test class name; _deprecated_ instead use `test_classes`
_(str)_
- **test_classes**: list of classes to be passed to TestNg _(list)_
- **main_class**: main java class for making executable jar _(str)_
- **maven_specs**: maven specifications for referring to thirdparty jars
(artifacts) _(dict)_
  - *repo_url*: artifact repo url
  - *group_id*: artifact group id
  - *artifact_id*: artifact id
  - *version*: artifact version number
  - *classifier*: artifact classifier (**optional**)
- **extract_deps**: list of deps to be extracted in cwd during test execution,
useful for file read/write tests _(list)_
- **jar_include_paths**: list of paths to be included in final jar; for a
directory path, whole directory is included, i.e. `com/example/project1` will
include all the classes which are inside com/example/project1 directory across
all the dependencies and the main sources _(list)_
- **jar_exclude_paths**: list of paths to be excluded, *this is applied before
inclusions*. Usually only one of the inclusion or exclusion rule is sufficient
_(list)_
- **includeDeps**: extra key to specify if "deps" should be packed with final
jar or not, default `False` for `java_test` rule, `True` otherwise _(bool)_
- **java_version**: java version string to be passed to `--source` and
`--target` params of `javac` command. It has to be at least the jdk version you
are using _(str)_

### 2. C++ Build Rules.
`cc_lib` creates a collection of object (.o) files and copies mentioned headers
(.h) files to output directory. `cc_bin` and `cc_test` create single executable
file. We support [GMOCK](https://code.google.com/p/googlemock/) and
[GTEST](https://code.google.com/p/googletest/) for cc tests.

```python
# Libraries.
"hello_world": {
    "rule_type": "cc_lib",
    # Multiple source/header files can be added in one lib rule.
    "srcs": [ "helloworld.cc"],
    "hdrs": [ "helloworld.h"]
},

"hello_gcc": [
    "rule_type": "cc_lib",
    # All source files MUST be of same type '.c' or '.cc'.
    # We use `gcc` if all sources are '.c' files else we use `g++`.
    "srcs": ["hello_gcc.c", "hello_gcc_macros.c"],
    "hdrs": ["hello_gcc.h"]
],

"factorial_lib": {
    "rule_type": "cc_lib",
    "srcs": ["factorial.cc"],
    "hdrs": ["factorial.h"]
},

# Binaries.
"factorial": {
    "rule_type": "cc_bin",
    # You can specify only one cc file for cc_bin/cc_test rules.
    "srcs": ["factorial_main.cc"],
    "deps": [".factorial_lib"],

    # Headers from custom locations can be added here.
    # You can use environment variables as well to keep it portable.
    "incdirs": ["env.BOOST_DIR/include"],

    # Library directories used by `gcc/g++` to search for "sys_deps".
    "libdirs": ["env.BOOST_DIR/lib"],
    "sys_deps": ["-lboost_regex", "-pthread"]
},

# Tests.
"factorial_test": {
    "rule_type": "cc_test",
    "srcs": ["factorial_test.cc"],
    "deps": [".factorial"],
    # We support cc testing using gtest & gmock libraries.
    # Following libs are added by mool by default, added here for demo only.
    "precompiled_deps": ["env.GTEST_MAIN_LIB", "env.GTEST_MOCK_LIB"]
}
```


### 3. Python Build Rules.
`py_lib` compiles and packs all python sources into a zip file, `py_bin`
appends an executable header to _py_lib_ zip and `py_test` creates python
library and runs it using [py.test](http://pytest.org/latest/). All
dependencies of a rule are always packed to create a standalone python library
or binary.

As of now we don't support a direct way to refer to thirdparty python
dependencies but we use python
[virtual environment](https://virtualenv.pypa.io/en/latest/) for running all
mool commands so one can simply install the required dependencies using
`pip install <dep_name==version>` command. Even better maintain a
`requirements.txt` file and just use `pip install -r path/to/requirements.txt`
to install all dependencies from requirements file.

Mool also does [pylint](http://www.pylint.org/) and
[pep8](https://pypi.python.org/pypi/pep8) checking for you for all python rules
by default!

```python
# Libraries.
"hello_world_utils": {
    "rule_type": "py_lib",
    "srcs": ["hello_world_utils.py"]
},

"json_linter": {
    "rule_type": "py_lib",
    "srcs": ["json_linter.py"],
    # You can get thirdparty deps which are not in mool env
    # packed with final lib using this key.
    "precompiled_deps": ["/Path/to/pysimplejson/module"]
},

# Binaries.
"hello_world": {
    "rule_type": "py_bin",
    "srcs": ["hello_world_main.py"],
    "deps": [".hello_world_utils"],
    # Path to main module is always w.r.t. BUILD_ROOT.
    # NOTICE that it uses file name 'hello_world_main' and then
    # the main function 'main_func' inside it.
    "main_method": "my.first_package.hello_world_main.main_func"
}

# Tests.
"simple_test": {
    "rule_type": "py_test",
    "srcs": ["simple_py_test.py"],
    "deps": [".hello_world_utils"]
}
```
Other keys:
- **py_skiplint**: "true" or "false". It can be used to disable lint checking.


### 4. Scala Build Rules.
Scala build rules are mostly same as java build rules except that the rule
names are different. We use [scalatest](http://www.scalatest.org/) to run scala
tests. Mool supports multiple versions of `scala` and one can specify the
desired scala version using `scala_version` key. There must be an environment
variable `SCALA_HOME_[VERSION]` ('.' replace with '_' in version number) for
the version you mention in scala rule i.e. `SCALA_HOME_2_10` should be set if
you are specifying "2.10" in a build rule.

Also `SCALA_DEFAULT_VERSION` should be set to the default version for example
"2.11". Mool installer sets up scala 2.8(default), 2.10, 2.11 for you.

### 5. Clojure Build Rules.
Clojure supports two [modes of compilation](http://clojure.org/compilation):
- **AOT** (Ahead Of Time): Scala source file is compiled and packed into final
jar.
- **Direct**: Sources are not compiled instead packed directly into the final
jar.

Since clojure compiler generates a _class_ file for each function, each clojure
(`clj`) source ends up generating large number of class files (clojure being a
functional programming language adds to this count). By default the non-AOT
sources are also compiled and checked for any compilation errors but
_developers_ can set `BUILD_CLOJURE_NONAOT` to `true` to skip compilation of
non-AOT sources and keep the builds faster.

**Note:** Clojure being java interop, it's build rules support most features
supported by java build rules. In fact mool drives clojure and scala rule
handling classes from java rule handler class ;)

```python
# Libraries.
"HelloWorld": {
    "rule_type": "clojure_lib",
    "srcs": ["hello_world.clj"],
    # By default sources are packed to jar as such. One can
    # specify the list of namespaces to be AOT compiled.
    "clojure_aot_ns": ["com.example.hello-world"]
},

"CompileAll": {
    "rule_type": "clojure_lib",
    "srcs": ["example_lib_one.clj", "example_lib_two.clj"],
    # Simply set ":all" to compile all namespaces and not
    # specifying it will pack the sources without compilation.
    "clojure_aot_ns": ":all",
    "clojure_version": "1.7"
},

# Binaries.
"MyExecutable": {
    "rule_type": "clojure_bin",
    "srcs": ["echo_name.clj"],
    "main_class": "com.example.EchoName",
    # Optionally pack clojure core classes in final jar to
    # make a standalone binary rather than adding it on classpath.
    "include_clojure_core": "True"
}

# Tests.
"FirstTest": {
    "rule_type": "clojure_test",
    "srcs": ["hello_test.clj"],
    "deps": [".HelloWorld"],
    "clojure_test_ns": ["com.example.HelloTest"]
}
```

### 6. Protobuf Build Rules.
Google [protobuf](https://developers.google.com/protocol-buffers/) is famous
message exchange format, well known for its efficiency and wide use. Given a
`.proto` file, mool compiles it using `protoc` compiler and creates a library
for use with C++/Java/Python code.

```python
# Proto rules for creating a cc library (.o + .h) files.
"address_cc": {
    # You can specify only one proto file in one rule.
    "rule_type": "cc_proto_lib",
    "srcs": ["address.proto"]
},

"person_cc": {
    "rule_type": "cc_proto_lib",
    "srcs": ["person.proto"],
    # Add dependencies to other proto files.
    "deps": [".address_cc"]
}

# Java proto rules create a jar.
"KeyValueService": {
    "rule_type": "java_proto_lib",
    "srcs": ["key_value_service.proto"]
},

"ServiceMain": {
    "rule_type": "java_bin",
    "srcs": ["ServiceMain.java"],
    # Add proto dependency to use it with java/cc/py rules.
    "deps": [".KeyValueService"],
    "main_class": "com.example.ServiceMain"
}

# Python proto rules create a py lib.
"key_store_service": {
    "rule_type": "py_proto_lib",
    "srcs": ["key_store.proto"],
    # Mool doesn't pack google protobuf python libraries in
    # the final lib by default. You can request to do so.
    "precompiled_deps": ["env.PYTHON_PROTOBUF_DIR"]
}
```
For `cc_proto_lib` rule, _protoc_ compiler generates _single_ cc file
(`.pb.cc`) and single header file (`.pb.h`) and the generated cc file is
compiled to generate an object file.

### 7. Thrift Build Rules.
Apache [thrift](https://thrift.apache.org/) is another famous message exchange
protocol. Given a `.thrift`  file, it uses _thrift_ compiler to generate a
C++/Java/Python library. Its rules are analogous to proto rules naming
`cc_thrift_lib`, `java_thrift_lib` and `py_thrift_lib`.

Note that for one `.thrift` file, _thrift_ compiler usually generates
_multiple_ cc sources which result in multiple '.o' files.

### 8. Packaging Build Rules.
There are two packaging rules, `file_coll` for creating a _jar_ file of raw
resource files and `release_package` for packaging output of different types of
build rules into one package. For instance, you can create a final _zip_ file
with some bash scripts and python binaries using `release_package` rule.

```python
# Create a jar file with given srcs at given file package
# path w.r.t root of jar file.
"config_files": {
    "rule_type": "file_coll",
    "srcs": ["server_config.cfg", "client_config.cfg"],
    # You can use "." to package them at root of jar file.
    "file_package": "org/example/config"
}

"ServerInstance": {
    "rule_type": "java_bin",
    # Use the config files with other build rules.
    "deps": [".ServerMain", ".config_files"],
    "main_class": "com.example.ServerMain"
}

# Package using out files of different build rules.
"complete_package": {
    "rule_type": "release_package",
    "package_modules": [
        "mool.project.module1.Server",
        "mool.project.module2.Client"],
    "package_tests": [
        "mool.project.module1.ServerTests",
        "mool.project.module2.ClientTests",
        "mool.project.combined.AllTests"]
}
```
For `release_package` rule, all build rules in `package_modules` are built and
all the test rules in `package_tests` are tested which _MUST_ pass for the
`release_package` rule to pass and create one final archive file.

Other Keys:
- **archive_type**:  Valid only for `file_coll` rule, possible value are "zip"
or "jar" with default as "jar".
- **extract_in_zip**: List of rules _from_ `package_module` keys to be
extracted before creating final zip. For instance one may want to unzip a bunch
of bash scripts coming from `file_coll` rule in zip because o/w they are
packaged as a zip/jar file inside release_package rule's final _zip_ file.

---

### Useful Environment variables
Mool is highly driven by environment variables. You need not know details of
all of them but some of the most useful ones are as follows:

- **DEBUG_MODE**: Set this to "true" to run mool in debug mode. It prints
sequence of commands that mool runs for building/testing a rule. It is quite
helpful when you have some unexpected error and you want details of what
commands were actually run the background.

- **DEVELOPER_MODE**: If set to "true", mool does following addition stuff:
 - downloads java maven _source_ jar as well along with main jar.
 - emits detailed warnings when there are multiple versions of a class in java
 test dependencies.

- **BUILD_CLOJURE_NONAOT**: If set to "false", it skips syntax validation
(using compilation, feel free to suggest a better way) of non-AOT clojure
sources. It is recommended NOT to set this on build servers so that unhealthy
code is flagged.

- **CLOJURE_SRCS_ROOT**: Unlike java, clojure compilation and testing requires
_clojure sources_ directory in _classpath_ with the path from that directory to
clojure source matching the [_namespace_](http://clojure.org/namespaces)
definition in the source. This path is _relative to BUILD_ROOT_. For example if
your clojure project namespace starts with 'com.example' and all your clojure
code is in `${BUILD_ROOT}/cljroot` directory, set `CLOJURE_SRCS_ROOT="cljroot"`.

- **MAVEN_PREFER_LOCAL_REPO**: By default mool fetches jars of `java_lib` rules
with maven details from repository specified in rule details. One can set this
variable to a local repository which follows maven structure to try and look
for jar sources locally and try external sources if local fails. For example
setting `MAVEN_PREFER_LOCAL_REPO="${HOME}/.m2/repository"` will instruct mool
to try local `.m2` repository for all the jars it needs.

- **ECLIPSE_WORKSPACE_DIR**: Used by `setup_eclipse_project` extension, it
instructs mool to use specified directory as workspace directory and within
which it creates a directory with requested project name and then creates
_.classpath_ and _.project_ files inside that directory.

There are quite a lot of other environment variables which are core to
functioning of mool. You are **strongly recommended** to use
[mool installer](#installation) which sets all these environment varilables
correctly in _mool_init.sh_ file. Following is the meaning of each of these:

- **BOOST_DIR**: after compilation of boost sources, its _libs_ and _headers_
are moved into this directory
- **CC_COMPILER:** path to g++ compiler to use
- **CC_INSTALL_PREFIX**: libs and headers for _gmock_, _gtest_ and _protobuf_
- **CLOJURE_DEFAULT_VERSION**: default clojure version to use i.e. "1.6"
- **JAR_SEARCH_PATH**: directory path to store all maven downloaded jars. Mool
maintains this jar cache and use it for future builds of that rule.
- **JAVA_COMPILER**: path to `javac` executable
- **JAVA_DEFAULT_VERSION**: default `--source` and `--target` arguments to be
passed to `javac`. We do a strict dependency checking between a build rule and
its dependencies for its _java_version_ key. _A lower java version build rule
cannot depend on higher java version!_
- **JAVA_HOME**: path to java home directory to use. It is assumed that all
java related executables are in `${JAVA_HOME}/bin/` directory.
- **JAVA_PROTOBUF_JAR**: full path to protobuf jar.
- **JAVA_TEST_DEFAULT_JARS**: Add ";" separated list of full paths to jars
which each test should include. i.e. you can add _testng_ and _jcommander_ jars
here instead of specifying them in each test rule.
- **JAVA_THRIFT_JARS**: Full path to thrift jar required for compiling
generated java code. Usually thrift requires `log4j` jar as well so you can add
both the jars (and any other as well) as ";" separated string.
- **PEP8_BINARY**: full path to `pep8` binary to use for lint checking. You can
add other command line parameters as well here i.e.
`/usr/bin/pep8 --max-line-length=80 --ignore=E111`.
- **PROTO_COMPILER**: full path to `protoc` executable
- **PYLINT_RC_FILE**: full path of `pylint` rcfile which has the required lint
configuration.
- **SCALA_DEFAULT_VERSION**: default scala version to use i.e "2.10". Make sure
that you have `SCALA_HOME_X_Y` defined for scala version "x.y" you want to use.
- **SCALA_HOME_X_Y**: Path root directory of scala (similar to java) for each
version separately.
- **SUBMITQ_DEBUG_MODE**: prints list of affected rules from given list of
changed files before building/testing them.
- **THRIFT_COMPILER**: full path to `thrift` executable.
- **THRIFT_DIR**: thrift libs and headers are kept here after compilation of
thrift sources.
- **VALGRIND_PREFIX**: path to [`valgrind`](http://valgrind.org) executable
along with any other command line parameters (except the test binary). This is
used for memory leak testing of cc libs and binaries.

---

> Huge thanks to [StackEdit](https://stackedit.io) without which this
documentation wouldn't have been possible.

Any pull requests are welcomed for bugs, documentation or new features!

We hope you will love using it :)
