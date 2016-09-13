import click
import shutil
import subprocess
import config
import cmake_helper
import os


class ComponentConfiguration:

    def __init__(self, component):
        self._name = component['name']
        self._description = component.get('description', '')
        self._goals = {}
        for g in component['goals']:
            self._goals[g['name']] = BuildGoal(g)

    def get_spec(self, goal, arch, type):
        try:
            build_goal = self._goals[goal]
            ret = build_goal.get_build(arch)
            if type is not None:
                ret._build_type = type
        except KeyError:
            ret = BuildSpec()
        return ret

    def description(self):
        return self._description

    def name(self):
        return self._name

    def goals(self):
        return self._goals


class BuildGoal:

    def __init__(self, goal):
        self._name = goal.get('name', '')
        self._description = goal.get('description', '')
        self._build_type = goal.get('buildType', None)
        self._build_vars = goal.get('buildVars', {})
        self._requires = goal.get('requires', {})
        self._builds = {}
        self._default_spec = BuildSpec(self._build_type, self._build_vars, self._requires, self._description)
        for b in goal['builds']:
            vars = b.get('buildVars', self._build_vars)
            type = b.get('buildType', self._build_type)
            requires = b.get('requires', {})
            requires.update(self._requires)
            description = b.get('description', '')
            arch = b['arch']
            script = b.get('script', None)
            self._builds[arch] = BuildSpec(type, vars, requires, description, arch, script=script)

    def description(self):
        return self._description

    def name(self):
        return self._name

    def builds(self):
        return self._builds

    def get_build(self, arch):
        return self._builds.get(arch, self._default_spec)


class BuildSpec:

    def __init__(self, type='release', vars={}, requires={}, description='', arch='', script=None):
        self._build_type = type
        self._build_vars = vars
        self._build_requires = requires
        self._build_description = description
        self._build_arch = arch
        self._build_script = script

    def build_type(self):
        return self._build_type

    def build_vars(self):
        return self._build_vars

    def build_requires(self):
        return self._build_requires

    def build_description(self):
        return self._build_description

    def build_arch(self):
        return self._build_arch

    def build_script(self):
        return self._build_script


def cmake_build(repo_root, arch, type, goal, verbose, vars):
    """Build using cmake"""
    if arch not in cmake_helper.known_arches():
        raise click.BadParameter("Arch not recognized, choose from:\n    - {}".format('\n    - '.join(cmake_helper.known_arches())))

    build_dir = os.path.join(repo_root, 'build', '{}-{}'.format(arch, type))
    ret = 0
    try:
        os.makedirs(build_dir)
    except OSError:
        pass
    if 'distclean' in goal:
        shutil.rmtree(build_dir)
    else:
        ret = cmake_helper.configure(repo_root, build_dir, arch, type, vars, click.echo if verbose else lambda x: x)
        if ret:
            raise click.ClickException("Error configuring with cmake")
        ret = cmake_helper.build(build_dir, type, goal, verbose)
        if ret:
            raise click.ClickException("Error building with cmake")
    return ret


@click.command()
@click.pass_context
@click.option('-a', '--arch', default='local', help='the desired architecture to build for')
@click.option('-t', '--type', type=click.Choice(cmake_helper.build_types),
              help='defaults to what is specified in the {} file, or release if unspecified there'.format(config.PROJECT_FILE_NAME))
@click.option('-v', '--verbose', is_flag=True, help='generates verbose output from the build')
@click.argument('goal')
def build(ctx, arch, type, verbose, goal):
    """Build project targets, the GOAL argument is the desired make target,
     use distclean to clean whole build folder"""
    # Run the supplied build command if there is one, otherwise assume cmake
    # Parse file to find requirements then check that they exist, then build
    project_config = ctx.obj.project_config()
    component = ComponentConfiguration(project_config['components'][0])
    spec = component.get_spec(goal, arch, type)
    requirements = spec.build_requires().get('zazu', [])
    for req in requirements:
        if verbose:
            tool_helper.install_spec(req, echo=click.echo)
        else:
            tool_helper.install_spec(req)
    ret = 0
    if spec.build_script() is None:
        ret = cmake_build(ctx.obj.repo_root, arch, spec.build_type(), goal, verbose, spec.build_vars())
    else:
        for s in spec.build_script():
            if verbose:
                click.echo(str(s))
            ret = subprocess.call(str(s), shell=True)
            if ret:
                click.echo("Error {} exited with code {}".format(str(s), ret))
                break
    return ret