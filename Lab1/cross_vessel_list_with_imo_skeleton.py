#!/usr/bin/python3
"""
NPR, 01/2019

This module extracts pieces of information from a RDF/XML document that describes a collection of ship properties, and crosses it with a CSV list of IMO vessel codes.
To run it:

	* ensure that the two input files :download:`imo-vessel-codes.csv <imo-vessel-codes.csv>` and :download:`ICES_vessel_sample.xml <ICES_vessel_sample.xml>` are in the current work directory 
	* then execute the script without any parameters: the tests take care of calling the appropriate functions with the correct arguments

-----------
INPUT:
-----------

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(a) A CSV list of vessel codes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:download:`imo-vessel-codes.csv <imo-vessel-codes.csv>`

.. code-block:: python

	imo,mmsi,name,flag,type
	9116462,1073727001,"AEGEANQUE EN",,"Passengers Ship"
	9116462,1072678425,"AEGEQNQUE EN",,"Passengers Ship"
	9700940,1028641360,"IVQ!PC=NDA  O0  O0",,Cargo
	9116462,1073727001,"AEGEANQUE EN",,"Passengers Ship"
	...

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
(b) An XML collection of ship descriptions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
:download:`ICES_vessel_sample.xml <ICES_vessel_sample.xml>`

.. code-block:: xml
	:emphasize-lines: 15, 17, 35, 37-42

	<?xml version="1.0" encoding="UTF-8"?><?xml-stylesheet href="/VocabV2/skosrdf2html.xsl" type="text/xsl" media="screen"?><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:skos="http://www.w3.org/2004/02/skos/core#" xmlns:dc="http://purl.org/dc/terms/" xmlns:dce="http://purl.org/dc/elements/1.1/" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#" xmlns:grg="http://www.isotc211.org/schemas/grg/" xmlns:owl="http://www.w3.org/2002/07/owl#" xmlns:void="http://rdfs.org/ns/void#" xmlns:pav="http://purl.org/pav/">
	<skos:Collection rdf:about="http://vocab.nerc.ac.uk/collection/C17/current/">
	<skos:prefLabel>ICES Platform Codes</skos:prefLabel>
	...
	<dc:creator>International Council for the Exploration of the Sea</dc:creator>
	<grg:RE_RegisterOwner>International Council for the Exploration of the Sea</grg:RE_RegisterOwner>
	<rdfs:comment>International organisation with a mission to advance the scientific capacity to give advice on human activities affecting, and affected by, marine ecosystems. Secretariat is located in Copenhagen.</rdfs:comment>

	<skos:member>
	<skos:Concept rdf:about="http://vocab.nerc.ac.uk/collection/C17/current/90UW/">
	<dc:identifier>SDN:C17::90UW</dc:identifier>
	<dce:identifier>SDN:C17::90UW</dce:identifier>
	<dc:date>2012-02-07 09:42:36.0</dc:date>
	<skos:notation>SDN:C17::90UW</skos:notation>
	<skos:prefLabel xml:lang="en">11TH Pjatiletka</skos:prefLabel>
	<skos:altLabel/>
	<skos:definition xml:lang="en">OCL REQUEST</skos:definition>
	<owl:versionInfo>2</owl:versionInfo>
	<pav:hasCurrentVersion rdf:resource="http://vocab.nerc.ac.uk/collection/C17/current/90UW/2/"/>
	<pav:version>2</pav:version>
	<pav:authoredOn>2012-02-07 09:42:36.0</pav:authoredOn>
	<skos:note xml:lang="en">deprecated</skos:note>
	<owl:deprecated>true</owl:deprecated>
	<dc:isReplacedBy rdf:resource="http://vocab.nerc.ac.uk/collection/C17/current/ZZ99/"/>
	<void:inDataset rdf:resource="http://vocab.nerc.ac.uk/.well-known/void"/>
	</skos:Concept>
	</skos:member>
	...
	<skos:member>
	<skos:Concept rdf:about="http://vocab.nerc.ac.uk/collection/C17/current/3234/">
	<dc:identifier>SDN:C17::3234</dc:identifier>
	<dce:identifier>SDN:C17::3234</dce:identifier>
	<dc:date>2015-12-16 13:28:25.0</dc:date>
	<skos:notation>SDN:C17::3234</skos:notation>
	<skos:prefLabel xml:lang="en">2nd Lt. John P.Bobo</skos:prefLabel>
	<skos:altLabel/>
	<skos:definition xml:lang="en">{
	  "country": "United States",
	  "platformclass": "naval vessel",
	  "IMO": "8219384",
	  "callsign": "NBOB"
	}</skos:definition>
	<owl:versionInfo>4</owl:versionInfo>
	<pav:hasCurrentVersion rdf:resource="http://vocab.nerc.ac.uk/collection/C17/current/3234/4/"/>
	<pav:version>4</pav:version>
	<pav:authoredOn>2015-12-16 13:28:25.0</pav:authoredOn>
	<skos:note xml:lang="en">accepted</skos:note>
	<owl:deprecated>false</owl:deprecated>
	<skos:broader rdf:resource="http://vocab.nerc.ac.uk/collection/L06/current/39/"/>
	<void:inDataset rdf:resource="http://vocab.nerc.ac.uk/.well-known/void"/>
	</skos:Concept>
	</skos:member>
	</skos:Collection>
	</rdf:RDF>

------------
OUTPUT:
------------

No console, or file output. For testing purpose, the main procedure just returns a structure of type `set`. Each element of
the set is a 3-tuple::

		(<IMO number>, <vessel name>, <vessel MMSI>)

where

		* the vessel name is the text element ``<skos:prefLabel>``, a child node of ``<skos:Concept>``
		* the vessel's IMO number is the value of property ``IMO`` in the JSON text content of element ``<skos:definition>``, also a child node of ``<skos:Concept>``.

Looking at the relevant test case will give you a better view of the data structure to be returned

"""
import sys
import os
import xml.dom.minidom
from xml.dom.minidom import parse, parseString
import json
import unittest
import csv
import xml.etree.ElementTree as ET


