"""Script to install mooltool on developer and test machines. We use python
virtual environment based approach for setting up the development environment.

Required packages before the script can be used are:
* Java >= 1.7.0
* python >= 2.7.3
* g++

It is supposed to work on Mac OS, Ubuntu and Centos.
Please visit mool wiki https://github.com/rocketfuel/mool/wiki for help on
installation of prerequisites.
"""
import sys
# Validate minimum python version.
assert (2, 7, 3) <= sys.version_info[:3]

import argparse
import hashlib
import logging
import os
import shlex
import shutil
import subprocess
import time
import urllib


BLOCK_SIZE = 1 << 20

MOOL_AUTOCOMPLETE_SCRIPT = 'mool_autocomplete.sh'

MOOL_INIT_TEMPLATE_FILE = 'mool_init_template.sh'

MOOL_INIT_VARS = (
    'BOOST_DIR', 'CC_INSTALL_PREFIX', 'GTEST_MAIN_LIB', 'GTEST_MOCK_LIB',
    'JAR_SEARCH_PATH', 'JAVA_HOME', 'JAVA_PROTOBUF_JAR', 'PROTO_COMPILER',
    'PYTHON_PROTOBUF_DIR', 'SCALA_DEFAULT_VERSION', 'SCALA_HOME_2_10',
    'SCALA_HOME_2_11', 'SCALA_HOME_2_8', 'THRIFT_DIR')

MOOLRC_TEXT = """
export MOOL_INIT_SCRIPT="VAR_MOOL_INIT_SCRIPT"
export MOOL_VIRTUALENV="VAR_VIRTUALENV_PATH"

function mool_init() {
  source "${MOOL_VIRTUALENV}"
  source "${MOOL_INIT_SCRIPT}"
  alias bu="${BU_SCRIPT_DIR}/bu"
  source "VAR_MOOL_AUTOCOMPLETE"
}
"""

SCALA_DEFAULT_VERSION = '2.8'

INSTALL_HELP_MSG = (
    '**** Refer to {0} link for installation instructions ****'.format(
        'https://github.com/rocketfuel/mool/wiki'))

BOOST_PACKAGE = (('http://downloads.sourceforge.net/project/boost/boost/'
                  '1.58.0/boost_1_58_0.tar.bz2'), 'boost_1_58_0',
                 '2fc96c1651ac6fe9859b678b165bd78dc211e881')

GMOCK_PACKAGE = ('https://googlemock.googlecode.com/files/gmock-1.7.0.zip',
                 'gmock-1.7.0', 'f9d9dd882a25f4069ed9ee48e70aff1b53e3c5a5')

PROTOBUF_PACKAGE = (('https://protobuf.googlecode.com/files/'
                     'protobuf-2.5.0.tar.bz2'), 'protobuf-2.5.0',
                    '62c10dcdac4b69cc8c6bb19f73db40c264cb2726')

SCALA_2_8 = ('http://www.scala-lang.org/files/archive/scala-2.8.2.final.tgz',
             'scala-2.8.2.final', '2d6250763dcba02f371e0c26999a4f43670e8e3e')

SCALA_2_10 = ('http://www.scala-lang.org/files/archive/scala-2.10.4.tgz',
              'scala-2.10.4', '970f779f155719838e81a267a7418a958fd4c13f')

SCALA_2_11 = ('http://www.scala-lang.org/files/archive/scala-2.11.4.tgz',
              'scala-2.11.4', 'a6d319b26ccabe9c609fadebc32e797bf9cb1084')

THRIFT_PACKAGE = (('http://www.us.apache.org/dist/thrift/0.9.1/'
                   'thrift-0.9.1.tar.gz'), 'thrift-0.9.1',
                  'dc54a54f8dc706ffddcd3e8c6cd5301c931af1cc')

VIRTUALENV_PACKAGE = (('https://pypi.python.org/packages/source/v/virtualenv/'
                       'virtualenv-1.11.6.tar.gz'), 'virtualenv-1.11.6',
                      'd3f8e94bf825cc999924e276c8f1c63b8eeb0715')

