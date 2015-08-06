"""This file has list of various build rules to be tested."""

SKIPPED_BUILD_COUNT = 107

# Regression tests.
REG_BUILD_RULES = [
    'mool.jroot.src.main.java.some.work.DriverFromMavenSpec',
    'mool.jroot.src.main.java.some.work.DriverWithReducedDeps',
    'mool.jroot.src.main.java.some.work.DriverFromDriverLibWithMissingDeps']

REG_PATTERN_TESTS = [
    (3, '.class', 'jroot/src/main/java/some/other/work/HelloWorld.jar'),
    (3, '.class',
     'jroot/src/main/java/some/work/DriverLibWithMissingDeps.jar'),
    (7, '.class',
     'jroot/src/main/java/some/work/DriverFromDriverLibWithMissingDeps.jar'),
    (4, 'apache', 'jroot/src/main/java/some/work/StrippedCommonLang.jar'),
    (4, 'apache', 'jroot/src/main/java/some/work/DriverWithReducedDeps.jar'),
    (157, '.class', 'jroot/src/main/java/some/work/DriverFromMavenSpec.jar')]

# All build rules and tests.
BUILD_RULES = [
    'mool.ccroot.common.ALL',
    'mool.ccroot.samples.ALL',
    'mool.ccroot.thrift.ALL',
    'mool.jroot.org.personal.compileDeps.DummyLogger',
    'mool.jroot.org.personal.firstlib.ALL',
    'mool.jroot.org.personal.jarMerger.SameClassRepeated',
    'mool.jroot.org.personal.jarMerger.service.ServiceLoaderDemo',
    'mool.jroot.org.personal.secondlib.ALL',
    'mool.jroot.src.main.java.some.other.work.HelloWorld',
    'mool.jroot.src.main.java.some.other.work.ApacheCommonsLang',
    'mool.jroot.src.main.java.some.work.ApacheCommonsLangSubset',
    'mool.jroot.src.main.java.some.work.BinWithNoDependencies',
    'mool.jroot.src.main.java.some.work.Driver',
    'mool.jroot.src.main.java.some.work.DriverFromDriverLibWithMissingDeps',
    'mool.jroot.src.main.java.some.work.DriverFromMavenSpec',
    'mool.jroot.src.main.java.some.work.DriverWithReducedDeps',
    'mool.jroot.src.main.java.some.work.ProtoSampleMain',
    'mool.jroot.src.main.java.some.work.complete_package',
    'mool.jroot.src.test.java.some.other.work.HelloWorldTest',
    'mool.jroot.src.test.java.some.other.work.MultipleTestClasses',
    'mool.jroot.src.test.java.some.work.DriverTest',
    'mool.jroot.src.test.java.some.work.DriverTestIntegration',
    'mool.jroot.src.test.java.some.work.ResourceAccessibleTest',
    'mool.pyroot.first_service.first_module.address_py_proto',
    'mool.pyroot.first_service.first_module.first_main',
    'mool.pyroot.first_service.first_module.java_dependency_pybin',
    'mool.pyroot.first_service.first_module.main_lib',
    'mool.pyroot.first_service.first_module.main_lib_test',
    'mool.pyroot.second_service.another_module.another_lib',
    'mool.pyroot.second_service.another_module.another_lib_test',
    'mool.pyroot.second_service.another_module.person_main',
    'mool.pyroot.second_service.another_module.person_main_from_proto_nodeps',
    'mool.pyroot.second_service.another_module.person_py_proto',
    'mool.pyroot.second_service.another_module.second_main',
    'mool.pyroot.second_service.another_module.second_service_package',
    'mool.scalaroot.com.failLib.SameVersion',
    'mool.scalaroot.com.failLib.ScalaLib_2_11',
    'mool.scalaroot.com.failLib.ScalaLib_2_8',
    'mool.scalaroot.com.testOne.ALL',
    'mool.scalaroot.com.testTwo.ALL']

BUILD_TESTS = [
    'mool.ccroot.common.ALL',
    'mool.ccroot.samples.ALL',
    'mool.jroot.org.personal.compileDeps.TestDummyLogger',
    'mool.jroot.org.personal.secondlib.SecondMainTest',
    'mool.jroot.org.personal.secondlib.SecondMainTest',
    'mool.pyroot.first_service.first_module.ALL',
    'mool.pyroot.second_service.another_module.ALL',
    'mool.scalaroot.com.testOne.ScalaTest',
    'mool.scalaroot.com.testOne.ScalaTest2_11',
    'mool.scalaroot.com.testTwo.AnotherTest']

