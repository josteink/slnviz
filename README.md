
# slnviz

slnviz is a command-line utility to help visualize Visual Studio and
msbuild build-dependencies and graphs.


## features

slnviz in a nutshell:

- command-line driven
- exports a [GraphViz](http://graphviz.org/) DOT-file from a visual studio SLN-file.
- highlights projects with dependencies which are not found in solution.
- ability to filter redundant transistive dependencies.
- ability to exclude certain kinds of project (test, shared, etc) from
  graph.

## dependencies

### python

slnviz is written in Python and targets python 3. No additional modules needs to
be installed.

It seems to work with python 2.7 too, but that's not a supported target.

### graphviz

If you want to visualize the graph, you need to have
[GraphViz](http://graphviz.org/) installed, or use a online service
like [viz-js](http://viz-js.com/).

## usage

The following example shows how to slnviz is intended to be used:

````sh
git clone https://github.com/josteink/slnviz
cd slnviz
./slnviz.py -i ../your_repo/your_solution.sln -o your_solution.dot
dot -Tsvg -o your_solution.svg your_solution.dot
# open svg-file in your preferred viewer
````

To list all parameters use the `-h` flag:

````sh
./slnviz.py -h
````
