#!/usr/bin/env python
#
# Copyright (c) 2001 Steven Knight
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

import TestSCons

test = TestSCons.TestSCons()

test.write('build.py', r"""
import sys
contents = open(sys.argv[2], 'r').read()
file = open(sys.argv[1], 'w')
file.write(contents)
file.close()
""")

test.write('SConstruct', """
env = Environment()
env.Command(target = 'f1.out', source = 'f1.in',
		action = "python build.py $target $sources")
env.Command(target = 'f2.out', source = 'f2.in',
		action = "python build.py temp2 $sources\\npython build.py $target temp2")
env.Command(target = 'f3.out', source = 'f3.in',
		action = ["python build.py temp3 $sources",
			  "python build.py $target temp3"])
# Eventually, add ability to do execute Python code.
""")

test.write('f1.in', "f1.in\n")

test.write('f2.in', "f2.in\n")

test.write('f3.in', "f3.in\n")

#XXXtest.run(arguments = '.')
test.run(arguments = 'f1.out f2.out f3.out')

test.fail_test(test.read('f1.out') != "f1.in\n")
test.fail_test(test.read('f2.out') != "f2.in\n")
test.fail_test(test.read('f3.out') != "f3.in\n")

test.pass_test()