def extract_imo(imo_filename):
    """
	.. _extract_imo:

	Read a list of vessel characteristics, and map the IMO numbers to the MMSIs.

	.. todo::

		1. Create an empty dictionary object (``dict`` type or ``{}``)
		2. Open the file whose name is given as a parameter
		3. Read it line by line (but skip the headers)
		4. For each line, extract the first two fields: IMO number, and MMSI, respectively.
		5. Create a corresponding entry in the table created in (1), using the IMO number as the key, and the MMSI as the value.
		6. When done reading the file, return the dictionary


	.. note::
		
		The CSV file might contain more than 1 entry for each IMO number. Your table should store only the last one. The input 
		file has about 64000 records; the resulting dictionary should contain about 58000 entries.

	:param imo_filename: the input file, where each line contains the CSV fields below::

		<IMO #>,<MMSI>,<NAME>,<FLAG>,<TYPE>

		E.g::

			9116462,1073727001,"AEGEANQUE EN",,"Passengers Ship"
	:type imo_filename: str
	:return: a dictionary object (i.e. a hash table) with the IMO number strings as keys, and the MMSI strings as value. E.g. for the ship above, the dictionary entry for IMO number '816993991' should be ``mytable['816993991']='1073727001'``.
	:rtype: dict

	"""
    directory = {}

    with open(imo_filename) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            directory[row[0]] = row[1]
    return directory


