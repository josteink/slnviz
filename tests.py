import unittest
import slnviz

class Tests(unittest.TestCase):
    def test_parse_project_declaration_regexp(self):
        decl = "	Project(\"{2150E333-8FDC-42A3-9474-1A3956D46DE8}\") = \"License\", \"License\", \"{A96EA6A0-2464-416D-8E69-3A06A7288A60}\""
        m = slnviz.project_declaration.match(decl)

        self.assertNotEqual(None, m)
        [name, filename, id] = m.groups()
        self.assertEqual("License", name)
        self.assertEqual("License", filename)
        self.assertEqual("A96EA6A0-2464-416D-8E69-3A06A7288A60", id)

    def test_parse_project_dependency_regexp(self):
        decl = "		{62AB4DC9-9913-4686-9F66-4BD3F4C7B119} = {62AB4DC9-9913-4686-9F66-4BD3F4C7B119}"
        
        m = slnviz.project_dependency_declaration.match(decl)

        self.assertNotEqual(None, m)
        [id1, id2] = m.groups()
        self.assertEqual(id1, id2)
        self.assertEqual("62AB4DC9-9913-4686-9F66-4BD3F4C7B119", id1)

    def test_parse_solution_contents(self):
        decl = """
Project("{2150E333-8FDC-42A3-9474-1A3956D46DE8}") = "DCF", "DCF", "{E6CAB0B1-AB81-40E4-9F7B-E777B2A706DE}"
EndProject
        Project("{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}") = "MakeDistribution", "Clients\CS\MakeDistribution\MakeDistribution.vcxproj", "{2E668CA6-63BC-4F85-8D9D-5287D80C7D6B}"
        ProjectSection(ProjectDependencies) = postProject
    {5A1B76E3-A314-4956-A50F-45475A5F330A} = {5A1B76E3-A314-4956-A50F-45475A5F330A}
        EndProjectSection
                Project("{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}") = "Admin", "Clients\CS\www\admin\Admin.vcxproj", "{5A1B76E3-A314-4956-A50F-45475A5F330A}"
        EndProject"""

        lines = decl.split("\n")
        projs = slnviz.analyze_projects_in_solution(lines)

        self.assertEqual(2, len(projs))

        self.assertEqual("Admin", projs[0].name)
        self.assertEqual(0, len(projs[0].dependant_ids))
        self.assertEqual("MakeDistribution", projs[1].name)
        self.assertEqual(1, len(projs[1].dependant_ids))

    def test_project_id(self):

        proj = slnviz.Project("SuperOffice.Test.Name", "stn.csproj", "123-234-345")

        self.assertEqual("SuperOffice_Test_Name", proj.get_friendly_id())

    def test_graphviz_output(self):
        proj1 = slnviz.Project("Project.SO.Main", "psomain.csproj", "123-234")
        proj2 = slnviz.Project("Project.SO.Installer", "psoinstaller.vcxproj", "234-345")

        proj1.add_dependency(proj2.id);

        txt = slnviz.render_dot_file([proj1, proj2])

        # has no trace of dotted IDs
        self.assertEqual(True, "Project_SO_Main" in txt)
        self.assertEqual(True, "Project_SO_Installer" in txt)

        # has proper labels
        self.assertEqual(True, "label=\"Project.SO.Main\"" in txt)

    def test_eliminate_dependencies(self):
        a = slnviz.Project("A", "A.csproj", "A")
        b = slnviz.Project("B", "B.csproj", "B")
        c = slnviz.Project("C", "C.csproj", "C")
        d = slnviz.Project("D", "D.csproj", "D")

        a.dependant_projects = [b,c,d]
        b.dependant_projects = [c,d]
        c.dependant_projects = [d]

        a.remove_transitive_dependencies()
        b.remove_transitive_dependencies()
        c.remove_transitive_dependencies()

        self.assertEqual([b], a.dependant_projects)
        self.assertEqual([c], b.dependant_projects)
        self.assertEqual([d], c.dependant_projects)

    def test_dependency_chains(self):
        a = slnviz.Project("A", "A.csproj", "A")
        b = slnviz.Project("B", "B.csproj", "B")
        c = slnviz.Project("C", "C.csproj", "C")
        d = slnviz.Project("D", "D.csproj", "D")

        a.dependant_projects = [b]
        b.dependant_projects = [c]
        c.dependant_projects = [d]

        all_deps = a.get_nested_dependencies()
        self.assertEqual([b,c,d], all_deps)
        
