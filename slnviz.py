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

def get_unix_path(file):
    return file.replace("\\", "/")


solution_path = "."

def set_working_basedir(sln_file):
    global solution_path
    solution_path = get_directory(get_unix_path(sln_file))
    print("Base-solution dir set to {0}".format(solution_path))

project_reference_declaration = re.compile("{(.*)}")

class Project(object):
    def __init__(self, name, filename, id):
        self.name = name
        self.filename = filename
        self.id = id
        self.dependant_ids = []

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
        print("--Project {0}-- Scanning dependencies...".format(self.name))
        if not os.path.isfile(xml_proj):
            print("--Project {0}-- Couldn't open project-file '{1}'".format(self.name, xml_proj))
            return []
        
        xml_doc = ET.parse(xml_proj).getroot()
        nodes = self.get_project_references(xml_doc)
        ids = self.get_project_ids(nodes)
        return ids

    
    def apply_declared_project_dependencies(self):
        ids = self.get_declared_project_dependency_ids()
        print("--Project {0}-- Found {1} dependencies in project file.".format(self.name, len(ids)))
        for id in ids:
            print("--Project {0}-- Adding dependency to project {1}.".format(self.name, id))
            self.add_dependency(id)    


def get_project_by_id(projects, id):
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
                
    return projects


def render_dot_file(projects):
    lines = []

    lines.append("digraph {")
    lines.append("    rankdir=\"TB\"")
    lines.append("")

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
        for id in project.dependant_ids:
            proj2 = get_project_by_id(projects, id)
            if proj2 is None:
                print("WARNING: Unable to resolve dependency with ID {0} for project {1}".format(id, project.name))
            else:
              proj2_id = proj2.get_friendly_id()
              lines.append("    {0} -> {1}".format(proj1_id, proj2_id))
    
    lines.append("")
    lines.append("}")
    
    return "\n".join(lines)


def get_directory(file):
    unix_file = get_unix_path(file)
    return os.path.split(unix_file)[0]


def process(sln_file, dot_file):
    set_working_basedir(sln_file)
    lines = get_lines_from_file(sln_file)
    projects = analyze_projects_in_solution(lines)
    txt = render_dot_file(projects)
    
    with open(dot_file, 'w') as f:
        f.write(txt)


def main():
    p = ArgumentParser()
    p.add_argument("--input", "-i", help="The file to analyze.")
    p.add_argument("--output", "-o", help="The file to write to.")

    args = p.parse_args()
    process(args.input, args.output)
    

# don't run from unit-tests
if __name__ == "__main__":
    main()