DOWNLOAD_ITEMS = (BOOST_PACKAGE, GMOCK_PACKAGE, PROTOBUF_PACKAGE, SCALA_2_8,
                  SCALA_2_10, SCALA_2_11, THRIFT_PACKAGE, VIRTUALENV_PACKAGE)

PIP_INSTALL_PACKAGES = [('pylint', '0.28.0'), ('pep8', '1.4.5'),
                        ('pytest', '2.3.4')]

GMOCK_BUILD_COMMANDS = [
    ('gcc -isystem ${GTEST_DIR}/include -I${GTEST_DIR}'
     ' -isystem ${GMOCK_DIR}/include -I${GMOCK_DIR}'
     ' -o${TARGET_DIR}/gtest-all.o -pthread -c ${GTEST_DIR}/src/gtest-all.cc'),
    ('gcc -isystem ${GTEST_DIR}/include -I${GTEST_DIR}'
     ' -isystem ${GMOCK_DIR}/include -I${GMOCK_DIR}'
     ' -o${TARGET_DIR}/gmock-all.o -pthread -c ${GMOCK_DIR}/src/gmock-all.cc'),
    ('gcc -isystem ${GTEST_DIR}/include -I${GTEST_DIR}'
     ' -c ${GTEST_DIR}/src/gtest_main.cc -o ${TARGET_DIR}/gtest_main.o'),
    ('ar -rv ${TARGET_DIR}/libgmock.a ${TARGET_DIR}/gtest-all.o'
     ' ${TARGET_DIR}/gmock-all.o')]


INSTALL_SUCCESS_MSG = """
********** Successfully installed build tool mool in {0} directory! **********
* Mool has been configure to use python virtual environment that points to {1}.
* Mool environment settings are in {2} file which you may want to look at.
* Entry for mool_init function has been added to {0}/moolrc file.
  You may want to add "source {0}/moolrc" in your bashrc/zshrc file.
* Execute `source {0}/moolrc && mool_init` to activate mool environment.
"""

def _is_valid_path(path_name):
    """Check if path is valid."""
    return path_name and os.path.exists(path_name)


def _check_sha_sum(file_path, sha_sum):
    """Check sha sum of a given file."""
    hash_object = hashlib.sha1()
    with open(file_path, 'r') as file_object:
        while True:
            file_text = file_object.read(BLOCK_SIZE)
            if not file_text:
                break
            hash_object.update(file_text)
    if hash_object.hexdigest() != sha_sum:
        raise Error('Sha1 mismatch for file {}!!'.format(file_path))


class Error(Exception):
    """Error class for this module."""
    def __exit__(self, etype, value, traceback):
        logging.error(self.message)


