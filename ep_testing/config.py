import os
import shutil
from tempfile import mkdtemp


class OS:
    Windows = 1
    Linux = 2
    Mac = 3


CONFIGURATIONS = {
    'ubuntu1804': {
        'os': OS.Linux, 'bitness': 'x64', 'asset_pattern': 'Linux-Ubuntu18.04-x86_64.tar.gz', 'os_version': '18.04'
    },
    'ubuntu2004': {
        'os': OS.Linux, 'bitness': 'x64', 'asset_pattern': 'Linux-Ubuntu20.04-x86_64.tar.gz', 'os_version': '20.04'
    },
    'mac1014': {
        'os': OS.Mac, 'bitness': 'x64', 'asset_pattern': 'Darwin-macOS10.15-x86_64.tar.gz', 'os_version': '10.14'
    },  # 10.15 on 10.14
    'mac1015': {
        'os': OS.Mac, 'bitness': 'x64', 'asset_pattern': 'Darwin-macOS10.15-x86_64.tar.gz', 'os_version': '10.15'
    },  # 10.15 on 10.15
    'win32': {
        'os': OS.Windows, 'bitness': 'x32', 'asset_pattern': 'Windows-i386.zip', 'os_version': '10'
    },
    'win64': {
        'os': OS.Windows, 'bitness': 'x64', 'asset_pattern': 'Windows-x86_64.zip', 'os_version': '10'
    },
}


class TestConfiguration:

    def __init__(self, run_config_key, msvc_version=None):

        # invalid keys are protected in the command's finalize_options method
        this_config = CONFIGURATIONS[run_config_key]
        self.os_version = this_config['os_version']
        self.os = this_config['os']
        self.msvc_version = None
        if msvc_version is not None:
            self.msvc_version = msvc_version
        elif self.os == OS.Windows:
            self.msvc_version = 15  # Default to 2017 for Travis

        self.asset_pattern = this_config['asset_pattern']
        self.bitness = this_config['bitness']

        self.this_version = '9.6'
        self.tag_this_version = 'v9.6.0-RC5'
        self.last_version = '9.5'
        self.tag_last_version = 'v9.5.0'

        # If this is turned on, it expects to find an asset already downloaded at the specified location
        self.skip_download = False
        self.skipped_download_file = '/tmp/ep.tar.gz'

        # But if we are on Travis, we override it to always download a new asset
        if os.environ.get('TRAVIS'):
            self.skip_download = False

        self.download_dir = mkdtemp()
        if self.skip_download:
            target_file_name = 'ep.tar.gz'
            if self.os == OS.Windows:
                target_file_name = 'ep.zip'
            file_path = os.path.join(self.download_dir, target_file_name)
            shutil.copy(self.skipped_download_file, file_path)
