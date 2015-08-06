"""Entry point for all the extensions. Each new extension should be hooked up
here with an appropriate command name."""

import extensions.bld_formatter
import extensions.bump_mvn_version
import extensions.dep_tree
import extensions.pom_builder
import extensions.setup_eclipse_project


# Dictionary of all the extension commands.
# <Command Name> : (<Handler Function>, <One line help message>)
EXTENSION_COMMANDS = {
    'bld_format': ('_handle_bld_format', 'check and format BLD file(s)'),
    'build_pom': ('_handle_build_pom', 'generate pom.xml file for java rules'),
    'bump_mvn_version': ('_handle_bump_mvn_version',
                         'update maven rule version in a given BLD file'),
    'dep_tree': ('_handle_dep_tree', 'prints dependency tree for given rule'),
    'setup_eclipse_project': ('_handle_setup_eclipse_project',
                              'creates metadata files for eclipse project')
}


def _handle_bld_format(program_name, params, _):
  """Handler function for bld_format command."""
  return extensions.bld_formatter.main(program_name, params)


def _handle_build_pom(program_name, params, _):
  """Handler function for build_pom command."""
  return extensions.pom_builder.main(program_name, params)


def _handle_bump_mvn_version(program_name, params, _):
  """Handler function for bump_mvn_version command."""
  return extensions.bump_mvn_version.main(program_name, params)


def _handle_dep_tree(program_name, params, _):
  """Handler function for dep_tree command."""
  return extensions.dep_tree.main(program_name, params)


def _handle_setup_eclipse_project(program_name, params, _):
  """Handler function for setup_eclipse_project command."""
  return extensions.setup_eclipse_project.main(program_name, params)


def generic_extension_handler(params, dependency_dict):
  """Generic extension handler visible outside."""
  handler = globals()[EXTENSION_COMMANDS[params[0]][0]]
  return handler('bu {}'.format(params[0]), params[1:], dependency_dict)
