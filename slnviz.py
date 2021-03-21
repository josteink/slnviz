#!/usr/bin/python3

#
# slnviz
# a tool to convert a Visual Studio sln-file into a
# graphviz dot-file, for easy dependency analysis
#

from argparse import ArgumentParser
import re
import os
import xml.etree.ElementTree as ET
import enum

debug_output = False
solution_path = "."

project_reference_declaration = re.compile("{(.*)}")
project_declaration = re.compile("\s*Project\(\"{.*}\"\) = \"(.*)\", \"(.*)\", \"{(.*)}\"")
project_dependency_declaration = re.compile("\s*{(.*)} = {(.*)}")

# Available themes to select
themes = {
    'dark': {
        'bgcolor': '#222222',
        'project.linecolor': '#ffffff',
        'project.fontcolor': '#ffffff',
        'dependency.color': '#ffffff',

        'project.highlight.style': 'filled',
        'project.highlight.fillcolor': '#30c2c2',
        'project.highlight.linecolor': '#000000',
        'project.highlight.fontcolor': '#000000',

        'project.is_missing_project.style': 'filled',
        'project.is_missing_project.fillcolor': '#f22430',
        'project.is_missing_project.linecolor': '#000000',
        'project.is_missing_project.fontcolor': '#000000',

        'project.has_missing_projects.style': 'filled',
        'project.has_missing_projects.fillcolor': '#c2c230',
        'project.has_missing_projects.linecolor': '#000000',
        'project.has_missing_projects.fontcolor': '#000000',
    },
    'light': {
        'bgcolor': '#ffffff',
        'project.linecolor': '#222222',
        'project.fontcolor': '#222222',
        'dependency.color': '#222222',

        'project.highlight.style': 'filled',
        'project.highlight.fillcolor': '#30c2c2',
        'project.highlight.linecolor': '#222222',
        'project.highlight.fontcolor': '#222222',

        'project.is_missing_project.style': 'filled',
        'project.is_missing_project.fillcolor': '#f22430',
        'project.is_missing_project.linecolor': '#222222',
        'project.is_missing_project.fontcolor': '#222222',

        'project.has_missing_projects.style': 'filled',
        'project.has_missing_projects.fillcolor': '#c2c230',
        'project.has_missing_projects.linecolor': '#222222',
        'project.has_missing_projects.fontcolor': '#222222',
    }
}

# Apply default theme to the style attributes
style_attributes = themes['dark']

messages = []


@enum.unique
class MessageLevel(enum.Enum):
    # Note that the values can/will be used as output
    DEBUG = "DEBUG  "
    INFO = "INFO   "
    WARNING = "WARNING"
    ERROR = "ERROR  "


class Message:
    def __init__(self, level: MessageLevel, text: str):
        self.level = level
        self.text = text


def __log_message(message: Message):
    messages.append(message)
    print('{0}: {1}'.format(message.level.value, message.text))


def log_info(text: str):
    __log_message(Message(MessageLevel.INFO, text))


def log_warning(text: str):
    __log_message(Message(MessageLevel.WARNING, text))


def log_error(text: str):
    __log_message(Message(MessageLevel.ERROR, text))


def debug(txt):
    global debug_output
    if debug_output:
        __log_message(Message(MessageLevel.DEBUG, txt))


def get_unix_path(file):
    return file.replace("\\", "/")


def get_directory(file):
    unix_file = get_unix_path(file)
    return os.path.split(unix_file)[0]


def set_working_basedir(sln_file):
    global solution_path
    solution_path = get_directory(get_unix_path(sln_file))
    debug("Base-solution dir set to {0}".format(solution_path))