def extract_ship_properties(imo_filename, xml_vessel_filename):
    """
	.. _extract_ship_properties:

	From a list of ship identifiers (first parameter), build a table that associate IMO numbers to MMSIs. Then extract from the XML list of  vessels (second parameter) those ships that have a valid IMO number in the first table, in order to construct a set of vessel tuples.

	The function uses the DOM to access the elements of interest, and the `json` module to process the 
	embedded JSON strings. 

	.. todo::

		1.  Call the extract_imo_ procedure to retrieve the table of valid IMO numbers
		2. Initialize an empty Python set object
		3. Load the document into a DOM object
		4. Use the DOM API to access each ship's description (elements ``<skos:Concept>``) and from there
			
			* the vessel's name (the text content of a ``<skos:prefLabel>`` element). Careful: ``<skos:prefLabel>`` elements can be found in two places of the XML tree, i.e. (i) as the child node of the ``<skos:Collection>`` element (the parent of all vessel descriptions) (ii) as a child of a ``<skos:Concept>`` element. Only the second kind of occurrence labels a ship's name.
			* the vessel's definition, i.e. the text content of the``<skos:definition>`` element

		5. Use the ``json`` module to parse the ship's definition, and extract the value of key ``IMO`` (*if provided*)
		6. Check that the IMO number retrieved in (4) does exist in the table of IMO numbers returned by the extract_imo_ function
		7. If it does exist (by only if so), add to the result set the following 3-tupple: (<IMO number>, <ship name>, <ship MMSI>), where the MMSI is to be found in the table of IMO numbers (under the IMO key)
		

	.. note:: 

		The following ships should *not* be included in the result set:

			* vessels that do not have a valid JSON definition
			* vessels whose definition does not have a field for the IMO number
			* vessels whose IMO number does not have a match in the list of IMO numbers retrieved in  extract_imo_ 

		Be careful using the provided get_text_ procedure to retrieve the content of the text nodes for a given element.

	:param imo_filename: the name of the input CSV list of vessel codes
	:type imo_filename: str
	:param xml_vessel_filename: the name of the input RDF/XML document, describing a collection of ship definitions.
	:type xml_vessel_filename: str
	:return: a set of 3-tuples of the form ``(<IMO number>, <ship name>, <ship MMSI>)``.
	:rtype: set
	"""
    dictionary = extract_imo(imo_filename)
    new_set = set()
    dom = xml.dom.minidom.parse(xml_vessel_filename)
    try:
        dom = xml.dom.minidom.parse(xml_vessel_filename)
    except (EnvironmentError, xml.parsers.expat.ExpatError) as err:
        print(f"{0}: import error: {1}".format(os.path.basename(sys.argv[0]), err))
    for member in dom.getElementsByTagName("skos:Concept"):
        vessel_name = get_text(member.getElementsByTagName("skos:prefLabel")[0])
        # print(vessel_name)
        # if get_text(member.getElementsByTagName("skos:definition")[0]) != :
        definition = get_text(member.getElementsByTagName("skos:definition")[0])
        print(definition)
        # definition = json.loads(definition)




def get_text(element):
    """
	.. _get_text:

	Helper function that extracts, and concatenates the text nodes of a given element, to be returned as a single string.


	:param element: a DOM element
	:type: xml.dom.minidom.Element
	:return: a concatenation of all textual nodes of the given element.
	:rtype: str
	"""
    text = []
    for child in element.childNodes:
        if child.nodeType == child.TEXT_NODE:
            text.append(child.data)
    return "".join(text).strip()


