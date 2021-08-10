import distutils.cmd
import distutils.log
from setuptools import setup
from ep_testing.downloader import Downloader
from ep_testing.tester import Tester
from ep_testing.config import TestConfiguration, CONFIGURATIONS


class Runner(distutils.cmd.Command):
    """A custom command to run E+ tests using `setup.py run --run_config <key>`"""

    description = 'Run E+ tests on installers for this platform'
    user_options = [
        # The format is (long option, short option, description).
        ('run-config=', None, 'Run configuration, see possible options in config.py'),
    ]

    def __init__(self, dist):
        super().__init__(dist)
        self.run_config = None

    def initialize_options(self):
        ...

    def finalize_options(self):
        if self.run_config is None:
            raise Exception("Parameter --run_config is missing")
        if self.run_config not in CONFIGURATIONS:
            raise Exception("Parameter --run_config has invalid value, see options in config.py")

    def run(self):
        verbose = True
        c = TestConfiguration(self.run_config)
        self.announce('Attempting to test tag name: %s' % c.tag_this_version, level=distutils.log.INFO)
        d = Downloader(c, self.announce)
        self.announce('EnergyPlus package extracted to: ' + d.extracted_install_path(), level=distutils.log.INFO)
        t = Tester(c, d.extracted_install_path(), verbose)
        # unhandled exceptions should cause this to fail
        t.run()


setup(
    name='EPSanityTester',
    version='0.2',
    packages=['ep_testing'],
    url='github.com/NREL/EnergyPlus',
    license='',
    author='edwin',
    author_email='',
    description='A small set of test scripts that will pull E+ installers and run a series of tests on them',
    cmdclass={
        'run': Runner,
    },
)
