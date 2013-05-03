#!/usr/bin/env python
#
# Module for handling SCons documentation processing.
#

__doc__ = """
This module parses home-brew XML files that document various things
in SCons.  Right now, it handles Builders, functions, construction
variables, and Tools, but we expect it to get extended in the future.

In general, you can use any DocBook tag in the input, and this module
just adds processing various home-brew tags to try to make life a
little easier.

Builder example:

    <builder name="BUILDER">
    <summary>
    This is the summary description of an SCons Builder.
    It will get placed in the man page,
    and in the appropriate User's Guide appendix.
    The name of any builder may be interpolated
    anywhere in the document by specifying the
    &b-BUILDER;
    element.  It need not be on a line by itself.

    Unlike normal XML, blank lines are significant in these
    descriptions and serve to separate paragraphs.
    They'll get replaced in DocBook output with appropriate tags
    to indicate a new paragraph.

    <example>
    print "this is example code, it will be offset and indented"
    </example>
    </summary>
    </builder>

Function example:

    <scons_function name="FUNCTION">
    <arguments>
    (arg1, arg2, key=value)
    </arguments>
    <summary>
    This is the summary description of an SCons function.
    It will get placed in the man page,
    and in the appropriate User's Guide appendix.
    The name of any builder may be interpolated
    anywhere in the document by specifying the
    &f-FUNCTION;
    element.  It need not be on a line by itself.

    Unlike normal XML, blank lines are significant in these
    descriptions and serve to separate paragraphs.
    They'll get replaced in DocBook output with appropriate tags
    to indicate a new paragraph.

    <example>
    print "this is example code, it will be offset and indented"
    </example>
    </summary>
    </scons_function>

Construction variable example:

    <cvar name="VARIABLE">
    <summary>
    This is the summary description of a construction variable.
    It will get placed in the man page,
    and in the appropriate User's Guide appendix.
    The name of any construction variable may be interpolated
    anywhere in the document by specifying the
    &t-VARIABLE;
    element.  It need not be on a line by itself.

    Unlike normal XML, blank lines are significant in these
    descriptions and serve to separate paragraphs.
    They'll get replaced in DocBook output with appropriate tags
    to indicate a new paragraph.

    <example>
    print "this is example code, it will be offset and indented"
    </example>
    </summary>
    </cvar>

Tool example:

    <tool name="TOOL">
    <summary>
    This is the summary description of an SCons Tool.
    It will get placed in the man page,
    and in the appropriate User's Guide appendix.
    The name of any tool may be interpolated
    anywhere in the document by specifying the
    &t-TOOL;
    element.  It need not be on a line by itself.

    Unlike normal XML, blank lines are significant in these
    descriptions and serve to separate paragraphs.
    They'll get replaced in DocBook output with appropriate tags
    to indicate a new paragraph.

    <example>
    print "this is example code, it will be offset and indented"
    </example>
    </summary>
    </tool>
"""

import imp
import os.path
import re
import sys

# Do we have libxml2/libxslt/lxml?
has_libxml2 = True
try:
    import libxml2
    import libxslt
except:
    has_libxml2 = False
    try:
        import lxml
    except:
        print("Failed to import either libxml2/libxslt or lxml")
        sys.exit(1)

has_etree = False
if not has_libxml2:
    try:
        from lxml import etree
        has_etree = True
    except ImportError:
        pass
if not has_etree:
    try:
        # Python 2.5
        import xml.etree.cElementTree as etree
    except ImportError:
        try:
            # Python 2.5
            import xml.etree.ElementTree as etree
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as etree
            except ImportError:
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as etree
                except ImportError:
                    print("Failed to import ElementTree from any known place")
                    sys.exit(1)

re_entity = re.compile("\&([^;]+);")
re_entity_header = re.compile("<!DOCTYPE\s+sconsdoc\s+[^\]]+\]>")

# Namespace for the SCons Docbook XSD
dbxsd="http://www.scons.org/dbxsd/v1.0"
# Namespace for schema instances
xsi = "http://www.w3.org/2001/XMLSchema-instance"

# Header comment with copyright
copyright_comment = """
__COPYRIGHT__

This file is processed by the bin/SConsDoc.py module.
See its __doc__ string for a discussion of the format.
"""
# Header comment for automatically generated files
generated_comment = """
    THIS IS AN AUTOMATICALLY-GENERATED FILE.  DO NOT EDIT.
  """

def isSConsXml(fpath):
    """ Check whether the given file is a SCons XML file, i.e. it
        contains the default target namespace definition.
    """
    try:
        f = open(fpath,'r')
        content = f.read()
        f.close()
        if content.find(dbxsd) >= 0:
            return True
    except:
        pass
    
    return False 