class TestExtraction(unittest.TestCase):
    imo_vessel_codes = 'imo-vessel-codes.csv'
    sample_vessel_database = 'ICES_vessel_sample.xml'

    # sample_vessel_database='international_council_exploration_seas_vessel_database.xml'

    def test_1_get_text(self):
        dom = xml.dom.minidom.parseString("""<?xml version="1.0" encoding="UTF-8"?>
					<bigFish>Moby Dick</bigFish>""")
        self.assertEqual(get_text(dom.childNodes[0]), 'Moby Dick')

    def test_2_extract_imo_length(self):
        """ Test that all imo numbers have been stored """
        valid_imos = extract_imo(self.imo_vessel_codes)

        self.assertEqual(len(valid_imos.items()), 58666)

    def test_3_extract_imo_pairs(self):
        """ Test that the mapping is correct (2 random pairs)"""

        valid_imos = extract_imo(self.imo_vessel_codes)

        self.assertEqual(valid_imos['9315513'], '366947110')
        self.assertEqual(valid_imos['9081174'], '351667000')

    def test_4_extract_ship_properties_is_set(self):
        """ Test that ship extraction returns a set """

        ship_properties = extract_ship_properties('imo-vessel-codes.csv', self.sample_vessel_database)
        self.assertEqual(type(ship_properties), set)

    def test_5_extract_ship_properties_is_set_of_tuples(self):
        """ Test that ship extraction returns a set of tuples """

        ship_properties = extract_ship_properties('imo-vessel-codes.csv', self.sample_vessel_database)
        self.assertTrue(type(ship) is tuple for ship in ship_properties)

    def test_6_extract_ship_properties_is_set_of_3_tuples(self):
        """ Test that ship extraction returns a set of 3-tuples """

        ship_properties = extract_ship_properties('imo-vessel-codes.csv', self.sample_vessel_database)
        self.assertTrue(type(ship) is tuple and len(ship) == 3 for ship in ship_properties)

    def test_7_extract_ship_properties_numbers(self):
        """ Test that all ship IMO numbers have been extracted, as first element of every 3-tuple in the set"""

        ship_properties = extract_ship_properties('imo-vessel-codes.csv', self.sample_vessel_database)

        self.assertEqual(set([ship[0] for ship in ship_properties]), set(
            ['9324863', '9139749', '9155391', '9593488', '9324837', '9334820', '9532795', '9334155', '9214898',
             '9326794', '9324849', '9334167', '6711883', '9218650', '9225407', '9218686', '9139713', '9139725',
             '9461879', '8219384', '9461867', '9074389']))

    def test_8_extract_ship_properties_numbers_names(self):
        """ Test that ship IMO numbers and ship name have been extracted, as first, second elements of every 3-tuple in the set"""

        ship_properties = extract_ship_properties('imo-vessel-codes.csv', self.sample_vessel_database)

        self.assertEqual(set([(ship[0], ship[1]) for ship in ship_properties]), set(
            [('9324863', 'ANL Warrain'), ('9139749', 'APL Coral'), ('9155391', 'ANL Echuca'), ('9593488', 'AM Tubarao'),
             ('9324837', 'ANL Warringa'), ('9334820', 'ANL Elanora'), ('9532795', 'APL Antwerp'),
             ('9334155', 'ANL Wyong'), ('9214898', 'A. P. Moller'), ('9326794', 'ANL Waratah'),
             ('9324849', 'ANL Windarra'), ('9334167', 'ANL Wangaratta'), ('6711883', 'A. V. Humboldt'),
             ('9218650', 'APL England'), ('9225407', 'ANL Kiewa'), ('9218686', 'APL Belgium'), ('9139713', 'APL Agate'),
             ('9139725', 'APL Cyprine'), ('9461879', 'APL Gwangyang'), ('8219384', '2nd Lt. John P.Bobo'),
             ('9461867', 'APL Chongquing'), ('9074389', 'APL China')]))

    def test_9_extract_ship_properties_numbers_names_mmsi(self):
        """ Test that ship IMO numbers, ship name, and MMSI have been extracted, as 3-tuple elements of the set"""

        ship_properties = extract_ship_properties('imo-vessel-codes.csv', self.sample_vessel_database)

        self.assertEqual(ship_properties,
                         {('9324863', 'ANL Warrain', '565997000'), ('9139749', 'APL Coral', '367478280'),
                          ('9155391', 'ANL Echuca', '636090756'), ('9593488', 'AM Tubarao', '636015171'),
                          ('9324837', 'ANL Warringa', '538002734'), ('9334820', 'ANL Elanora', '636091287'),
                          ('9532795', 'APL Antwerp', '351467000'), ('9334155', 'ANL Wyong', '235060306'),
                          ('9214898', 'A. P. Moller', '219882000'), ('9326794', 'ANL Waratah', '636091052'),
                          ('9324849', 'ANL Windarra', '538002733'), ('9334167', 'ANL Wangaratta', '235060679'),
                          ('6711883', 'A. V. Humboldt', '376404000'), ('9218650', 'APL England', '563722000'),
                          ('9225407', 'ANL Kiewa', '636092575'), ('9218686', 'APL Belgium', '367578740'),
                          ('9139713', 'APL Agate', '367403460'), ('9139725', 'APL Cyprine', '367403790'),
                          ('9461879', 'APL Gwangyang', '566319000'), ('8219384', '2nd Lt. John P.Bobo', '367049000'),
                          ('9461867', 'APL Chongquing', '566318000'), ('9074389', 'APL China', '369247000')})


def main():
    unittest.main()


if __name__ == '__main__':
    main()
