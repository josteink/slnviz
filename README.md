
# slnviz

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

The following example shows how to slnviz is intended to be used:

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
