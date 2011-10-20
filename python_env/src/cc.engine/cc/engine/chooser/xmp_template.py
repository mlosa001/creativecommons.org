import string
import re

from cc.i18n.gettext_i18n import ugettext_for_locale
from cc.i18n.util import locale_to_lower_lower


WORK_FORMATS = {
    'Other': None,
    'Audio': 'Sound',
    'Video': 'MovingImage',
    'Image': 'StillImage',
    'Interactive': 'InteractiveResource'}

ANCHOR_START_RE = re.compile("""\<a .+ href=["'].+["']\>""", re.I)
ANCHOR_END_RE = re.compile("""</a>""", re.I)


def strip_href(input_str):
    """Take input_str and strip out the <a href='...'></a> tags."""
    result = ANCHOR_START_RE.sub("", input_str)
    result = ANCHOR_END_RE.sub("", result)

    return result


def workType(format):
    if format == "":
        return "work"

    if format not in WORK_FORMATS:
        return format

    return WORK_FORMATS[format] 


def get_xmp_info(request_form, license, locale):
    ugettext = ugettext_for_locale(locale)

    # assemble the necessary information for the XMP file before rendering
    year = ('field_year' in request_form and
            request_form['field_year']) or ""
    creator = ('field_creator' in request_form and
               request_form['field_creator']) or None
    work_type = workType(('field_format' in request_form and
                          request_form['field_format']) or "")
    work_url = ('field_url' in request_form and
                request_form['field_url']) or None

    # determine the license notice
    if ('publicdomain' in license.uri):
        notice = "This %s is dedicated to the public domain." % (work_type)
        copyrighted = False
    else:
        if creator:
            notice = "Copyright %s %s.  " % (year, creator,)
        else:
            notice = ""

        i18n_work = ugettext('util.work')
        work_notice_template = string.Template(
            ugettext('license.work_type_licensed'))
        work_notice = work_notice_template.substitute(
            {'license_name': license.title(locale_to_lower_lower(locale)),
             'license_url': license.uri,
             'work_type': i18n_work})

        notice = notice + work_notice

        copyrighted = True

    return {
        'copyrighted': copyrighted,
        'notice':notice,
        'license_url':license.uri,
        'license':license,
        'work_url':work_url}


def license_xmp_template(request_form, license, locale):
    xmp_info = get_xmp_info(request_form, license, locale)
    xmp_output = u""

    def attrib_or_none(field_name):
        try:
            datum = request_form[field_name].strip()
            if datum:
                return datum
            else:
                # Blank strings count as a miss here.
                raise KeyError
        except KeyError:
            return None

    work_title = attrib_or_none("field_worktitle")
    attrib_name = attrib_or_none("field_attribute_to_name")
    attrib_url = attrib_or_none("field_attribute_to_url")
    
    # assemble the XMP
    xmp_output += u"""<?xpacket begin='' id=''?><x:xmpmeta xmlns:x='adobe:ns:meta/'>
    <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>

     <rdf:Description rdf:about=''
      xmlns:xapRights='http://ns.adobe.com/xap/1.0/rights/'>
      <xapRights:Marked>%(copyrighted)s</xapRights:Marked>""" % xmp_info

    if xmp_info['work_url'] != None:
        xmp_output += """  <xapRights:WebStatement rdf:resource='%(work_url)s'/>""" % xmp_info
        
    xmp_output += """ </rdf:Description>

     <rdf:Description rdf:about=''
      xmlns:dc='http://purl.org/dc/elements/1.1/'>
      <dc:rights>
       <rdf:Alt>\n"""

    language_line = "        <rdf:li xml:lang='{0}' >%(notice)s</rdf:li>\n"
    xmp_output += language_line.format(locale)
    if locale != 'en':
        xmp_output += language_line.format('en')

    xmp_output += """
       </rdf:Alt>
      </dc:rights>
     </rdf:Description>

     <rdf:Description rdf:about=''
      xmlns:cc='http://creativecommons.org/ns#'>
      <cc:license rdf:resource='%(license_url)s'/>
     </rdf:Description>\n"""

    if work_title:
        xmp_output += """
     <rdf:Description rdf:about='' xmlns:dc='http://purl.org/dc/elements/1.1/'>
      <dc:title>{0}</dc:title>
     </rdf:Description>\n""".format(work_title)

    if attrib_name:
        xmp_output += """
     <rdf:Description rdf:about='' xmlns:cc='http://creativecommons.org/ns#'>
      <cc:attributionName>{0}</cc:attributionName>
     </rdf:Description>\n""".format(attrib_name)
        
    if attrib_url:
        xmp_output += """
     <rdf:Description rdf:about='' 
      xmlns:xmpRights='http://ns.adobe.com/xap/1.0/rights/'>
      <xmlRights:WebStatement>{0}</xmlRights:WebStatement>
     </rdf:Description>\n""".format(attrib_url)

    xmp_output += """
    </rdf:RDF>
    </x:xmpmeta>
    <?xpacket end='r'?>
    """

    return xmp_output % xmp_info
