#!/usr/bin/env python
# coding: utf-8

"""
    Base document tree emitter
    ~~~~~~~~~~~~~~~~~~~~~~~~~~


    :copyleft: 2008-2011 by python-creole team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""

import posixpath

from creole.html_parser.config import BLOCK_TAGS
from creole.html_tools.deentity import Deentity
from creole.shared.markup_table import MarkupTable
from creole.shared.unknown_tags import transparent_unknown_nodes


class BaseEmitter(object):
    """
    Build from a document_tree (html2creole.parser.HtmlParser instance) a
    creole markup text.
    """
    def __init__(self, document_tree, unknown_emit=transparent_unknown_nodes, debug=False):
        self.root = document_tree

        self._unknown_emit = unknown_emit

        self.last = None
        self.debugging = debug

        self.deentity = Deentity() # for replacing html entities
        self._inner_list = ""
        self._mask_linebreak = False

    #--------------------------------------------------------------------------

    def blockdata_pass_emit(self, node):
        return u"%s\n\n" % node.content
        return node.content

    #--------------------------------------------------------------------------

    def data_emit(self, node):
        #node.debug()
        return node.content

    def entityref_emit(self, node):
        """
        emit a named html entity
        """
        entity = node.content

        try:
            return self.deentity.replace_named(entity)
        except KeyError, err:
            if self.debugging:
                print "unknown html entity found: %r" % entity
            return "&%s" % entity # FIXME
        except UnicodeDecodeError, err:
            raise UnicodeError(
                "Error handling entity %r: %s" % (entity, err)
            )

    def charref_emit(self, node):
        """
        emit a not named html entity
        """
        entity = node.content

        if entity.startswith("x"):
            # entity in hex
            hex_no = entity[1:]
            return self.deentity.replace_hex(hex_no)
        else:
            # entity as a unicode number
            return self.deentity.replace_number(entity)

    #--------------------------------------------------------------------------

    def p_emit(self, node):
        return u"%s\n\n" % self.emit_children(node)

    def br_emit(self, node):
        if self._inner_list != "":
            return u"\\\\"
        else:
            return u"\n"

    #--------------------------------------------------------------------------

    def _typeface(self, node, key):
        return key + self.emit_children(node) + key


    #--------------------------------------------------------------------------

    def li_emit(self, node):
        content = self.emit_children(node)
        return u"\n%s %s" % (self._inner_list, content)

    def _list_emit(self, node, list_type):
        start_newline = False
        if self.last and self.last.kind not in BLOCK_TAGS:
            if not self.last.content or not self.last.content.endswith("\n"):
                start_newline = True

        if self._inner_list == "": # Start a new list
            self._inner_list = list_type
        else:
            start = False
            self._inner_list += list_type

        content = u"%s" % self.emit_children(node)

        self._inner_list = self._inner_list[:-1]

        if self._inner_list == "": # Start a new list
            if start_newline:
                return "\n" + content + "\n\n"
            else:
                return content.strip() + "\n\n"
        else:
            return content

    #--------------------------------------------------------------------------

    def table_emit(self, node):
        self._table = MarkupTable(
            head_prefix=self.table_head_prefix,
            auto_width=self.table_auto_width,
            debug_msg=self.debug_msg
        )
        self.emit_children(node)
        content = self._table.get_table_markup()
        return u"%s\n" % content

    def tr_emit(self, node):
        self._table.add_tr()
        content = self.emit_children(node)
        return u""

    def _escape_linebreaks(self, text):
        text = text.strip()
        text = text.split("\n")
        lines = [line.strip() for line in text]
        lines = [line for line in lines if line]
        content = u"\\\\".join(lines)
        content = content.strip("\\")
        return content

    def th_emit(self, node):
        content = self.emit_children(node)
        content = self._escape_linebreaks(content)
        self._table.add_th(content)
        return u""

    def td_emit(self, node):
        content = self.emit_children(node)
        content = self._escape_linebreaks(content)
        self._table.add_td(content)
        return u""

    #--------------------------------------------------------------------------

    def _emit_content(self, node):
        content = self.emit_children(node)
        content = self._escape_linebreaks(content)
        if node.kind in BLOCK_TAGS:
            content = u"%s\n\n" % content
        return content

    def div_emit(self, node):
        return self._emit_content(node)

    def span_emit(self, node):
        return self._emit_content(node)

    #--------------------------------------------------------------------------

    def document_emit(self, node):
        self.last = node
        return self.emit_children(node)

    def emit_children(self, node):
        """Emit all the children of a node."""
        self.last = node
        result = []
        for child in node.children:
            content = self.emit_node(child)
            assert isinstance(content, unicode)
            result.append(content)
        return u"".join(result)
        #~ return u''.join([self.emit_node(child) for child in node.children])

    def emit_node(self, node):
        """Emit a single node."""
        def unicode_error(method_name, method, node, content):
            node.debug()
            raise AssertionError(
                "Method '%s' (%s) returns no unicode - returns: %s (%s)" % (
                    method_name, method, repr(content), type(content)
                )
            )

        self.debug_msg("emit_node", "%s: %r" % (node.kind, node.content))

        method_name = "%s_emit" % node.kind
        emit_method = getattr(self, method_name, None)

        if emit_method:
            content = emit_method(node)
            if not isinstance(content, unicode):
                unicode_error(method_name, emit_method, node, content)
        else:
            content = self._unknown_emit(self, node)
            if not isinstance(content, unicode):
                unicode_error(method_name, self._unknown_emit, node, content)

        self.last = node
        return content

    def emit(self):
        """Emit the document represented by self.root DOM tree."""
        result = self.emit_node(self.root)
        return result.strip() # FIXME

    #-------------------------------------------------------------------------

    def debug_msg(self, method, txt):
        if not self.debugging:
            return
        print "%13s: %s" % (method, txt)
