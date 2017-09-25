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

    def get_friendly_id(self):
        return self.id.replace("-", "")
        
# todo:
# - process one line at a time
# - detect delimiters
#   - Project declaration
#
#   Project("{2150E333-8FDC-42A3-9474-1A3956D46DE8}") = "License", "License", "{A96EA6A0-2464-416D-8E69-3A06A7288A60}"
#                                                        Name                   ID
#
#   - Project Dependency
#
# 	ProjectSection(ProjectDependencies) = postProject
#		{62AB4DC9-9913-4686-9F66-4BD3F4C7B119} = {62AB4DC9-9913-4686-9F66-4BD3F4C7B119}
#       EndProjectSection
#
# - build it all

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
                current_project.dependant_ids.append(id1)
            
    return projects


def render_dot_file(projects):
    # TODO
    return


def process(sln_file, dot_file):
    lines = get_lines_from_file(sln_file)
    projects = analyze_solution(lines)
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