class Project(object):
    def __init__(self, name, filename, id):
        self.name = name
        self.filename = filename
        self.id = id
        self.dependant_ids = []
        self.dependant_projects = []
        self.declared_dependant_projects = []
        self.missing_project_ids = []
        self.has_missing_projects = False
        self.is_missing_project = False
        self.highlight = False

    def filter_id(self, id):
        return id.replace("-", "")

    def get_friendly_id(self):
        return self.name.replace(".", "_").replace("-", "_")

    def add_dependency(self, id):
        id = str.upper(id)
        if id not in self.dependant_ids:
            self.dependant_ids.append(id)

    def get_full_project_file_path(self):
        return os.path.join(solution_path, get_unix_path(self.filename))

    def get_project_references(self, xml_doc):
        nodes = []
        for elem in xml_doc.getiterator():
            if "ProjectReference" in elem.tag:
                nodes.append(elem)
        return nodes

    def get_project_ids(self, nodes):
        result = []
        for node in nodes:
            for elem in node.getiterator():
                if "Project" in elem.tag and elem.text:
                    match = project_reference_declaration.match(elem.text)
                    if match:
                        result.append(match.groups()[0].upper())
        return result

    def get_declared_project_dependency_ids(self):
        xml_proj = self.get_full_project_file_path()
        if not os.path.isfile(xml_proj):
            log_warning("--Project {0}-- Couldn't open project-file '{1}'".format(self.name, xml_proj))
            return []

        xml_doc = ET.parse(xml_proj).getroot()
        nodes = self.get_project_references(xml_doc)
        ids = self.get_project_ids(nodes)
        return ids

    def apply_declared_project_dependencies(self):
        ids = self.get_declared_project_dependency_ids()
        for id in ids:
            self.add_dependency(id)

    def resolve_projects_from_ids(self, projects):
        for id in self.dependant_ids:
            project = get_project_by_id(id, projects)
            if project is None:
                # track missing deps consistently
                missing_project_id = "Missing_" + id.replace("-", "")
                project = Project(missing_project_id, missing_project_id, id)
                project.is_missing_project = True
                projects.append(project)

            if project.is_missing_project:
                self.has_missing_projects = True
                self.missing_project_ids.append(id)

            self.dependant_projects.append(project)

        self.declared_dependant_projects = self.dependant_projects

    def remove_transitive_dependencies(self):
        # if A depends on B & C, and
        # B also depends on C, then
        # A has a transitive dependency on C through B.

        # This is a dependency which can be eliminated to clean up the graph.

        # clone list to have separate object to work on
        project_deps = self.dependant_projects[:]

        # investigate each direct sub-dependency as its own tree
        for dep in self.dependant_projects:

            # calculate all dependencies for this one tree
            nested_deps = dep.get_nested_dependencies()

            # check if any of those are direct dependencues
            for nested_dep in nested_deps:
                # if so, remove them
                if nested_dep in project_deps:
                    debug("--Project {0}-- Removed transitive dependency: {1} (via {2})".format(self.name, nested_dep.name, dep.name))
                    project_deps.remove(nested_dep)

        eliminated_deps = len(self.dependant_projects) - len(project_deps)
        if eliminated_deps != 0:
            debug("--Project {0}-- Eliminated {1} transitive dependencies. Was {2}. Reduced to {3}".format(self.name, eliminated_deps, len(self.dependant_projects), len(project_deps)))

        self.dependant_projects = project_deps

    def get_nested_dependencies(self):
        # clone to new list, don't modify the existing list!
        # that means -adding- dependencies when we want to remove them!
        total_deps = self.dependant_projects[:]

        for dep in self.dependant_projects:
            dep_deps = dep.get_nested_dependencies()
            for dep_dep in dep_deps:
                if dep_dep not in total_deps:
                    total_deps.append(dep_dep)

        return total_deps

    def has_highlighted_dependencies(self):
        allDeps = self.get_nested_dependencies()
        for dep in allDeps:
            if dep.highlight:
                return True
        return False

    def has_declared_highlighted_dependencies(self):
        declaredDeps = self.declared_dependant_projects
        for dep in declaredDeps:
            if dep.highlight:
                return True
        return False
        


