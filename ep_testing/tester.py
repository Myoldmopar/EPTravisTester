import os
from tempfile import mkdtemp

from ep_testing.config import TestConfiguration, OS
from ep_testing.tests.api import TestPythonAPIAccess, TestCAPIAccess, TestCppAPIDelayedAccess
from ep_testing.tests.energyplus import TestPlainDDRunEPlusFile
from ep_testing.tests.expand_objects import TestExpandObjectsAndRun
from ep_testing.tests.transition import TransitionOldFile


class Tester:

    def __init__(self, config: TestConfiguration, install_path: str, verbose: bool):
        self.install_path = install_path
        self.config = config
        self.verbose = verbose

    def run(self):
        saved_path = os.getcwd()
        temp_dir = mkdtemp()
        print('Creating sandbox dir and changing to it: ' + temp_dir)
        os.chdir(temp_dir)
        TestPlainDDRunEPlusFile().run(
            self.install_path, self.verbose, {'test_file': '1ZoneUncontrolled.idf'}
        )
        TestPlainDDRunEPlusFile().run(
            self.install_path, self.verbose, {'test_file': 'PythonPluginCustomOutputVariable.idf'}
        )
        TestExpandObjectsAndRun().run(
            self.install_path, self.verbose, {'test_file': 'HVACTemplate-5ZoneFanCoil.idf'}
        )
        TransitionOldFile().run(
            self.install_path, self.verbose, {'last_version': self.config.tag_last_version}
        )
        if self.config.os == OS.Windows:
            if self.verbose:
                print("Symlink runs are not testable on Travis, I think the user doesn't have symlink privilege.")
        else:
            TestPlainDDRunEPlusFile().run(
                self.install_path, self.verbose, {'test_file': '1ZoneUncontrolled.idf', 'binary_sym_link': True}
            )
        TestCAPIAccess().run(
            self.install_path, self.verbose, {'os': self.config.os, 'bitness': self.config.bitness}
        )
        TestCppAPIDelayedAccess().run(
            self.install_path, self.verbose, {'os': self.config.os, 'bitness': self.config.bitness}
        )
        if self.config.bitness == 'x32':
            if self.verbose:
                print("Travis does not have a 32-bit Python package readily available")
        else:
            TestPythonAPIAccess().run(
                self.install_path, self.verbose, {'os': self.config.os}
            )
        os.chdir(saved_path)
