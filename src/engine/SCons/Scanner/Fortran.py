"""SCons.Scanner.Fortran

This module implements the dependency scanner for Fortran code. 

"""

#
# Copyright (c) 2001, 2002 Steven Knight
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
# KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__revision__ = "__FILE__ __REVISION__ __DATE__ __DEVELOPER__"


import copy
import os.path
import re

import SCons.Node
import SCons.Node.FS
import SCons.Scanner
import SCons.Util
import SCons.Warnings

include_re = re.compile("INCLUDE[ \t]+'([\\w./\\\\]+)'", re.M)

def FortranScan(fs = SCons.Node.FS.default_fs):
    """Return a prototype Scanner instance for scanning source files
    for Fortran INCLUDE statements"""
    scanner = SCons.Scanner.Recursive(scan, "FortranScan", fs,
                                      [".f", ".F", ".for", ".FOR"])
    return scanner

def scan(node, env, target, fs = SCons.Node.FS.default_fs):
    """
    scan(node, Environment) -> [node]

    the Fortran dependency scanner function

    This function is intentionally simple. There are two rules it
    follows:
    
    1) #include <foo.h> - search for foo.h in F77PATH followed by the
        directory 'filename' is in
    2) #include \"foo.h\" - search for foo.h in the directory 'filename' is
       in followed by F77PATH

    These rules approximate the behaviour of most C/C++ compilers.

    This scanner also ignores #ifdef and other preprocessor conditionals, so
    it may find more depencies than there really are, but it never misses
    dependencies.
    """

    # This function caches various information in node and target:
    # target.f77path - env['F77PATH'] converted to nodes
    # node.found_includes - include files found by previous call to scan, 
    #     keyed on f77path
    # node.includes - the result of include_re.findall()

    if not hasattr(target, 'f77path'):
        try:
            target.f77path = tuple(fs.Rsearchall(SCons.Util.mapPaths(env['F77PATH'], target.cwd), clazz=SCons.Node.FS.Dir))
        except KeyError:
            target.f77path = ()

    f77path = target.f77path

    nodes = []

    node = node.rfile()
    try:
        nodes = node.found_includes[f77path]
    except KeyError:
        if node.rexists():

            # cache the includes list in node so we only scan it once:
            if node.includes != None:
                includes = node.includes
            else:
                includes = include_re.findall(node.get_contents())
                node.includes = includes

            source_dir = node.get_dir()
            
            for include in includes:
                n = SCons.Node.FS.find_file(include,
                                            (source_dir,) + f77path,
                                            fs.File)
                if not n is None:
                    nodes.append(n)
                else:
                    SCons.Warnings.warn(SCons.Warnings.DependencyWarning,
                                        "No dependency generated for file: %s (included from: %s) -- file not found" % (include, node))
        node.found_includes[f77path] = nodes

    # Schwartzian transform from the Python FAQ Wizard
    def st(List, Metric):
        def pairing(element, M = Metric):
            return (M(element), element)
        def stripit(pair):
            return pair[1]
        paired = map(pairing, List)
        paired.sort()
        return map(stripit, paired)

    def normalize(node):
        # We don't want the order of includes to be 
        # modified by case changes on case insensitive OSes, so
        # normalize the case of the filename here:
        # (see test/win32pathmadness.py for a test of this)
        return SCons.Node.FS._my_normcase(str(node))

    return st(nodes, normalize)
