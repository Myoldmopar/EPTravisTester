import os
import platform
import subprocess
from subprocess import CalledProcessError
from tempfile import mkdtemp, mkstemp
from typing import List

from ep_testing.config import OS
from ep_testing.exceptions import EPTestingException
from ep_testing.tests.base import BaseTest


def api_resource_dir() -> str:
    this_file_path = os.path.realpath(__file__)
    this_directory = os.path.dirname(this_file_path)
    templates_dir = os.path.join(this_directory, 'api_templates')
    return templates_dir


def my_check_call(verbose: bool, command_line: List[str], **kwargs) -> None:

    r = subprocess.run(command_line,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, **kwargs)
    if r.returncode == 0 and verbose:
        print(r.stderr.decode().strip())
    else:
        raise CalledProcessError(
            r.returncode, command_line,
            'Command failed!\n'
            'stderr:\n{}'
            '\n\n'
            'stdout:\n{}'.format(r.stderr.decode().strip(),
                                 r.stdout.decode().strip()))


class TestPythonAPIAccess(BaseTest):

    def __init__(self):
        super().__init__()
        self.os = None

    def name(self):
        return 'Test running an API script against pyenergyplus'

    @staticmethod
    def _api_script_content(install_root: str) -> str:
        if platform.system() in ['Linux', 'Darwin']:
            pass
        else:  # windows
            install_root = install_root.replace('\\', '\\\\')
        template_file = os.path.join(api_resource_dir(), 'python_link.py')
        template = open(template_file).read()
        return template % install_root

    def run(self, install_root: str, verbose: bool, kwargs: dict):
        self.verbose = verbose
        print('* Running test class "%s"... ' % self.__class__.__name__, end='')
        if 'os' not in kwargs:
            raise EPTestingException('Bad call to %s -- must pass os in kwargs' % self.__class__.__name__)
        self.os = kwargs['os']
        handle, python_file_path = mkstemp(suffix='.py')
        with os.fdopen(handle, 'w') as f:
            f.write(self._api_script_content(install_root))
        print(' [FILE WRITTEN] ', end='')
        try:
            if platform.system() == 'Linux':
                py = 'python3'
            elif platform.system() == 'Darwin':
                py = '/usr/local/bin/python3'
            else:  # windows
                py = 'C:\\Python36\\Python.exe'
            my_env = os.environ.copy()
            if self.os == OS.Windows:  # my local comp didn't have cmake in path except in interact shells
                my_env["PATH"] = install_root + ";" + my_env["PATH"]
            my_check_call(self.verbose, [py, python_file_path], env=my_env)
            print(' [DONE]!')
        except CalledProcessError as e:
            print('Python API Wrapper Script failed!')
            raise e


def make_build_dir_and_build(cmake_build_dir: str, verbose: bool, this_os: int, bitness: str):
    try:
        os.makedirs(cmake_build_dir)
        my_env = os.environ.copy()
        if this_os == OS.Mac:  # my local comp didn't have cmake in path except in interact shells
            my_env["PATH"] = "/usr/local/bin:" + my_env["PATH"]
        command_line = ['cmake', '..']
        if this_os == OS.Windows:
            if bitness == 'x64':
                command_line.extend(['-G', 'Visual Studio 15 Win64'])
            elif bitness == 'x32':
                command_line.extend(['-G', 'Visual Studio 15'])  # defaults to 32
            else:
                raise EPTestingException('Bad bitness sent to make_build_dir_and_build')
        my_check_call(verbose, command_line, cwd=cmake_build_dir, env=my_env)
        command_line = ['cmake', '--build', '.']
        if platform.system() == 'Windows':
            command_line.extend(['--config', 'Release'])
        my_check_call(verbose, command_line, env=my_env, cwd=cmake_build_dir)
        print(' [COMPILED] ', end='')
    except CalledProcessError as e:
        print("C API Wrapper Compilation Failed!")
        raise e


