# -*- coding: utf-8 -*-
"""Defines helper functions for cmake interaction"""
import subprocess
import multiprocessing
import os


def architecture_to_generator(arch):
    """Gets the required generator for a given architecture"""
    known_arches = {
        'x86_64-win-msvc_2015': 'Visual Studio 14 2015 Win64',
        'x86_32-win-msvc_2015': 'Visual Studio 14 2015',
        'x86_64-win-msvc_2013': 'Visual Studio 12 2013 Win64',
        'x86_32-win-msvc_2013': 'Visual Studio 12 2013'
    }
    return known_arches.get(arch, 'Unix Makefiles')


def get_toolchain_file_from_arch(arch):
    """Gets the required toolchain file for a given architecture"""
    ret = None
    if 'arm32-linux-gnueabihf' in arch:
        import pkg_resources
        ret = pkg_resources.resource_filename('zazu', 'cmake/arm32-linux-gnueabihf.cmake')
    return ret


def known_arches():
    """Lists arches that zazu is familiar with"""
    return ['local',
            'arm32-linux-gnueabihf',
            'arm32-none-eabi',
            'x86_64-linux-gcc',
            'x86_32-linux-gcc',
            'x86_64-win-msvc_2013',
            'x86_64-win-msvc_2015',
            'x86_32-win-msvc_2013',
            'x86_32-win-msvc_2015']


def configure(repo_root, build_dir, arch, build_type, build_variables, echo=lambda x: x):
    """Configures a cmake based project to be built and caches args used to bypass configuration in future"""
    os.chdir(build_dir)
    configure_args = ['cmake',
                      repo_root,
                      '-G', architecture_to_generator(arch),
                      '-DCMAKE_BUILD_TYPE=' + build_type.capitalize(),
                      '-DCPACK_SYSTEM_NAME=' + arch,
                      '-DCPACK_PACKAGE_VERSION=' + build_variables['ZAZU_BUILD_VERSION'],
                      '-DZAZU_TOOL_PATH=' + os.path.expanduser('~/.zazu/tools')
                      ]
    for k, v in build_variables.items():
        configure_args.append('-D{}={}'.format(k, v))
    toolchain_file = get_toolchain_file_from_arch(arch)
    if toolchain_file is not None:
        configure_args.append('-DCMAKE_TOOLCHAIN_FILE=' + toolchain_file)

    configure_arg_str = ' '.join(configure_args)
    echo('CMake Configuration: {}'.format('\n    '.join(configure_args)))
    cache_file = os.path.join(build_dir, 'cmake_command.txt')
    previous_args = ''
    try:
        with file(cache_file) as f:
            previous_args = f.read()
    except IOError:
        pass
    r = 0
    if previous_args != configure_arg_str:
        try:
            r = subprocess.call(configure_args)
        except OSError:
            r = -1
            warn_uninstalled(configure_args[0])
        if not r:
            # Cache the call args
            with open(cache_file, 'w') as f:
                f.write(configure_arg_str)
    return r


def warn_uninstalled(pkg_name):
    """Prints a warning to std error for a missing package"""
    print('{0} not found, install it via "apt-get install {0}" or "brew install {0}"'.format(pkg_name))


def build(build_dir, build_type, target, verbose):
    """Build using CMake"""
    os.chdir(build_dir)
    if 'nt' in os.name:
        build_args = ['cmake', '--build', '.', '--config', build_type.capitalize()]
        if 'all' not in target:
            build_args.append('--target')
            build_args.append(target)
    else:
        build_args = ['make', '-j{}'.format(multiprocessing.cpu_count()), target]
        if verbose:
            build_args.append('VERBOSE=1')
    try:
        ret = subprocess.call(build_args)
    except OSError:
        warn_uninstalled(build_args[0])
    return ret

build_types = ['release', 'debug', 'minSizeRel', 'relWithDebInfo', 'coverage']