class Installer(object):
    """Installer main module."""
    @classmethod
    def _mkdir(cls, dir_path):
        """Recursively make directory."""
        subprocess.check_call(['mkdir', '-p', dir_path])

    @classmethod
    def _rmdir(cls, dir_path):
        """Recursively remove directory."""
        subprocess.check_call(['mkdir', '-p', dir_path])
        subprocess.check_call(['rm', '-rf', dir_path])

    def __init__(self, args):
        """Initializer."""
        self.args = args
        self.args.install_dir = os.path.realpath(self.args.install_dir)
        self.vars_to_export = {}
        self.root_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        self.openssl_install_path = None
        assert _is_valid_path(self.args.java_home), 'Need valid java home.'
        self.vars_to_export['JAVA_HOME'] = self.args.java_home.rstrip(os.sep)

    def _temp_dir(self):
        """Get temporary directory."""
        return os.path.join(self.args.install_dir, 'temp')

    def _downloads_dir(self):
        """Get download directory."""
        return os.path.join(self.args.install_dir, 'downloads')

    def _packages_dir(self):
        """Get package directory."""
        return os.path.join(self.args.install_dir, 'packages')

    def _virtual_env_dir(self):
        """Get virtual environment path."""
        return os.path.join(self.args.install_dir, 'MOOL_ENV')

    def _log_file_path(self):
        """Get log file path."""
        return os.path.join(self._temp_dir(), 'mool_install.log')

    def _execute(self, command, use_stdout=False, use_shell=False):
        """Executes a given command and logs stdout to file."""
        if use_shell:
            command_text_for_logging = command
        else:
            command_text_for_logging = ' '.join(command)
        start_time = time.time()
        logging.info('Executing "%s".', command_text_for_logging)
        try:
            if not use_stdout:
                with open(self._log_file_path(), 'a') as log_obj:
                    subprocess.check_call(
                        command, stdout=log_obj, shell=use_shell)
            else:
                subprocess.check_call(command, shell=use_shell)
        except subprocess.CalledProcessError:
            logging.error('Command "%s" failed!!', command_text_for_logging)
            raise
        elapsed_seconds = time.time() - start_time
        if elapsed_seconds > 60:
            logging.info('Command took %s minutes.',
                         str(round(elapsed_seconds / 60.0, 2)))

    def _copy_all(self, src_path, dst_path):
        """Recursively copy everything from src_path to dst_path."""
        flags = '-rf' if os.path.isdir(src_path) else '-f'
        self._execute(['cp', flags, src_path, dst_path])

    def _extract(self, source_file, dest_dir):
        """Extract a package to a directory."""
        assert os.path.exists(source_file), 'Source does not exist'
        assert not os.path.exists(dest_dir), 'Destination already exists'
        target_dir = os.path.dirname(dest_dir)
        logging.info('Extracting %s', os.path.basename(source_file))
        if source_file.endswith('.tar.gz'):
            self._execute(['tar', '-zxf', source_file, '-C', target_dir])
        elif source_file.endswith('.tgz'):
            self._execute(['tar', '-zxf', source_file, '-C', target_dir])
        elif source_file.endswith('.tar.bz2'):
            self._execute(['tar', '-xf', source_file, '-C', target_dir])
        elif source_file.endswith('.zip'):
            self._execute(['unzip', source_file, '-d', target_dir])
        assert_text = 'Directory "{}" does not exist'.format(dest_dir)
        assert os.path.exists(dest_dir), assert_text

    def _download_item(self, url, file_path, sha_sum):
        """Download url to file path. This function intially checks if the file
        exists and re-downloads only if necessary."""
        def _report_hook(count, block_size, total_size):
            """Handler for urllib report hook."""
            done = (block_size * count * 50 / total_size)
            print '\rDownload: [{}{}] {:>3}%'.format(
                '=' * done, ' ' * (50 - done), done * 2),
            sys.stdout.flush()

        # check for pre existence
        if os.path.exists(file_path):
            try:
                _check_sha_sum(file_path, sha_sum)
                return
            except Error:
                self._execute(['rm', '-f', file_path])
        # downloading the item
        temp_path = file_path + '.temp'
        logging.info('Downloading %s to %s.', url, file_path)
        urllib.urlretrieve(url, temp_path, reporthook=_report_hook)
        _check_sha_sum(temp_path, sha_sum)
        shutil.move(temp_path, file_path)

    def _touch_file(self, file_path):
        """Touch a file, typically a done marker file."""
        self._execute(['touch', '-f', file_path])

    def _check_dependencies(self):
        """Check for preinstalled dependencies required for mool."""
        logging.info('Checking support for JAVA.')
        try:
            javac_bin = os.path.join(self.vars_to_export['JAVA_HOME'], 'bin',
                                     'javac')
            output = subprocess.check_output([javac_bin, '-version'],
                                             stderr=subprocess.STDOUT).strip()
            version = tuple(
                [int(v) for v in output.split(' ')[1].split('.')[0:2]])
            if version < (1, 7):
                raise Error(('Java version found: %s, min required: %s. '
                             'Aborting installation!'), output, '1.7')
        except OSError:
            raise Error('Java support not found. Aborting installation!!')

        logging.info('Checking ant, required for thrift java compilation.')
        try:
            self._execute(['ant', '-version'])
        except OSError:
            raise Error('"ant" binary not found. Aborting installation!!')

        logging.info('Checking OpenSSL version > 1.0.0 for thrift libs')
        try:
            openssl_install_path = os.environ.get('OPENSSL_INSTALL_PATH', None)
            openssl = 'openssl'
            if openssl_install_path is not None:
                openssl = os.path.join(openssl_install_path, 'bin', 'openssl')
            output = subprocess.check_output([openssl, 'version'],
                                             stderr=subprocess.STDOUT).strip()
            version = tuple(
                [int(v) for v in output.split(' ')[1].split('.')[0:2]])
            if version < (1, 0):
                logging.error(('OpenSSL version found: %s, min required: %s. '
                              'Aborting installation!'), output, '1.0')
                raise Error(('Use OPENSSL_INSTALL_PATH key to use custom '
                             'OpenSSL installation'))
            self.openssl_install_path = openssl_install_path
        except OSError:
            raise Error('openssl binary not found!')
        logging.info('All dependency checks passed.')

    def _download_packages(self):
        """Download all required packages in one shot."""
        logging.info('Downloading packages.')
        os.chdir(self._downloads_dir())
        done_file = './downloads.done.txt'
        if not os.path.exists(done_file):
            used_dirs = []
            for package in DOWNLOAD_ITEMS:
                url, _, sha_sum = package
                dest_path = os.path.join(os.path.realpath('.'),
                                         os.path.basename(url))
                assert dest_path not in used_dirs
                logging.info('Downloading %s', os.path.basename(url))
                self._download_item(url, dest_path, sha_sum)
                used_dirs.append(dest_path)
            self._touch_file(done_file)

    def _extract_packages(self):
        """Expand all required packages in one shot."""
        logging.info('Extracting packages.')
        os.chdir(self._packages_dir())
        for package in DOWNLOAD_ITEMS:
            url, dir_name, _ = package
            source_file = os.path.join(self._downloads_dir(),
                                       os.path.basename(url))
            dest_dir = os.path.join(os.path.realpath('.'), dir_name)
            assert os.path.exists(source_file)
            if os.path.exists(dest_dir):
                continue
            self._extract(source_file, dest_dir)

    def _setup_protobuf(self):
        """Install protobuf."""
        logging.info('Setting up protobuf.')
        cur_dir = os.path.join(self._packages_dir(), PROTOBUF_PACKAGE[1])
        os.chdir(cur_dir)
        # Configure and install.
        done_marker = os.path.realpath('./step.0.done.txt')
        if not os.path.exists(done_marker):
            # Add missing '<iostream>' include statement.
            bad_file = 'src/google/protobuf/message.cc'
            with open(os.path.join(cur_dir, bad_file), 'r+') as file_obj:
                msg_file_contents = file_obj.readlines()
                msg_file_contents.insert(35, '#include <iostream>\n')
                file_obj.seek(0)
                file_obj.write(''.join(msg_file_contents))
            self._execute(['./configure', '--prefix={}'.format(cur_dir),
                           '--disable-shared', '--enable-static'])
            self._execute(['make', 'install'])
            self._touch_file(done_marker)
        assert os.path.exists(done_marker)
        protoc_binary = os.path.join(cur_dir, 'bin', 'protoc')
        assert os.path.exists(protoc_binary)
        self.vars_to_export['PROTO_COMPILER'] = protoc_binary

        # Build for python.
        done_marker = os.path.realpath('./step.1.done.txt')
        os.chdir(os.path.join(cur_dir, 'python'))
        if not os.path.exists(done_marker):
            self._execute(['python2.7', 'setup.py', 'build'])
            self._touch_file(done_marker)
        self.vars_to_export['PYTHON_PROTOBUF_DIR'] = os.path.join(
            os.path.realpath('.'), 'build', os.listdir('build')[0])

        # Build for java.
        os.chdir(os.path.join(cur_dir, 'java'))
        java_protobuf_jar = os.path.basename(cur_dir) + '.jar'
        target_dir = os.path.join(os.path.realpath('.'), 'target')
        protobuf_jar_path = os.path.join(target_dir, java_protobuf_jar)
        if not os.path.exists(protobuf_jar_path):
            self._execute([
                protoc_binary, '--java_out=src/main/java', '-I../src',
                '../src/google/protobuf/descriptor.proto'])
            self._mkdir(target_dir)
            javac_bin = os.path.join(
                self.vars_to_export['JAVA_HOME'], 'bin', 'javac')
            jar_bin = os.path.join(
                self.vars_to_export['JAVA_HOME'], 'bin', 'jar')
            command = [javac_bin, '-d', target_dir]
            src_dir = os.path.join(os.path.realpath('.'),
                                   'src/main/java/com/google/protobuf/')
            command.extend(
                [os.path.join(src_dir, f) for f in os.listdir(src_dir)])
            self._execute(command)
            os.chdir(target_dir)
            self._execute([jar_bin, '-cf', java_protobuf_jar, 'com'])
        assert os.path.exists(protobuf_jar_path)
        self.vars_to_export['JAVA_PROTOBUF_JAR'] = protobuf_jar_path

    def _setup_cc_libs(self):
        """Setup packages related to C++."""
        logging.info('Setting up C++ libraries.')
        assert 'JAVA_PROTOBUF_JAR' in self.vars_to_export
        os.chdir(self._packages_dir())
        cc_lib_dir = os.path.join(self._packages_dir(), 'cc_lib')
        proto_dir = os.path.join(self._packages_dir(), PROTOBUF_PACKAGE[1])
        cc_lib_libs = os.path.join(cc_lib_dir, 'lib')
        cc_lib_headers = os.path.join(cc_lib_dir, 'include')
        gmock_dir = os.path.join(self._packages_dir(), GMOCK_PACKAGE[1])
        done_file = os.path.join(cc_lib_dir, 'setup.done.txt')
        if not os.path.exists(done_file):
            self._mkdir(cc_lib_libs)
            self._mkdir(cc_lib_headers)
            for cmd in GMOCK_BUILD_COMMANDS:
                cmd = cmd.replace('${GTEST_DIR}',
                                  os.path.join(gmock_dir, 'gtest'))
                cmd = cmd.replace('${GMOCK_DIR}', os.path.join(gmock_dir))
                cmd = cmd.replace('${TARGET_DIR}', cc_lib_libs)
                self._execute(shlex.split(cmd.replace('\n', ' ')),
                              use_stdout=True)
                self._copy_all(
                    os.path.join(gmock_dir, 'include', 'gmock'),
                    cc_lib_headers)
                self._copy_all(
                    os.path.join(gmock_dir, 'gtest', 'include', 'gtest'),
                    cc_lib_headers)
            for lib in os.listdir(os.path.join(proto_dir, 'lib')):
                if lib.find('.so') < 0:
                    self._copy_all(os.path.join(proto_dir, 'lib', lib),
                                   cc_lib_libs)
            self._copy_all(os.path.join(proto_dir, 'include', 'google'),
                           cc_lib_headers)
            self._touch_file(done_file)
        assert os.path.exists(done_file)
        self.vars_to_export['CC_INSTALL_PREFIX'] = cc_lib_dir
        self.vars_to_export['GTEST_MAIN_LIB'] = os.path.join(cc_lib_libs,
                                                             'gtest_main.o')
        self.vars_to_export['GTEST_MOCK_LIB'] = os.path.join(cc_lib_libs,
                                                             'libgmock.a')

    def _setup_boost(self):
        """Setup Boost directory."""
        logging.info('Setting up Boost.')
        cur_dir = os.path.join(self._packages_dir(), BOOST_PACKAGE[1])
        os.chdir(cur_dir)
        target_dir = os.path.join(os.path.realpath('.'), 'target')
        if not os.path.exists(target_dir):
            done_marker = os.path.realpath('./step.0.done.txt')
            if not os.path.exists(done_marker):
                self._execute(['./bootstrap.sh'])
                self._touch_file(done_marker)
            self._mkdir(target_dir)
            self._execute(['./b2', '--prefix=' + target_dir, 'link=static',
                           'install'])
        self.vars_to_export['BOOST_DIR'] = target_dir

    def _setup_scala(self):
        """Setup Scala path vars."""
        logging.info('Setting up Scala.')
        items = (('SCALA_HOME_2_8', SCALA_2_8[1]),
                 ('SCALA_HOME_2_10', SCALA_2_10[1]),
                 ('SCALA_HOME_2_11', SCALA_2_11[1]))
        for env, package_path in items:
            self.vars_to_export[env] = os.path.join(self._packages_dir(),
                                                    package_path)

    def _setup_thrift(self):
        """Setup Thrift."""
        logging.info('Setting up thrift.')
        cur_dir = os.path.join(self._packages_dir(), THRIFT_PACKAGE[1])
        os.chdir(cur_dir)
        done_marker = os.path.join(cur_dir, 'thrift.patch.applied.txt')
        if not os.path.exists(done_marker):
            patch_file = os.path.join(self.root_dir, 'thrift.patch')
            try:
                self._execute(
                    ['patch', '-p1', '-d', '.', '-N', '-i', patch_file],
                    use_stdout=True)
            except subprocess.CalledProcessError:
                logging.info('Assuming thrift patch is already applied!')
            self._touch_file(done_marker)
        target_dir = os.path.join(cur_dir, 'target')
        if not os.path.exists(target_dir):
            openssl_opt = ''
            if self.openssl_install_path is not None:
                openssl_opt = '--with-openssl={} '.format(
                    self.openssl_install_path)
            command_parts = []
            command_parts.append('export PY_PREFIX={} && '.format(target_dir))
            command_parts.append('export JAVA_PREFIX={} && '.format(target_dir))
            command_parts.append('./configure --with-lua=no --with-perl=no ')
            command_parts.append('--with-php=no --with-ruby=no ')
            command_parts.append(openssl_opt)
            command_parts.append(
                '--with-boost={} '.format(self.vars_to_export['BOOST_DIR']))
            command_parts.append('--disable-shared ')
            command_parts.append('--prefix={}'.format(target_dir))
            command = ''.join(command_parts)
            self._mkdir(target_dir)
            self._execute(command, use_shell=True)
            self._execute('make install 2>&1', use_shell=True)
        assert os.path.exists(target_dir)

        pylib_target_dir = os.path.join(target_dir, 'pylib')
        if not os.path.exists(pylib_target_dir):
            # Python libs are copied to platform specific location.
            lib_dir = os.path.join(target_dir, 'lib')
            lib64_dir = os.path.join(target_dir, 'lib64')
            py_dir = None
            for directory in (lib_dir, lib64_dir):
                if not os.path.exists(directory):
                    continue
                py_dir = [d for d in os.listdir(directory)
                          if d.startswith('python')]
                if len(py_dir) > 0:
                    py_dir = os.path.join(
                        directory, py_dir[0], 'site-packages', 'thrift')
                    break
            self._mkdir(pylib_target_dir)
            self._copy_all(py_dir, pylib_target_dir)
        assert os.path.exists(pylib_target_dir)
        self.vars_to_export['THRIFT_DIR'] = target_dir

    def _setup_virtualenv(self):
        """Install and activate python virtual environment."""
        logging.info('Setting up virtualenv.')
        if not os.path.exists(self._virtual_env_dir()):
            virtualenv_py = os.path.join(self._packages_dir(),
                                         VIRTUALENV_PACKAGE[1], 'virtualenv.py')
            assert os.path.exists(virtualenv_py)
            self._execute(
                [sys.executable, virtualenv_py, '--no-site-packages', '-p',
                 sys.executable, self._virtual_env_dir()])
            activate_script = os.path.join(self._virtual_env_dir(), 'bin',
                                           'activate')
            for package, version in PIP_INSTALL_PACKAGES:
                full_name = '{}=={}'.format(package, version)
                self._execute('source {} && pip install {}'.format(
                    activate_script, full_name), use_stdout=False,
                    use_shell=True)
        assert os.path.exists(self._virtual_env_dir())

    def _setup_mool(self):
        """Install mool."""
        logging.info('Setting up mool.')
        mool_rc_file = os.path.join(self.args.install_dir, 'moolrc')
        if os.path.exists(mool_rc_file):
            return
        self.vars_to_export['JAR_SEARCH_PATH'] = os.path.join(
            self.args.install_dir, 'jars')
        self.vars_to_export['SCALA_DEFAULT_VERSION'] = SCALA_DEFAULT_VERSION
        mool_init_template = os.path.join(
            self.root_dir, MOOL_INIT_TEMPLATE_FILE)
        file_contents = None
        with open(mool_init_template, 'r') as template_file:
            file_contents = template_file.read()
        for var in MOOL_INIT_VARS:
            file_contents = file_contents.replace('VAR_{}'.format(var),
                                                  self.vars_to_export[var])
        mool_autocomplete_src = os.path.join(self.root_dir,
                                         MOOL_AUTOCOMPLETE_SCRIPT)
        mool_autocomplete_dst = os.path.join(self.args.install_dir,
                                             MOOL_AUTOCOMPLETE_SCRIPT)
        shutil.copy(mool_autocomplete_src, mool_autocomplete_dst)

        mool_init_script = os.path.join(self.args.install_dir, 'mool_init.sh')
        with open(mool_init_script, 'w') as init_file:
            init_file.write(file_contents)
        moolrc_text = MOOLRC_TEXT.replace('VAR_MOOL_INIT_SCRIPT',
                                          mool_init_script)
        moolrc_text = moolrc_text.replace(
            'VAR_VIRTUALENV_PATH',
            os.path.join(self._virtual_env_dir(), 'bin', 'activate'))
        moolrc_text = moolrc_text.replace('VAR_MOOL_AUTOCOMPLETE',
                                          mool_autocomplete_dst)
        with open(mool_rc_file, 'w') as moolrc_obj:
            moolrc_obj.write(moolrc_text)
        logging.info(INSTALL_SUCCESS_MSG.format(
            self.args.install_dir, self._virtual_env_dir(), mool_init_script))

    def do_install(self):
        """Entry point for installation steps."""
        if self.args.test_only:
            return
        logging.info('Using "%s" as installation directory.',
                     self.args.install_dir)
        logging.info('Using "%s" for installation log.', self._log_file_path())
        if self.args.fresh:
            self._rmdir(self.args.install_dir)
        self._mkdir(self._temp_dir())
        self._mkdir(self._downloads_dir())
        self._mkdir(self._packages_dir())
        self._check_dependencies()
        self._download_packages()
        self._extract_packages()
        self._setup_protobuf()
        self._setup_cc_libs()
        self._setup_boost()
        self._setup_scala()
        self._setup_thrift()
        self._setup_virtualenv()
        for _, value in self.vars_to_export.iteritems():
            assert os.path.exists(value)
        self._setup_mool()

    def do_test(self):
        """Execute tests."""
        logging.info('Running mool tests using current environment setup.')
        os.chdir(self.root_dir)
        activate_script = os.path.join(self._virtual_env_dir(), 'bin',
                                       'activate')
        test_script = os.path.join(os.path.dirname(self.root_dir),
                                   'test_all.sh')
        self._execute('source {} && {}'.format(activate_script, test_script),
                      use_stdout=True, use_shell=True)
        logging.info('Post-install tests ran successfully.')


def do_main():
    """Entry point."""
    logging.basicConfig(level=logging.DEBUG,
                        format='%(levelname)-6s: %(message)s')
    try:
        arg_parser = argparse.ArgumentParser()
        arg_parser.add_argument(
            '-d', '--install_dir', type=str,
            default=os.path.realpath('./.rfmool'),
            help='Installation path for mool.')
        arg_parser.add_argument(
            '-j', '--java_home', type=str, default=os.environ.get('JAVA_HOME'),
            help='Path to JAVA Home. Default JAVA_HOME environment variable.')
        arg_parser.add_argument(
            '-t', '--test_only', default=False,
            action='store_true', help='Test current mool installation.')
        arg_parser.add_argument(
            '-fi', '--fresh', default=False, action='store_true',
            help='Erase existing and install fresh copy of mool.')
        installer = Installer(arg_parser.parse_args())
        installer.do_install()
        installer.do_test()
        return 0
    except:
        ex = sys.exc_info()[1]
        if isinstance(ex, Error):
            logging.debug('Exception: %s', ex.message)
        else:
            logging.debug('Exception: %s', str(sys.exc_info()))
        print INSTALL_HELP_MSG
        return 1


if __name__ == '__main__':
    sys.exit(do_main())