class TestCAPIAccess(BaseTest):

    def __init__(self):
        super().__init__()
        self.os = None
        self.bitness = None
        self.source_file_name = 'func.c'
        self.target_name = 'TestCAPIAccess'

    def name(self):
        return 'Test running an API script against energyplus in C'

    @staticmethod
    def _api_fixup_content() -> str:
        template_file = os.path.join(api_resource_dir(), 'eager_cpp_fixup.txt')
        template = open(template_file).read()
        return template

    def _api_cmakelists_content(self, install_path: str) -> str:
        if platform.system() == 'Linux':
            lib_file_name = 'libenergyplusapi.so'
        elif platform.system() == 'Darwin':
            lib_file_name = 'libenergyplusapi.dylib'
        else:  # windows
            lib_file_name = 'energyplusapi.lib'
            install_path = install_path.replace('\\', '\\\\')
        template_file = os.path.join(api_resource_dir(), 'eager_cpp_cmakelists.txt')
        template = open(template_file).read()
        return template.format(
            EPLUS_INSTALL_NO_SLASH=install_path, LIB_FILE_NAME=lib_file_name,
            TARGET_NAME=self.target_name, SOURCE_FILE=self.source_file_name
        )

    @staticmethod
    def _api_script_content() -> str:
        template_file = os.path.join(api_resource_dir(), 'eager_cpp_source.cpp')
        template = open(template_file).read()
        return template

    def run(self, install_root: str, verbose: bool, kwargs: dict):
        self.verbose = verbose
        print('* Running test class "%s"... ' % self.__class__.__name__, end='')
        if 'os' not in kwargs:
            raise EPTestingException('Bad call to %s -- must pass os in kwargs' % self.__class__.__name__)
        if 'bitness' not in kwargs:
            raise EPTestingException('Bad call to %s -- must pass bitness in kwargs' % self.__class__.__name__)
        self.os = kwargs['os']
        self.bitness = kwargs['bitness']
        build_dir = mkdtemp()
        c_file_name = self.source_file_name
        c_file_path = os.path.join(build_dir, c_file_name)
        with open(c_file_path, 'w') as f:
            f.write(self._api_script_content())
        print(' [SRC FILE WRITTEN] ', end='')
        cmake_lists_path = os.path.join(build_dir, 'CMakeLists.txt')
        with open(cmake_lists_path, 'w') as f:
            f.write(self._api_cmakelists_content(install_root))
        print(' [CMAKE FILE WRITTEN] ', end='')
        fixup_cmake_path = os.path.join(build_dir, 'fixup.cmake')
        with open(fixup_cmake_path, 'w') as f:
            f.write(self._api_fixup_content())
        print(' [FIXUP CMAKE WRITTEN] ', end='')
        cmake_build_dir = os.path.join(build_dir, 'build')
        make_build_dir_and_build(cmake_build_dir, self.verbose, self.os, self.bitness)
        try:
            new_binary_path = os.path.join(cmake_build_dir, self.target_name)
            if self.os == OS.Windows:  # override the path/name for Windows
                new_binary_path = os.path.join(cmake_build_dir, 'Release', self.target_name + '.exe')
            command_line = [new_binary_path]
            my_check_call(self.verbose, command_line, cwd=install_root)
        except CalledProcessError as e:
            print('C API Wrapper Execution failed!')
            raise e
        print(' [DONE]!')


class TestCppAPIDelayedAccess(BaseTest):

    def __init__(self):
        super().__init__()
        self.os = None
        self.bitness = None
        self.source_file_name = 'func.cpp'
        self.target_name = 'TestCAPIAccess'

    def name(self):
        return 'Test running an API script against energyplus in C++ but with delayed DLL loading'

    def _api_cmakelists_content(self) -> str:
        template_file = os.path.join(api_resource_dir(), 'delayed_cpp_cmakelists.txt')
        template = open(template_file).read()
        return template.format(TARGET_NAME=self.target_name, SOURCE_FILE=self.source_file_name)

    @staticmethod
    def _api_script_content(install_path: str) -> str:
        if platform.system() == 'Linux':
            lib_file_name = '/libenergyplusapi.so'
        elif platform.system() == 'Darwin':
            lib_file_name = '/libenergyplusapi.dylib'
        else:  # windows
            raise EPTestingException('Dont call TestCAPIDelayedAccess._api_script_content for Windows')
        template_file = os.path.join(api_resource_dir(), 'delayed_cpp_source_linux_mac.cpp')
        template = open(template_file).read()
        return template.replace('{EPLUS_INSTALL_NO_SLASH}', install_path).replace('{LIB_FILE_NAME}', lib_file_name)

    @staticmethod
    def _api_script_content_windows(install_path: str) -> str:
        lib_file_name = '\\\\energyplusapi.dll'
        install_path = install_path.replace('\\', '\\\\')
        template_file = os.path.join(api_resource_dir(), 'delayed_cpp_source_windows.cpp')
        template = open(template_file).read()
        return template.replace('{EPLUS_INSTALL_NO_SLASH}', install_path).replace('{LIB_FILE_NAME}', lib_file_name)

    def run(self, install_root: str, verbose: bool, kwargs: dict):
        self.verbose = verbose
        print('* Running test class "%s"... ' % self.__class__.__name__, end='')
        if 'os' not in kwargs:
            raise EPTestingException('Bad call to %s -- must pass os in kwargs' % self.__class__.__name__)
        if 'bitness' not in kwargs:
            raise EPTestingException('Bad call to %s -- must pass bitness in kwargs' % self.__class__.__name__)
        self.os = kwargs['os']
        self.bitness = kwargs['bitness']
        build_dir = mkdtemp()
        c_file_name = 'func.cpp'
        c_file_path = os.path.join(build_dir, c_file_name)
        with open(c_file_path, 'w') as f:
            if platform.system() == 'Linux' or platform.system() == 'Darwin':
                f.write(self._api_script_content(install_root))
            else:
                f.write(self._api_script_content_windows(install_root))
        print(' [SRC FILE WRITTEN] ', end='')
        cmake_lists_path = os.path.join(build_dir, 'CMakeLists.txt')
        with open(cmake_lists_path, 'w') as f:
            f.write(self._api_cmakelists_content())
        print(' [CMAKE FILE WRITTEN] ', end='')
        cmake_build_dir = os.path.join(build_dir, 'build')
        make_build_dir_and_build(cmake_build_dir, self.verbose, self.os, self.bitness)
        if platform.system() == 'Windows':
            built_binary_path = os.path.join(cmake_build_dir, 'Release', 'TestCAPIAccess')
        else:
            built_binary_path = os.path.join(cmake_build_dir, 'TestCAPIAccess')
        my_env = os.environ.copy()
        if self.os == OS.Windows:  # my local comp didn't have cmake in path except in interact shells
            my_env["PATH"] = install_root + ";" + my_env["PATH"]
        try:
            my_check_call(self.verbose, [built_binary_path], env=my_env)
        except CalledProcessError as e:
            print("Delayed C API Wrapper execution failed")
            raise e
        print(' [DONE]!')
