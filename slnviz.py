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

debug_output = False
def debug(txt):
    global debug_output
    if debug_output:
        print(txt)
        
def get_unix_path(file):
    return file.replace("\\", "/")


solution_path = "."

def get_directory(file):
    unix_file = get_unix_path(file)
    return os.path.split(unix_file)[0]

def set_working_basedir(sln_file):
    global solution_path
    solution_path = get_directory(get_unix_path(sln_file))
    debug("Base-solution dir set to {0}".format(solution_path))


project_reference_declaration = re.compile("{(.*)}")

class Project(object):
    def __init__(self, name, filename, id):
        self.name = name
        self.filename = filename
        self.id = id
        self.dependant_ids = []
        self.dependant_projects = []
        self.missing_project_ids = []
        self.has_missing_projects = False

    def filter_id(self, id):
        return id.replace("-", "")

    def get_friendly_id(self):
        return self.name.replace(".", "_").replace("-","_")

    def add_dependency(self, id):
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
              if "Project" in elem.tag:
                  match = project_reference_declaration.match(elem.text)
                  if match:
                      result.append(match.groups()[0].upper())
        return result
        
    def get_declared_project_dependency_ids(self):
        xml_proj = self.get_full_project_file_path()
        if not os.path.isfile(xml_proj):
            print("--Project {0}-- Couldn't open project-file '{1}'".format(self.name, xml_proj))
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
                self.has_missing_projects = True
                self.missing_project_ids.append(id)
            else:
                self.dependant_projects.append(project)

    def remove_transitive_dependencies(self):
        # if A depends on B & C, and
        # B also depends on C, then
        # A has a transitive dependency on C through B.
    
        # This is a dependency which can be eliminated to clean up the graph.
        
        # clone list to have separate object to work on
        project_deps = self.dependant_projects[:]
        for dep in self.dependant_projects:
            nested_deps = dep.get_nested_dependencies()

            for nested_dep in nested_deps:
                if nested_dep in project_deps:
                    project_deps.remove(nested_dep)

        eliminated_deps = len(self.dependant_projects) - len(project_deps)
        if eliminated_deps != 0:
            debug("--Project {0}-- Eliminated {1} transitive dependencies. Was {2}. Reduced to {3}".format(self.name, eliminated_deps, len(self.dependant_projects), len(project_deps)))
            for removee in self.dependant_projects:
                if removee not in project_deps:
                    debug("--Project {0}-- Removed dependency: {1}".format(self.name, removee.name))

        self.dependant_projects = project_deps

    def get_nested_dependencies(self):
        total_deps = self.dependant_projects

        for dep in self.dependant_projects:
            dep_deps = dep.get_nested_dependencies()
            for dep_dep in dep_deps:
                if dep_dep not in total_deps:
                    total_deps.append(dep_dep)

        return total_deps


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


project_declaration = re.compile("\s*Project\(\"{.*}\"\) = \"(.*)\", \"(.*)\", \"{(.*)}\"")
project_dependency_declaration = re.compile("\s*{(.*)} = {(.*)}")


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
                
    return projects


def remove_transitive_dependencies(projects):
    for project in projects:
        project.remove_transitive_dependencies()

        
def render_dot_file(projects):
    lines = []

    lines.append("digraph {")
    lines.append("    rankdir=\"TB\"")
    lines.append("")
    lines.append("# project declarations")

    # define projects
    # create nodes like this
    #  A [ label="First Node" shape="circle" ]
    for project in projects:
        id = project.get_friendly_id()
        lines.append("    {0} [ label=\"{1}\" ]".format(id, project.name))

    # apply dependencies
    lines.append("")
    for project in projects:
        proj1_id = project.get_friendly_id()
        for proj2 in project.dependant_projects:
            if proj2 is None:
                print("WARNING: Unable to resolve dependency with ID {0} for project {1}".format(id, project.name))
            else:
              proj2_id = proj2.get_friendly_id()
              lines.append("    {0} -> {1}".format(proj1_id, proj2_id))
    
    lines.append("")
    lines.append("}")
    
    return "\n".join(lines)


def process(sln_file, dot_file, keep_deps):
    set_working_basedir(sln_file)
    lines = get_lines_from_file(sln_file)
    projects = analyze_projects_in_solution(lines)

    if not keep_deps:
        remove_transitive_dependencies(projects)
        
    txt = render_dot_file(projects)
    
    with open(dot_file, 'w') as f:
        f.write(txt)

    print("Wrote output-file '{0}'.".format(dot_file))


def main():
    global debug_output
    
    p = ArgumentParser()
    p.add_argument("--input", "-i", help="The file to analyze.")
    p.add_argument("--output", "-o", help="The file to write to.")
    p.add_argument("--keep-declared-deps", "-k", action="store_true", help="Don't remove redundant, transisitive dependencies in post-processing.")
    p.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    args = p.parse_args()

    debug_output = args.verbose
    
    process(args.input, args.output, args.keep_declared_deps)
    

# don't run from unit-tests
if __name__ == "__main__":
    main()
