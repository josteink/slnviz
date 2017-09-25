import unittest
import slnviz

class Tests(unittest.TestCase):
    def test_parse_project_declaration_regexp(self):
        decl = "	Project(\"{2150E333-8FDC-42A3-9474-1A3956D46DE8}\") = \"License\", \"License\", \"{A96EA6A0-2464-416D-8E69-3A06A7288A60}\""
        m = slnviz.project_declaration.match(decl)

        self.assertNotEqual(None, m)
        [name, id] = m.groups()
        self.assertEqual("License", name)
        self.assertEqual("A96EA6A0-2464-416D-8E69-3A06A7288A60", id)

    def test_parse_project_dependency_regexp(self):
        decl = "		{62AB4DC9-9913-4686-9F66-4BD3F4C7B119} = {62AB4DC9-9913-4686-9F66-4BD3F4C7B119}"
        
        m = slnviz.project_dependency_declaration.match(decl)

        self.assertNotEqual(None, m)
        [id1, id2] = m.groups()
        self.assertEqual(id1, id2)
        self.assertEqual("62AB4DC9-9913-4686-9F66-4BD3F4C7B119", id1)

    def test_parse_solution_contents(self):
        decl = """    Project("{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}") = "MakeDistribution", "Clients\CS\MakeDistribution\MakeDistribution.vcxproj", "{2E668CA6-63BC-4F85-8D9D-5287D80C7D6B}"
        ProjectSection(ProjectDependencies) = postProject
    {5A1B76E3-A314-4956-A50F-45475A5F330A} = {5A1B76E3-A314-4956-A50F-45475A5F330A}
        EndProjectSection
                Project("{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}") = "Admin", "Clients\CS\www\admin\Admin.vcxproj", "{5A1B76E3-A314-4956-A50F-45475A5F330A}"
        EndProject"""

        lines = decl.split("\n")
        projs = slnviz.analyze_projects_in_solution(lines)

        self.assertEqual(2, len(projs))
