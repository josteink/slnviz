#!/usr/bin/python3

#
# slnviz
# a tool to convert a Visual Studio sln-file into a
# graphviz dot-file, for easy dependency analysis
#

from argparse import ArgumentParser
import re


class Project(object):
    def __init__(self, name, id):
        self.name = name
        self.id = id
        self.dependant_ids = []

    def filter_id(self, id):
        return id.replace("-", "")

    def get_friendly_id(self):
        return self.name.replace(".", "_").replace("-","_")

    def add_dependency(self, id):
        self.dependant_ids.append(id)


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


project_declaration = re.compile("\s*Project\(\"{.*}\"\) = \"(.*)\", \".*\", \"{(.*)}\"")
project_dependency_declaration = re.compile("\s*{(.*)} = {(.*)}")


def analyze_projects_in_solution(lines):

    projects = []
    current_project = None

    for line in lines:

        m = project_declaration.match(line)
        if m is not None:
            [name, id] = m.groups()
            current_project = Project(name, id)
            projects.append(current_project)

        m = project_dependency_declaration.match(line)
        if m is not None:
            [id1, id2] = m.groups()
            # sanity-check: should be same value!
            if id1 == id2:
                current_project.add_dependency(id1)

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
            proj2_id = proj2.get_friendly_id()
            lines.append("    {0} -> {1}".format(proj1_id, proj2_id))
    
    lines.append("")
    lines.append("}")
    
    return "\n".join(lines)


def process(sln_file, dot_file):
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
