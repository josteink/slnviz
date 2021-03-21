
# slnviz

![CI](https://github.com/josteink/slnviz/workflows/CI/badge.svg)

slnviz is a command-line utility to help visualize Visual Studio and
msbuild build-dependencies and graphs.


## features

slnviz in a nutshell:

- command-line driven.
- exports a [GraphViz](http://graphviz.org/) DOT-file from a Visual Studio SLN-file.
- highlights projects whose dependencies are not found in the solution.
- ability to filter redundant transistive dependencies.
- ability to exclude certain kinds of projects (test, shared, etc) from
  graph.
- ability to highlight specific projects, and dependency-paths in the graph.

## dependencies

### python

slnviz is written in Python and targets Python 3. No additional modules needs to
be installed.

It seems to work with Python 2.7 as well, but that's not a supported target.

### graphviz

If you want to visualize the graph, you need to have
[GraphViz](http://graphviz.org/) installed, or use a online service
like [viz-js](http://viz-js.com/).

## usage

The following example shows how slnviz is intended to be used:

````sh
git clone https://github.com/josteink/slnviz
cd slnviz
./slnviz.py -i ../your_repo/your_solution.sln -o your_solution.dot
dot -Tsvg -o your_solution.svg your_solution.dot
# open svg-file in your preferred viewer
````

To list all parameters and options use the `-h` flag:

````sh
./slnviz.py -h
````

## themes
The output can be themed with the `--theme`  parameter. The default theme is `dark`.  

Supported themes are:

* dark (default)
* light

### style attributes

With the parameter ` --style attribute value` the dot rendering can be modified. These attributes override the definitions in the theme, so you can combine the usage of `--theme` and `--style` to tweak existing themes to your preference.

### supported style attrbutes
The following attributes are supported:

| Attribute name                         | Description                                                  | Default value |
| -------------------------------------- | ------------------------------------------------------------ | ------------- |
| bgcolor                                | Diagram background color.                                    | `#222222`     |
| project.linecolor                      | Line color for projects.                                     | `#ffffff`     |
| project.fontcolor                      | Font color for projects.                                     | `#ffffff`     |
| project.highlight.style                | Fill style for projects matching the highlight expression.   | `filled`      |
| project.highlight.fillcolor            | Fill color for projects matching the highlight expression.   | `#30c2c2`     |
| project.highlight.fontcolor            | Font color for projects matching the highlight expression.   | `#000000`     |
| project.highlight.linecolor            | Line color for projects matching the highlight expression.   | `#000000`     |
| dependency.color                       | Dependency line color.                                       | `#ffffff`     |
| project.is_missing_project.style       | Fill style for missing projects.                             | `filled`      |
| project.is_missing_project.fillcolor   | Fill color for missing projects.                             | `#f22430`     |
| project.is_missing_project.fontcolor   | Font color for missing projects.                             | `#000000`     |
| project.is_missing_project.linecolor   | Line color for missing projects.                             | `#000000`     |
| project.has_missing_projects.style     | Fill style for projects that have dependencies on missing projects. | `filled`      |
| project.has_missing_projects.fillcolor | Fill color for projects that have dependencies on missing projects. | `#c2c230`     |
| project.has_missing_projects.fontcolor | Font color for projects that have dependencies on missing projects. | `#000000`     |
| project.has_missing_projects.linecolor | Line color for projects that have dependencies on missing projects. | `#000000`     |