def get_project_by_id(id, projects):
    for project in projects:
        if project.id == id:
            return project
    return None


def get_lines_from_file(file):
    with open(file, 'r') as f:
        contents = f.read()
        lines = contents.split("\n")
        return lines


def sort_projects(projects):
    projects.sort(key=lambda x: x.name)


def analyze_projects_in_solution(lines):

    projects = []
    current_project = None

    for line in lines:

        m = project_declaration.match(line)
        if m is not None:
            [name, filename, id] = m.groups()
            # solution folders are declared with a virtual filename, same as
            # node-name. ignore these entries!
            if name != filename:
                current_project = Project(name, filename, id)
                projects.append(current_project)

        m = project_dependency_declaration.match(line)
        if m is not None:
            [id1, id2] = m.groups()
            # sanity-check: should be same value!
            if id1 == id2:
                current_project.add_dependency(id1)

    # pull in dependencies declared in project-files
    for project in projects:
        project.apply_declared_project_dependencies()

    # all projects & dependencies should now be known. lets analyze them
    for project in projects:
        project.resolve_projects_from_ids(projects)

    # format results in a alphabetical order
    sort_projects(projects)
    for project in projects:
        sort_projects(project.dependant_projects)

    return projects


def remove_transitive_dependencies(projects):
    for project in projects:
        project.remove_transitive_dependencies()


def filter_projects(rx, projects):
    result = []

    for project in projects:
        if not rx.match(str.lower(project.name)):
            result.append(project)
        else:
            debug("Info: Excluding project {0}.".format(project.name))

    return result


def highlight_projects(rx, projects):
    for project in projects:
        if rx.match(str.lower(project.name)):
            debug("Highlighting project {0}".format(project.name))
            project.highlight = True


def render_dot_file(projects, highlight_all=False):
    lines = []

    lines.append("digraph {")
    lines.append("    rankdir=\"TB\"")
    lines.append("")
    lines.append("    # apply theme")
    lines.append("    bgcolor=\"{0}\"".format(style_attributes['bgcolor']))
    lines.append("")
    lines.append("    // defaults for edges and nodes can be specified")
    lines.append("    node [ color=\"{0}\" fontcolor=\"{1}\" ]".format(
        style_attributes['project.linecolor'],
        style_attributes['project.fontcolor']
    ))
    lines.append("    edge [ color=\"{0}\" ]".format(
        style_attributes['dependency.color']
    ))
    lines.append("")
    lines.append("    # project declarations")

    # define projects
    # create nodes like this
    #  A [ label="First Node" shape="circle" ]
    for project in projects:
        id = project.get_friendly_id()

        styling = ""
        if project.highlight:
            styling = " fillcolor=\"{0}\" style={1} color=\"{2}\" fontcolor=\"#000000\"".format(
                style_attributes['project.highlight.fillcolor'],
                style_attributes['project.highlight.style'],
                style_attributes['project.highlight.linecolor'],
                style_attributes['project.highlight.fontcolor']
            )
        elif project.is_missing_project:
            styling = " fillcolor=\"{0}\" style={1} color=\"{2}\" fontcolor=\"#000000\"".format(
                style_attributes['project.is_missing_project.fillcolor'],
                style_attributes['project.is_missing_project.style'],
                style_attributes['project.is_missing_project.linecolor'],
                style_attributes['project.is_missing_project.fontcolor']
            )
        elif project.has_missing_projects:
            styling = " fillcolor=\"{0}\" style={1} color=\"{2}\" fontcolor=\"#000000\"".format(
                style_attributes['project.has_missing_projects.fillcolor'],
                style_attributes['project.has_missing_projects.style'],
                style_attributes['project.has_missing_projects.linecolor'],
                style_attributes['project.has_missing_projects.fontcolor']
            )

        lines.append("    {0} [ label=\"{1}\" {2} ]".format(id, project.name, styling))

    # apply dependencies
    lines.append("")
    lines.append("    # project dependencies")
    for project in projects:
        proj1_id = project.get_friendly_id()
        for proj2 in project.dependant_projects:
            if proj2 is None:
                log_warning("Unable to resolve dependency with ID {0} for project {1}".format(id, project.name))
            else:
              proj2_id = proj2.get_friendly_id()
              styling = ""
              if proj2.highlight or proj2.has_declared_highlighted_dependencies() or (highlight_all and proj2.has_highlighted_dependencies()):
                  styling = " [color=\"{0}\"]".format(style_attributes['project.highlight.fillcolor'])
              elif proj2.is_missing_project or (project.has_missing_projects and proj2.has_missing_projects):
                  styling = " [color=\"{0}\"]".format(style_attributes['project.is_missing_project.fillcolor'])
              lines.append("    {0} -> {1}{2}".format(proj1_id, proj2_id, styling))

    lines.append("")
    lines.append("}")

    return "\n".join(lines)