def xml_tree(root, comment=generated_comment):
    """ Return a XML file tree with the correct namespaces set,
        the element root as top entry and the given header comment.
    """
    NSMAP = {None: dbxsd,
             'xsi' : xsi}

    t = etree.Element(root,
                      nsmap = NSMAP,
                      attrib = {"{"+xsi+"}schemaLocation" : "%s scons.xsd" % dbxsd})

    c = etree.Comment(comment)
    t.append(c)

    return t

def remove_entities(content):
    # Cut out entity inclusions
    content = re_entity_header.sub("", content, re.M)
    # Cut out entities themselves
    content = re_entity.sub(lambda match: match.group(1), content)
    
    return content

default_xsd = os.path.join('doc','xsd','scons.xsd')

ARG = "dbscons"

class Libxml2ValidityHandler:
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        
    def error(self, msg, data):
        if data != ARG:
            raise Exception, "Error handler did not receive correct argument"
        self.errors.append(msg)

    def warning(self, msg, data):
        if data != ARG:
            raise Exception, "Warning handler did not receive correct argument"
        self.warnings.append(msg)

def validate_xml(fpath, xmlschema_context):
    if not has_libxml2:
        # Use lxml
        xmlschema = etree.XMLSchema(xmlschema_context)
        doc = etree.parse(fpath)
        doc.xinclude()
        try:
            xmlschema.assertValid(doc)
        except Exception, e:
            print e
            print "%s fails to validate" % fpath
            return False
        return True

    # Create validation context
    validation_context = xmlschema_context.schemaNewValidCtxt()
    # Set error/warning handlers
    eh = Libxml2ValidityHandler()
    validation_context.setValidityErrorHandler(eh.error, eh.warning, ARG)
    # Read file and resolve entities
    doc = libxml2.readFile(fpath, None, libxml2.XML_PARSE_NOENT)
    doc.xincludeProcessFlags(libxml2.XML_PARSE_NOENT)
    err = validation_context.schemaValidateDoc(doc)
    # Cleanup
    doc.freeDoc()
    del validation_context

    if err or eh.errors:
        for e in eh.errors:
            print e.rstrip("\n")
        print "%s fails to validate" % fpath
        return False
        
    return True

def prettyprint_xml(fpath):
    if not has_libxml2:
        # Use lxml
        fin = open(fpath,'r')
        tree = etree.parse(fin)
        pretty_content = etree.tostring(tree, pretty_print=True)
        fin.close()

        fout = open(fpath,'w')
        fout.write(pretty_content)
        fout.close()

    # Read file and resolve entities
    doc = libxml2.readFile(fpath, None, libxml2d.XML_PARSE_NOENT)
    err = xmlschema_context.schemaValidateDoc(doc)
    # Cleanup
    doc.freeDoc()
    

perc="%"

def validate_all_xml(dpaths, xsdfile=default_xsd):
    xmlschema_context = None
    if not has_libxml2:
        # Use lxml
        xmlschema_context = etree.parse(xsdfile)
    else:
        # Use libxml2 and prepare the schema validation context
        ctxt = libxml2.schemaNewParserCtxt(xsdfile)
        xmlschema_context = ctxt.schemaParse()
        del ctxt
    
    fpaths = []
    for dp in dpaths:
        for path, dirs, files in os.walk(dp):
            for f in files:
                if f.endswith('.xml'):
                    fp = os.path.join(path, f)
                    if isSConsXml(fp):
                        fpaths.append(fp)
                
    fails = []
    for idx, fp in enumerate(fpaths):
        fpath = os.path.join(path, f)
        print "%.2f%s (%d/%d) %s" % (float(idx+1)*100.0/float(len(fpaths)),
                                     perc, idx+1, len(fpaths),fp)
                                              
        if not validate_xml(fp, xmlschema_context):
            fails.append(fp)
            continue

    if has_libxml2:
        # Cleanup
        del xmlschema_context

    if fails:
        return False
    
    return True

class Item(object):
    def __init__(self, name):
        self.name = name
        self.sort_name = name.lower()
        if self.sort_name[0] == '_':
            self.sort_name = self.sort_name[1:]
        self.summary = []
        self.sets = []
        self.uses = []
    def cmp_name(self, name):
        if name[0] == '_':
            name = name[1:]
        return name.lower()
    def __cmp__(self, other):
        return cmp(self.sort_name, other.sort_name)

class Builder(Item):
    pass

