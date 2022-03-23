
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
    'mac1015': {
        'os': OS.Mac, 'bitness': 'x64', 'asset_pattern': 'Darwin-macOS10.15-x86_64.tar.gz', 'os_version': '10.15'
    },  # 10.15 on 10.15
    'mac11': {
        'os': OS.Mac, 'bitness': 'x64', 'asset_pattern': 'Darwin-macOS11.6-x86_64.tar.gz', 'os_version': '11.0'
    },  # 10.15 on 11
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
            self.msvc_version = 16  # Default to 2017 for Travis
        self.asset_pattern = this_config['asset_pattern']
        self.bitness = this_config['bitness']

        self.this_version = '22.1'
        self.tag_this_version = 'v22.1.0-TestBuild2'
        self.last_version = '9.6'
        self.tag_last_version = 'v9.6.0'
