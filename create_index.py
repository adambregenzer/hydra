#!/usr/bin/env python

import sys, os
from struct import unpack
from xml.etree.cElementTree import Element, ElementTree, SubElement

if len(sys.argv) < 5:
    print "Usage: create_index.py <type> <description> <out file> <in file[s]>\n"
    exit()

group_type = sys.argv[1]
group_description = sys.argv[2]
xml_out = open(sys.argv[3], 'w')

xmltree = ElementTree(Element('fileGroup', {'type': group_type, 'description': group_description}))
xmlroot = xmltree.getroot()

for path in sys.argv[4:]:
    record_count = os.path.getsize(path) - 266
    file = open(path, 'r')
    magic, description, file_order, record_size = unpack('!L256sLH', file.read(266))
    record_count /= record_size
    SubElement(xmlroot, 'file', {
        'src': path,
        'file_order': str(file_order),
        'description': str(description).rstrip('\00'),
        'record_size': str(record_size),
        'record_count': str(record_count)
    })

xml_out.write('<?xml version="1.0" encoding="utf-8"?>')
xmltree.write(xml_out, 'utf-8')
