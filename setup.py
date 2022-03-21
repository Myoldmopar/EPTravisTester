from os import path
from setuptools import setup
from tempfile import mkdtemp
import distutils.cmd
import distutils.log
from ep_testing.downloader import Downloader
from ep_testing.tester import Tester
from ep_testing.config import TestConfiguration, CONFIGURATIONS


class Runner(distutils.cmd.Command):
    """A custom command to run E+ tests using `setup.py run --run_config <key>`

    Locally it is also possible to path two extract parameters:
    * the path to where you extracted the tar.gz/zip manually, and,
    * on windows: the version of MSVC to use

    eg: `python setup.py run --verbose_output
                             --run-config win64
                             --msvc-version 16
                             --extracted-install-path "path/to/EnergyPlus-9.6.0-ed3a9d36c8-Windows-x86_64"`

    """

    description = 'Run E+ tests on installers for this platform'
    user_options = [
        # The format is (long option, short option, description).
        ('run-config=', None, 'Run configuration, see possible options in config.py'),
        ('use-local-copy=', 'x',
         'Specifies a path to a local E+ copy for testing, either a path to an archive, or an extracted directory'),
        ('msvc-version=', None,
         'For OS.Windows only, specifies a MSVC generator to use. 15 is default, you can override to 16'),
        # distutils is already claiming --verbose and setting it as default = 1
        ('verbose-output', None, 'Enable verbose mode'),
    ]

    def __init__(self, dist):
        super().__init__(dist)
        self.run_config = None
        self.use_local_copy = None
        self.msvc_version = None
        self.verbose_output = None

    def initialize_options(self):
        self.run_config = None
        self.use_local_copy = None
        self.msvc_version = None
        self.verbose_output = None

    def finalize_options(self):
        if self.run_config is None:
            raise Exception("Parameter --run_config is missing")
        if self.run_config not in CONFIGURATIONS:
            raise Exception("Parameter --run_config has invalid value, see options in config.py")
        if self.msvc_version is not None:
            if "win" not in self.run_config:
                raise Exception("Parameter --msvc_version doesn't apply not non windows OS")
            try:
                self.msvc_version = int(self.msvc_version)
            except ValueError:
                raise Exception("Parameter --msvc_version should be an int like 15 (2017) or 16 (2019)")

        if self.verbose_output is None:
            self.verbose_output = False
        else:
            self.verbose_output = bool(self.verbose_output)

    def run(self):

        c = TestConfiguration(self.run_config, self.msvc_version)
        self.announce('Attempting to test tag name: %s' % c.tag_this_version, level=distutils.log.INFO)
        download_dir: str = mkdtemp()
        local_copy: str = self.use_local_copy
        if local_copy is None:
            d = Downloader(c, download_dir, announce=self.announce)
            local_copy = d.extracted_install_path
            self.announce(f'EnergyPlus package extracted to: {local_copy}', level=distutils.log.INFO)
        else:
            if path.isdir(local_copy):
                # in this case local copy is already an extracted dir, no need to do anything, just test
                self.announce(f'Using local EnergyPlus package extracted at: {local_copy}', level=distutils.log.INFO)
            elif path.isfile(local_copy):
                self.announce(f'Using local EnergyPlus archive at {local_copy}', level=distutils.log.INFO)
                # this call will skip downloading, but it will extract it to a new directory
                d = Downloader(c, download_dir, use_local=local_copy, announce=self.announce)
                local_copy = d.extracted_install_path
            else:
                self.announce(
                    f'Trying to use local copy at {local_copy}, but it does not exist!  Aborting...',
                    level=distutils.log.INFO
                )
                return
        t = Tester(c, local_copy, self.verbose_output)
        # unhandled exceptions should cause this to fail
        t.run()


# the cmdclass entry below is expecting a Mapping[str, Type(Command)], which is essentially what we have with our
# inherited Command class above, but for whatever reason, the type inference engine is complaining, so I'm ignoring that
# inspection for this one declaration
# noinspection PyTypeChecker
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