FILE_COUNT_TESTS = [
    (8, 'jroot/src/main/java/some/work/some_resource_files.jar'),
    (7, 'jroot/src/main/java/some/work/BinWithNoDependencies.jar'),
    (184, 'jroot/src/main/java/some/work/Driver.jar'),
    (23,
     'jroot/src/main/java/some/work/DriverFromDriverLibWithMissingDeps.jar'),
    (184, 'jroot/src/main/java/some/work/DriverFromMavenSpec.jar'),
    (23, 'jroot/src/main/java/some/work/DriverWithReducedDeps.jar'),
    (269, 'jroot/src/main/java/some/work/ProtoSampleMain.jar'),
    (8, 'jroot/src/main/java/some/other/work/HelloWorld.jar'),
    (267, 'jroot/src/main/java/some/other/work/ProtoSampleUtils.jar'),
    (175, 'jroot/src/main/java/some/work/ApacheCommonsCommonLang.jar'),
    (7, 'jroot/src/main/java/some/work/DriverLibWithMissingDeps.jar'),
    (7, 'jroot/src/main/java/some/work/StrippedCommonLang.jar'),
    (6, 'jroot/src/test/java/some/other/work/HelloWorldTest.jar'),
    (5, 'jroot/src/test/java/some/work/DriverTest.jar'),
    (5, 'jroot/src/test/java/some/work/DriverTestIntegration.jar'),
    (2, 'jroot/src/main/java/some/work/complete_package.zip'),
    (6, 'jroot/org/personal/firstlib/prod_files.jar'),
    (7, 'jroot/org/personal/firstlib/test_files.jar'),
    (7, 'jroot/org/personal/firstlib/Main.jar'),
    (9, 'jroot/org/personal/secondlib/SecondMain.jar'),
    (7, 'jroot/org/personal/firstlib/MainLib.jar'),
    (9, 'jroot/org/personal/secondlib/SecondMainLib.jar'),
    (6, 'jroot/org/personal/firstlib/MainTest.jar'),
    (6, 'jroot/org/personal/secondlib/SecondMainTest.jar'),
    (8092, 'jroot/org/personal/secondlib/StormCore.jar'),
    (14, 'jroot/org/personal/jarMerger/service/ServiceLoaderDemo.jar')]

PATTERN_TESTS = [
    (1, '.txt', 'jroot/org/personal/firstlib/MainLib.jar'),
    (1, '.txt', 'jroot/org/personal/firstlib/Main.jar'),
    (2, '.txt', 'jroot/org/personal/firstlib/zip_archive.zip'),
    (3, '.class', 'jroot/org/personal/compileDeps/DummyLogger.jar'),
    (11, '.class',
     'jroot/src/main/java/some/work/ApacheCommonsLangSubset.jar'),
    (6, '.py', 'pyroot/first_service/first_module/first_main'),
    (5, '.py', 'pyroot/first_service/first_module/main_lib'),
    (7, '.py', 'pyroot/first_service/first_module/main_lib_test'),
    (8, '.py', 'pyroot/second_service/another_module/another_lib'),
    (9, '.py', 'pyroot/second_service/another_module/second_main'),
    (10, '.py', 'pyroot/second_service/another_module/another_lib_test'),
    (4, '.py', 'pyroot/first_service/first_module/address_py_proto'),
    (29, '.py', 'pyroot/second_service/another_module/person_py_proto'),
    (34, '.py', 'pyroot/second_service/another_module/person_main'),
    (4, '.py', 'pyroot/second_service/another_module/person_py_proto_nodeps'),
    (34, '.py',
     'pyroot/second_service/another_module/person_main_from_proto_nodeps'),
    (1, 'first_module',
     'pyroot/second_service/another_module/second_service_package.zip'),
    (3, 'another_module',
     'pyroot/second_service/another_module/second_service_package.zip'),
    (3, '.txt',
     'pyroot/second_service/another_module/second_service_package.zip'),
    (5, '.pyc', 'pyroot/first_service/first_module/first_main'),
    (8, '.pyc', 'pyroot/second_service/another_module/second_main'),
    (33, '.pyc', 'pyroot/second_service/another_module/person_main'),
    (33, '.pyc',
     'pyroot/second_service/another_module/person_main_from_proto_nodeps')]

# TODO: Modify it to accept any command to run with support for substituting
# env variables, pattern serach in output and overall pass/fail of binary
# execution. Merge the VALIDATE_BINARY_OUTPUT section with this.

# Format of the command is (<Executable to run>, [command line options]).
# .jar files are explicitly run using java.
EXECUTABLES_TO_RUN = [
    ('ccroot/samples/factorial_main'),
    ('ccroot/samples/person_proto_main'),
    ('ccroot/samples/person_proto_main_indirect'),
    ('ccroot/thrift/demo_client'),
    ('ccroot/thrift/demo_client_indirect'),
    ('jroot/src/main/java/some/work/Driver.jar', ['-Xms6m', '-Xmx80m']),
    ('jroot/src/main/java/some/work/DriverWithReducedDeps.jar',
     ['-Xms6m', '-Xmx80m']),
    ('jroot/src/main/java/some/work/DriverFromDriverLibWithMissingDeps.jar'),
    ('jroot/src/main/java/some/work/DriverFromMavenSpec.jar'),
    ('jroot/src/main/java/some/work/BinWithNoDependencies.jar',
     ['-Xms6m', '-Xmx80m']),
    ('jroot/src/main/java/some/work/ProtoSampleMain.jar',
     ['-Xms6m', '-Xmx80m']),
    ('jroot/org/personal/firstlib/Main.jar', ['-Xms6m', '-Xmx80m']),
    ('jroot/org/personal/secondlib/SecondMain.jar', ['-Xms6m', '-Xmx80m']),
    ('jroot/org/personal/jarMerger/service/ServiceLoaderDemo.jar'),
    ('pyroot/first_service/first_module/first_main'),
    ('pyroot/first_service/first_module/java_dependency_pybin'),
    ('pyroot/second_service/another_module/second_main'),
    ('pyroot/second_service/another_module/person_main'),
    ('pyroot/second_service/another_module/person_main_from_proto_nodeps'),
    ('scalaroot/com/testOne/MainWithScalaCore.jar', ['-Xms6m', '-Xmx80m']),
    ('scalaroot/com/testOne/ScalaDepInJavaBin.jar', ['-Xms6m', '-Xmx80m'])]

# File collection tests. These must be run after building all rules.
# Format is ('Common File', [list of jars which should contain the file]).
FILE_COLLECTION_TESTS = [
    ('src/main/java/some/work/some_resource.txt',
     ['jroot/src/main/java/some/work/Driver.jar',
      'jroot/src/main/java/some/work/DriverWithReducedDeps.jar',
      'jroot/src/main/java/some/work/DriverFromDriverLibWithMissingDeps.jar',
      'jroot/src/main/java/some/work/DriverFromMavenSpec.jar']),
    ('org/personal/firstlib/prod_data00.txt',
     ['jroot/org/personal/firstlib/MainLib.jar',
      'jroot/org/personal/firstlib/Main.jar',
      'jroot/org/personal/firstlib/prod_and_test_files.jar',
      'jroot/org/personal/secondlib/SecondMainLib.jar',
      'jroot/org/personal/secondlib/SecondMain.jar']),
    ('org/personal/firstlib/test_data01.txt',
     ['jroot/org/personal/firstlib/prod_and_test_files.jar']),
    ('org/personal/firstlib/test_data02.txt',
     ['jroot/org/personal/firstlib/prod_and_test_files.jar']),
    ('pyroot/first_service/first_module/first_main',
     ['pyroot/second_service/another_module/second_service_package.zip']),
    ('pyroot/second_service/another_module/person_main',
     ['pyroot/second_service/another_module/second_service_package.zip']),
    ('pyroot/second_service/another_module/person_main_from_proto_nodeps',
     ['pyroot/second_service/another_module/second_service_package.zip']),
    ('pyroot/second_service/another_module/second_main',
     ['pyroot/second_service/another_module/second_service_package.zip'])]

# SUBMITQ tests.
# Format is ([list of effected SUBMITQ file path], [list of changed files]).
SUBMITQ_TESTS = [
    (['mool.jroot.org.personal.firstlib.MainTest',
      'mool.jroot.src.main.java.some.other.work.LIGHTRULES',
      'mool.jroot.src.test.java.some.other.work.HelloWorldTest'],
     ['jroot/src/main/java/some/other/work/any_file']),
    (['mool.jroot.src.test.java.some.work.DriverTest',
      'mool.jroot.src.main.java.some.other.work.LIGHTRULES',
      'mool.jroot.src.main.java.some.work.LIGHTRULES',
      'mool.jroot.src.test.java.some.other.work.HelloWorldTest',
      'mool.jroot.org.personal.firstlib.MainTest'],
     ['jroot/src/main/java/some/other/work/any_file',
      'jroot/src/main/java/some/work/another_file',
      'jroot/src/main/java/some/work/another_file'])]

# Validate tests output.
VALIDATE_BINARY_OUTPUT = [
    ('ccroot/common/hello_gcc', ['Detected gcc.']),
    ('pyroot/first_service/first_module/main_lib_test',
     ['2 passed in', 'collected 2 items', 'e2e_test.py ..']),
    ('pyroot/first_service/first_module/first_main',
     ['1', 'In main function.']),
    ('pyroot/second_service/another_module/second_main',
     ['42', '23', 'In second module main function.']),
    ('pyroot/second_service/another_module/another_lib_test',
     ['3 passed in', 'collected 3 items', 'another_class_test.py ...']),
    ('pyroot/second_service/another_module/person_main',
     ['100 Pleasant Dr', 'John Doe (Python)']),
    ('pyroot/second_service/another_module/person_main_from_proto_nodeps',
     ['100 Pleasant Dr', 'John Doe (Python)'])]

# Set of build rules which should fail and output given patterns in stderr.
BUILD_FAIL_TESTS = [('mool.jroot.org.personal.faillib.WrongJavaVersionDep',
                     ['Java version dependency check failed.']),
                    ('mool.aa.bb.ALL',
                     ['Missing rule file: ${BUILD_ROOT}/aa/bb/BLD']),
                    ('mool.jroot.org.personal.faillib.MissingName',
                     ['Rule "MissingName" does not exist in '
                      '${BUILD_ROOT}/jroot/org/personal/faillib/BLD']),
                    ('mool.jroot.org.personal.faillib.NoType',
                     ['Rule "NoType" missing rule_type in '
                      '${BUILD_ROOT}/jroot/org/personal/faillib/BLD']),
                    ('mool.jroot.org.personal.faillib.BadType',
                     ['Unexpected rule type "typo" in '
                      '${BUILD_ROOT}/jroot/org/personal/faillib/BLD']),
                    ('mool.jroot.org.personal.faillib.MissingSource',
                     ['File does not exist: ${BUILD_ROOT}/'
                      'jroot/org/personal/faillib/NotFound.java']),
                    ('mool.jroot.org.personal.faillib.RelativeSource',
                     ['Unexpected separator in source file for: ${BUILD_ROOT}/'
                      'jroot/org/personal/faillib/BLD']),
                    ('mool.jroot.org.personal.faillib.FailingTest',
                     ['java.lang.AssertionError: expected [2] but found [1]']),
                    ('mool.jroot.org.personal.badjson.ALL',
                     ['Invalid JSON in file '
                      '${BUILD_ROOT}/jroot/org/personal/badjson/BLD']),
                    ('mool.jroot.org.personal.faillib.TestDepOfLib',
                     ['Non test rule', 'cannot depend on test rule',
                      'mool.jroot.org.personal.firstlib.MainTest']),
                    ('mool.scalaroot.com.failLib.HigherVersion',
                     ['Scala version dependency check', 'failed']),
                    ('mool.scalaroot.com.failLib.LowerVersion',
                     ['Scala version dependency check', 'failed']),
                    ('mool.jroot.org.personal.jarMerger.SameClassDiffVersion',
                     ['File clash: Mismatching', 'exists in both'])]

# Miscellaneous test data.
# This test tests that rebuild of a rule should depend on actual rule details
# mentioned in BLD file and shouldn't be effected by other parts of BLD file.
BLD_UPDATE_TEST = ('mool.jroot.org.personal.bldChange.ALL',
                   'jroot/org/personal/bldChange/BLD',
                   ('jroot/org/personal/bldChange/bld_version1', 1),
                   ('jroot/org/personal/bldChange/bld_version2', 0),
                   ('jroot/org/personal/bldChange/bld_version3', 1))
