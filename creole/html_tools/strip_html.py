#!/usr/bin/env python
# coding: utf-8


"""
    python-creole utils
    ~~~~~~~~~~~~~~~~~~~    


    :copyleft: 2008-2011 by python-creole team, see AUTHORS for more details.
    :license: GNU GPL v3 or above, see LICENSE for more details.
"""


import re

from creole.html_parser.config import BLOCK_TAGS


strip_html_regex = re.compile(
    r"""
        \s*
        <
            (?P<end>/{0,1})       # end tag e.g.: </end>
            (?P<tag>[^ >]+)       # tag name
            .*?
            (?P<startend>/{0,1})  # closed tag e.g.: <closed />
        >
        \s*
    """,
    re.VERBOSE | re.MULTILINE | re.UNICODE
)



def strip_html(html_code):
    """
    Delete whitespace from html code. Doesn't recordnize preformatted blocks!

    >>> strip_html(u' <p>  one  \\n two  </p>')
    u'<p>one two</p>'

    >>> strip_html(u'<p><strong><i>bold italics</i></strong></p>')
    u'<p><strong><i>bold italics</i></strong></p>'

    >>> strip_html(u'<li>  Force  <br /> \\n linebreak </li>')
    u'<li>Force<br />linebreak</li>'

    >>> strip_html(u'one  <i>two \\n <strong>   \\n  three  \\n  </strong></i>')
    u'one <i>two <strong>three</strong> </i>'

    >>> strip_html(u'<p>a <unknown tag /> foobar  </p>')
    u'<p>a <unknown tag /> foobar</p>'

    >>> strip_html(u'<p>a <pre> preformated area </pre> foo </p>')
    u'<p>a<pre>preformated area</pre>foo</p>'
    
    FIXME:
    >>> strip_html(u'<strong>foo</strong>\\n<ul><li>one</li></ul>')
    u'<strong>foo</strong><ul><li>one</li></ul>'
    """

    def strip_tag(match):
        block = match.group(0)
        end_tag = match.group("end") in ("/", u"/")
        startend_tag = match.group("startend") in ("/", u"/")
        tag = match.group("tag")

#        print "_"*40
#        print match.groupdict()
#        print "block.......: %r" % block
#        print "end_tag.....:", end_tag
#        print "startend_tag:", startend_tag
#        print "tag.........: %r" % tag

        if tag in BLOCK_TAGS:
            return block.strip()

        space_start = block.startswith(" ")
        space_end = block.endswith(" ")

        result = block.strip()

        if end_tag:
            # It's a normal end tag e.g.: </strong>
            if space_start or space_end:
                result += " "
        elif startend_tag:
            # It's a closed start tag e.g.: <br />

            if space_start: # there was space before the tag
                result = " " + result

            if space_end: # there was space after the tag
                result += " "
        else:
            # a start tag e.g.: <strong>
            if space_start or space_end:
                result = " " + result

        return result

    data = html_code.strip()
    clean_data = " ".join([line.strip() for line in data.split("\n")])
    clean_data = strip_html_regex.sub(strip_tag, clean_data)
    return clean_data


if __name__ == '__main__':
    import doctest
    print doctest.testmod()