def process(sln_file, dot_file, exclude, highlight, highlight_all, keep_deps):
    log_info("Parsing: {0}".format(sln_file))
    set_working_basedir(sln_file)
    lines = get_lines_from_file(sln_file)
    projects = analyze_projects_in_solution(lines)

    if not keep_deps:
        debug("Removing redundant dependencies...")
        remove_transitive_dependencies(projects)

    if exclude:
        debug("Excluding projects...")
        excluder = re.compile(str.lower(exclude))
        projects = filter_projects(excluder, projects)

    if highlight:
        debug("Highlighting projects...")
        highlighter = re.compile(str.lower(highlight))
        highlight_projects(highlighter, projects)

    txt = render_dot_file(projects, highlight_all)

    with open(dot_file, 'w') as f:
        f.write(txt)

    log_info("Wrote output-file '{0}'.".format(dot_file))


def set_style(theme, attributes):
    global style_attributes

    if not theme:
        theme = 'dark'

    debug("Using {0} theme".format(theme))
    style_attributes = themes[theme]

    if attributes:
        for attr in attributes:
            name, value = attr
            if name not in style_attributes:
                log_error("Unknown style attribute defined: {0}".format(name))
            else:
                debug("Overriding style {0}".format(name))
                style_attributes[name] = value


def write_logs(logfile: str, must_append: bool):
    if logfile:
        with open(logfile, "a" if must_append else "w") as log_file:
            log_file.writelines(["{0}:{1}\n".format(msg.level.value, msg.text) for msg in messages])


def main():
    global debug_output

    p = ArgumentParser()
    p.add_argument("--input", "-i", help="The file to analyze.")
    p.add_argument("--output", "-o", help="The file to write to.")
    p.add_argument("--keep-declared-deps", "-k", action="store_true",
                   help="Don't remove redundant, transisitive dependencies in post-processing.")
    p.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    p.add_argument("--exclude", "-e", help="Filter projects matching this expression from the graph")
    p.add_argument("--highlight", help="Highlights projects matching this expression in the graph")
    p.add_argument("--highlight-all", action="store_true", help="Highlight all paths leading to a highlighted project")

    p.add_argument("--theme", "-t", help="select one of the defined themes")
    p.add_argument("--style", "-s", action="append", nargs=2, metavar=("attribute", "value"),
                   help="Provide style information for dot rendering")
    p.add_argument("--log", "-l", help="Log events to file")
    p.add_argument("--logappend", "-la", action="store_true", help="Append logs to file")

    args = p.parse_args()

    debug_output = args.verbose

    set_style(args.theme, args.style)
    process(args.input, args.output, args.exclude, args.highlight, args.highlight_all, args.keep_declared_deps)
    write_logs(args.log, args.logappend)


# don't run from unit-tests
if __name__ == "__main__":
    main()