class Function(Item):
    def __init__(self, name):
        super(Function, self).__init__(name)

class Tool(Item):
    def __init__(self, name):
        Item.__init__(self, name)
        self.entity = self.name.replace('+', 'X')

class ConstructionVariable(Item):
    pass

class Chunk(object):
    def __init__(self, tag, body=None):
        self.tag = tag
        if not body:
            body = []
        self.body = body
    def __str__(self):
        body = ''.join(self.body)
        return "<%s>%s</%s>\n" % (self.tag, body, self.tag)
    def append(self, data):
        self.body.append(data)

class Arguments(object):
    def __init__(self, signature, body=None):
        if not body:
            body = []
        self.body = body
        self.signature = signature
    def __str__(self):
        s = ''.join(self.body).strip()
        result = []
        for m in re.findall('([a-zA-Z/_]+|[^a-zA-Z/_]+)', s):
            if ' ' in m:
                m = '"%s"' % m
            result.append(m)
        return ' '.join(result)
    def append(self, data):
        self.body.append(data)

class SConsDocHandler(object):
    def __init__(self):
        self.builders = {}
        self.functions = {}
        self.tools = {}
        self.cvars = {}

    def parseText(self, root):
        txt = ""
        for e in root.childNodes:
            if (e.nodeType == e.TEXT_NODE):
                txt += e.data
        return txt

    def parseItems(self, domelem):
        items = []

        for i in domelem.iterchildren(tag="item"):
            items.append(self.parseText(i))

        return items

    def parseUsesSets(self, domelem):
        uses = []
        sets = []

        for u in domelem.iterchildren(tag="uses"):
            uses.extend(self.parseItems(u))
        for s in domelem.iterchildren(tag="sets"):
            sets.extend(self.parseItems(s))
        
        return sorted(uses), sorted(sets)

    def parseInstance(self, domelem, map, Class):
        name = domelem.attrib.get('name','unknown')
        try:
            instance = map[name]
        except KeyError:
            instance = Class(name)
            map[name] = instance
        uses, sets = self.parseUsesSets(domelem)
        instance.uses.extend(uses)
        instance.sets.extend(sets)
        # Parse summary and function arguments
        for s in domelem.iterchildren(tag="{%s}summary" % dbxsd):
            if not hasattr(instance, 'summary'):
                instance.summary = []
            for c in s:
                instance.summary.append(c)
        for a in domelem.iterchildren(tag="{%s}arguments" % dbxsd):
            if not hasattr(instance, 'arguments'):
                instance.arguments = []
            instance.arguments.append(a)

    def parseDomtree(self, root):    
        # Process Builders
        for b in root.iterchildren(tag="{%s}builder" % dbxsd):
            self.parseInstance(b, self.builders, Builder)
        # Process Functions
        for f in root.iterchildren(tag="{%s}scons_function" % dbxsd):
            self.parseInstance(f, self.functions, Function)
        # Process Tools
        for t in root.iterchildren(tag="{%s}tool" % dbxsd):
            self.parseInstance(t, self.tools, Tool)
        # Process CVars
        for c in root.iterchildren(tag="{%s}cvar" % dbxsd):
            self.parseInstance(c, self.cvars, ConstructionVariable)
        
    def parseContent(self, content, include_entities=True):
        if not include_entities:
            content = remove_entities(content)
        # Create domtree from given content string
        root = etree.fromstring(content)
        # Parse it
        self.parseDomtree(root)

    def parseXmlFile(self, fpath):
        # Create domtree from file
        domtree = etree.parse(fpath)
        # Parse it
        self.parseDomtree(domtree.getroot())

    def set_file_info(self, filename, preamble_lines):
        self.filename = filename
        self.preamble_lines = preamble_lines

# lifted from Ka-Ping Yee's way cool pydoc module.
def importfile(path):
    """Import a Python source file or compiled file given its path."""
    magic = imp.get_magic()
    file = open(path, 'r')
    if file.read(len(magic)) == magic:
        kind = imp.PY_COMPILED
    else:
        kind = imp.PY_SOURCE
    file.close()
    filename = os.path.basename(path)
    name, ext = os.path.splitext(filename)
    file = open(path, 'r')
    try:
        module = imp.load_module(name, file, path, (ext, 'r', kind))
    except ImportError, e:
        sys.stderr.write("Could not import %s: %s\n" % (path, e))
        return None
    file.close()
    return module

# Local Variables:
# tab-width:4
# indent-tabs-mode:nil
# End:
# vim: set expandtab tabstop=4 shiftwidth=4:
