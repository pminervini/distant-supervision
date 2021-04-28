#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

import re
from os.path import join
from timeit import default_timer as timer
import xml.etree.ElementTree as ET
from zipfile import ZipFile

import logging

logger = logging.getLogger(os.path.basename(sys.argv[0]))


DDI_SIDE_EFFECT_1 = re.compile('The risk or severity of (?P<se>.*) can be (?P<mode>\S+)d when .* is combined with .*')
DDI_SIDE_EFFECT_2 = re.compile('.* may (?P<mode>\S+) (?P<se>\S+\s?\w*\s?\w*) of .* as a diagnostic agent.')
DDI_SIDE_EFFECT_3 = re.compile('The (?P<se>\S+\s?\w*\s?\w*) of .* can be (?P<mode>\S+)d when used in combination with .*')
DDI_SIDE_EFFECT_4 = re.compile('The (?P<se>\S+\s?\w*\s?\w*) of .* can be (?P<mode>\S+)d when it is combined with .*')
DDI_SIDE_EFFECT_5 = re.compile('.* can cause a decrease in the absorption of .* resulting in a (?P<mode>\S+) (?P<se>\S+\s?\w*\s?\w*) and potentially a decrease in efficacy.')
DDI_SIDE_EFFECT_6 = re.compile('.* may decrease the excretion rate of .* which could result in a (?P<mode>\S+) (?P<se>\S+\s?\w*\s?\w*).')
DDI_SIDE_EFFECT_7 = re.compile('.* may increase the excretion rate of .* which could result in a (?P<mode>\S+) (?P<se>\S+\s?\w*\s?\w*) and potentially a reduction in efficacy.')
DDI_SIDE_EFFECT_8 = re.compile('The (?P<se>\S+\s?\w*\s?\w*) of .* can be (?P<mode>\S+)d when combined with .*')
DDI_SIDE_EFFECT_9 = re.compile('.* can cause an increase in the absorption of .* resulting in an (?P<mode>\S+)d (?P<se>\S+\s?\w*\s?\w*) and potentially a worsening of adverse effects.')
DDI_SIDE_EFFECT_10 = re.compile('The risk of a (?P<se>\S+\s?\w*\s?\w*) to .* is (?P<mode>\S+)d when it is combined with .*')
DDI_SIDE_EFFECT_11 = re.compile('The (?P<se>\S+\s?\w*\s?\w*) of .* can be (?P<mode>\S+)d when combined with .*')
DDI_SIDE_EFFECT_12 = re.compile('The (?P<se>\S+\s?\w*\s?\w*) of the active metabolites of .* can be (?P<mode>\S+)d when .* is used in combination with .*')
DDI_SIDE_EFFECT_13 = re.compile('The (?P<se>\S+\s?\w*\s?\w*) of .*, an active metabolite of .* can be (?P<mode>\S+)d when used in combination with .*')
DDI_SIDE_EFFECT_14 = re.compile('.* may (?P<mode>\S+) the (?P<se>.*) of .*')
DDI_SIDE_EFFECT_15 = re.compile('.* may (?P<mode>\S+) the central nervous system depressant (?P<se>\S+\s?\S*\s?\S*) of .*')

DDI_SIDE_EFFECTS = [
    DDI_SIDE_EFFECT_1, DDI_SIDE_EFFECT_2, DDI_SIDE_EFFECT_3, DDI_SIDE_EFFECT_4,
    DDI_SIDE_EFFECT_5, DDI_SIDE_EFFECT_6, DDI_SIDE_EFFECT_7, DDI_SIDE_EFFECT_8,
    DDI_SIDE_EFFECT_9, DDI_SIDE_EFFECT_10, DDI_SIDE_EFFECT_11, DDI_SIDE_EFFECT_12,
    DDI_SIDE_EFFECT_13, DDI_SIDE_EFFECT_14, DDI_SIDE_EFFECT_15
]


DDI_MODE_MAP = {
    'reduced': "decrease",
    'increase': "increase",
    'higher': "increase",
    'decrease': "decrease",
    'reduce': "decrease",
    'lower': "decrease"
}

DDI_SE_NAME_MAP = {
    "central_nervous_system_depressant_(cns_depressant)_activities": 'cns_depression_activities',
    "(cns_depressant)_activities": 'cns_depression_activities',
    "cns_depression": 'cns_depression_activities',
    "cardiotoxic_activities": 'cardiotoxicity',
    "constipating_activities": 'constipation',
    "excretion": 'excretion_rate',
    "hyperkalemic_activities": 'hyperkalemia',
    "hypertensive_activities": 'hypertension',
    "qtc-prolonging_activities": "qtc_prolongation",
    "tachycardic_activities": "tachycardia",
    "hypokalemic_activities": "hypokalemia",
    "hypoglycemic_activities": "hypoglycemia",
    "hypercalcemic_activities": "hypercalcemia",
    "bradycardic_activities": "bradycardia",
    "neutropenic_activities": "neutropenia",
    "orthostatic_hypotensive_activities": "orthostatic_hypotension",
    "neutropenic_activities": "neutropenia",
    "pseudotumor_cerebri_activities": "pseudotumor_cerebri",
    "sedative_activities": "sedation",
    "ototoxic_activities": "ototoxicity",
    "neuromuscular_blocking_activities": "neuromuscular_blockade",
    "nephrotoxic_activities": "nephrotoxicity",
    "myelosuppressive_activities": "myelosuppression",
    "hypotensive_activities": "hypotension",
    "serum_level": "serum_concentration"
}


def sanatize_text(text):
    """ Replace non alphanumeric characters in text with '_'
    Parameters
    ----------
    text : str
        text to sanatize
    Returns
    -------
    text
        the sanatized text
    """
    if text is None:
        return text
    return re.sub('[^a-zA-Z0-9]', '_', text.strip())


def sanatize_se_txt(txt):
    return txt.strip().replace(" ", "_").lower()


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


program_header = "= Building the [" + bcolors.OKBLUE + "biokg" + bcolors.ENDC + "] knowledge graph"
dwn_sym = "(" + bcolors.FAIL + "⤓" + bcolors.ENDC + ") "
done_sym = " (" + bcolors.OKGREEN + "✓" + bcolors.ENDC + ")"
fail_sym = " (" + bcolors.FAIL + "✘" + bcolors.ENDC + ")"
prc_sym = "(" + bcolors.OKBLUE + "⏣" + bcolors.ENDC + ") "
hsh_sym = " (" + bcolors.OKBLUE + "#" + bcolors.ENDC + ") "
inf_sym = "(" + bcolors.WARNING + bcolors.BOLD + "‣" + bcolors.ENDC + ") "


def print_line():
    """ print stdout line
    """
    print("------------------------------------------------")


def print_section_header(header_txt):
    """
    Parameters
    ----------
    header_txt: str
        header text to print
    """
    print(">>>  %s ... " % header_txt)
    print_line()


class SetWriter:
    """
    Utility class for writing DrugBank statements
    Enforces uniqueness of statements between written between flushes
    Set clear_on_flush to false to enforce uniquness for on all writes
    (should not be set for very large datasets)
    """

    def __init__(self, path):
        """
        Initialize a new SetWriter
        Parameters
        ----------
        """
        self._lines = []
        self._lineset = set()
        self._fd = open(path, 'w')
        self._clear_on_flush = True
        self._closed = False

    @property
    def clear_on_flush(self):
        return self._clear_on_flush

    @clear_on_flush.setter
    def clear_on_flush(self, value):
        self._clear_on_flush = value

    def write(self, line):
        if self._closed:
            raise ValueError('I/O operation on closed file')

        if line in self._lineset:
            return
        self._lineset.add(line)
        self._lines.append(line)

    def flush(self):
        if self._closed:
            raise ValueError('I/O operation on closed file')
        self._fd.writelines(self._lines)
        self._lines = []
        if self._clear_on_flush:
            self._lineset = set()

    def close(self):
        if len(self._lines) > 0:
            self.flush()
        self._lineset = set()
        self._fd.close()


class DrugBankParser:
    """
    A DrugBank data parser
    """

    def __init__(self):
        """
        """
        self._filemap = {
            "interaction": "db_ddi.txt",
            "target": "db_targets.txt",
            "pathway": "db_pathways.txt",
            "meta": "db_meta.txt",
            "mesh": "db_mesh.txt",
            "classification": "db_classification.txt",
            "atc": "db_atc.txt",
            "stage": "db_product_stage.txt",
            'mechanism': "db_mechanism_of_action.txt"
        }
        self._ns = {'db': 'http://www.drugbank.ca'}

    @property
    def filelist(self):
        return [s for s in self._filemap.values()]

    def __parse_target(self, target_element, drug_id, rel_type, output_fd):
        """
        Parse a drug target

            targets with actions are set as unknown
            targets with action 'other' are set as unknown
            targets with action 'other/unknown' are set as unknown
        Parameters
        ----------
        target_element : xml.etree.ElementTree.Element
            xml element
        drug_id : string
            id of the drug
        rel_type : string
            type of target
        output : SetWriter
            writer for statements
        """

        # Link to uniprot
        poly = target_element.find('./db:polypeptide', self._ns)
        if poly is None:
            return
        poly_id = None
        if 'source' in poly.attrib and poly.attrib['source'] == 'Swiss-Prot':
            poly_id = poly.attrib['id']
        else:
            for extern_id in poly.findall('./db:external-identifiers/db:external-identifier', self._ns):
                res = extern_id.find('db:resource', self._ns)
                val = extern_id.find('db:identifier', self._ns)
                if res is not None and val is not None and res.text == 'UniprotKB':
                    poly_id = sanatize_text(val.text)
                    break
        if poly_id is None:
            return

        # gather any references to pubmed
        pmids = target_element.findall('./db:references/db:articles/db:article/db:pubmed-id', self._ns)
        pmids = [sanatize_text(pmid.text) for pmid in filter(lambda x: x.text is not None, pmids)]
        ref_string = ''
        if len(pmids) > 0:
            ref_string = ','.join(pmids)

        # gather all actions
        actions = target_element.findall('./db:actions/db:action', self._ns)
        formatted_actions = []
        for action in actions:
            action_text = sanatize_text(action.text)
            #
            if action_text == 'other' or action_text == 'other_unknown':
                action_text = 'unknown'
            if action_text == '':
                continue
            formatted_actions.append(action_text)

        # If no action provided set it to unknown
        if len(formatted_actions) == 0:
            formatted_actions = ['unknown']

        # create an extended quad for each action including references
        for action in formatted_actions:
            if len(pmids) > 0:
                output_fd.write(f'{drug_id}\t{rel_type}\t{poly_id}\t{action}\t{ref_string}\n')
            else:
                output_fd.write(f'{drug_id}\t{rel_type}\t{poly_id}\t{action}\n')

    def __extract_side_effects(self, desc):
        """
        Extracts side effects from drug drug interaction descriptions
        Parameters
        ----------
        desc : str
            The interaction description
        Returns
        -------
        side_effects : list
            The list of side effects of the interaction
        """
        side_effects = []
        for pattern_index, pattern in enumerate(DDI_SIDE_EFFECTS):
            pg = re.match(pattern, desc)
            if pg is not None:
                se_name_list = []
                se_name = pg.group("se").lower()
                mode = pg.group("mode")

                # Handle the case of multiple activities eg x, y and z activities
                has_word_activities = ("activities" in se_name)
                if has_word_activities:
                    se_name = se_name.replace(" activities", "")
                mode_name = DDI_MODE_MAP[mode]
                if ", and" in se_name:
                    se_name_list = [sanatize_se_txt(se) for se in se_name.replace("and", "").split(", ")]
                elif "and" in se_name:
                    se_name_list = [sanatize_se_txt(se) for se in se_name.split(" and ")]
                else:
                    se_name_list = [sanatize_se_txt(se_name)]

                if has_word_activities:
                    se_name_list = [txt + "_activities" for txt in se_name_list]

                for side_effect in se_name_list:
                    if side_effect in DDI_SE_NAME_MAP:
                        side_effect = DDI_SE_NAME_MAP[side_effect]
                    side_effects.append(f'{mode_name}_{side_effect}')

                # decrease_excretion_rate
                if pattern_index == 5:
                    side_effects.append('decrease_excretion_rate')
                elif pattern_index == 6:
                    side_effects.append('increase_excretion_rate')

                break
        return side_effects

    def __parse_drug_interaction(self, interaction_element, drug_id, output):
        """
        Parse a drug interaction
        Parameters
        ----------
        interaction_element : xml.etree.ElementTree.Element
            xml element
        drug_id : string
            id of the drug
        output : SetWriter
            writer for statements
        """
        dest = interaction_element.find('./db:drugbank-id', self._ns)
        if dest is None:
            raise Exception('Interaction does not contain destination')

        dest_text = sanatize_text(dest.text)

        # Add description of interaction to output
        desc = interaction_element.find('./db:description', self._ns)
        desc_text = None
        if desc.text is not None:
            desc_text = desc.text.strip().replace('\t', ' ').replace('\n', ' ')

        if dest_text is not None and dest_text != '':
            # Output side effect descritpion if available
            if desc_text is not None and desc_text != '':
                side_effects = self.__extract_side_effects(desc_text)
                for se in side_effects:
                    output.write(f'{drug_id}\tDRUG_INTERACTION\t{dest_text}\t{se}\n')
            else:
                output.write(f'{drug_id}\tDRUG_INTERACTION\t{dest_text}\n')

    def __parse_atc_code(self, code_element, drug_id, output):
        """
        Parse a drug atc codes
        the code string encodes all levels of the code hierarchy
        for example B01AE02
        B       : C1
        B01     : C2
        B01A    : C3
        B01AE   : C4
        B01AE02 : C5
        Parameters
        ----------
        code_element : xml.etree.ElementTree.Element
            xml element
        drug_id : string
            id of the drug
        output : SetWriter
            writer for statements
        """
        code = code_element.get('code')

        output.write(f'{drug_id}\tDRUG_ATC\tATC:{code[0:1]}\n')
        output.write(f'{drug_id}\tDRUG_ATC\tATC:{code[0:3]}\n')
        output.write(f'{drug_id}\tDRUG_ATC\tATC:{code[0:4]}\n')
        output.write(f'{drug_id}\tDRUG_ATC\tATC:{code[0:5]}\n')
        output.write(f'{drug_id}\tDRUG_ATC\tATC:{code}\n')

    def __parse_pathway(self, pathway_element, drug_id, output):
        """
        Parse a drug pathway
        Parameters
        ----------
        pathway_element : xml.etree.ElementTree.Element
            xml element
        drug_id : string
            id of the drug
        output : SetWriter
            writer for statements
        """
        pid = pathway_element.find('./db:smpdb-id', self._ns)
        if pid is None:
            return
        pid = pid.text
        output.write(f'{drug_id}\tDRUG_PATHWAY\t{pid}\n')
        category = pathway_element.find('./db:category', self._ns)
        if category is not None:
            category_text = sanatize_text(category.text)
            if category_text is not None and category_text != '':
                output.write(f'{pid}\tPATHWAY_CATEGORY\t{category.text.strip()}\n')
        for enzyme in pathway_element.findall('./db:enzymes/db:uniprot-id', self._ns):
            enzyme_text = sanatize_text(enzyme.text)
            if enzyme_text is not None and enzyme_text != '':
                output.write(f'{pid}\tPATHWAY_ENZYME\t{enzyme_text}\n')

    def __parse_drug(self, drug_element, output_writers):
        """
        Parse a top level xml drug entry

        Parameters
        ----------
        drug_element : xml.etree.ElementTree.Element
            xml element
        output_writers: dict
            maps section names to their SetWriters
        """

        #
        # Parse drug metadata
        meta_fd = output_writers['meta']
        stage_fd = output_writers['stage']
        mech_fd = output_writers['mechanism']
        drug_id_elem = drug_element.find('./db:drugbank-id[@primary="true"]', self._ns)

        if drug_id_elem is None:
            raise Exception('Primary id not found')

        drug_id = drug_id_elem.text
        meta_fd.write(f'{drug_id}\tTYPE\tDRUG\n')
        name = drug_element.find('./db:name', self._ns)
        if name is not None:
            name_text = sanatize_text(name.text)
            if name_text is not None and name_text != '':
                meta_fd.write(f'{drug_id}\tNAME\t{name_text}\n')

        for synonym in drug_element.findall('./db:synonyms/db:synonym[@language="english"]', self._ns):
            syn_text = sanatize_text(synonym.text)
            if syn_text is not None and syn_text != '':
                meta_fd.write(f'{drug_id}\tSYNONYM\t{syn_text}\n')

        for group in drug_element.findall('./db:groups/db:group', self._ns):
            group_text = sanatize_text(group.text)
            if group_text is not None and group_text != '':
                stage_fd.write(f'{drug_id}\tPRODUCT_STAGE\t{group_text}\n')

        for pmid in drug_element.findall('./db:general-references/db:articles/db:article/db:pubmed-id', self._ns):
            pmid_text = sanatize_text(pmid.text)
            if pmid_text is not None and pmid_text != '':
                meta_fd.write(f'{drug_id}\tPUBMED_ARTICLE\t{pmid_text}\n')

        for product in drug_element.findall('./db:products/db:product/db:name', self._ns):
            product_text = sanatize_text(product.text)
            if product_text is not None and product_text != '':
                meta_fd.write(f'{drug_id}\tPRODUCT\t{product_text}\n')

        mechanism = drug_element.find('./db:mechanism-of-action', self._ns)
        if mechanism is not None:
            if mechanism.text is not None and mechanism.text.strip() != '':
                mech_text = re.sub('\s', ' ', mechanism.text).strip()
                mech_fd.write(f'{drug_id}\t{mech_text}\n')
        #
        # Parse drug classification
        classification_fd = output_writers['classification']
        classification = drug_element.find('./db:classification', self._ns)
        if classification is not None:
            for child in classification:
                if child.tag == '{%s}description' % self._ns['db']:
                    continue
                if child.text is not None and child.text != '':
                    c_type = child.tag.split('}')[-1]
                    c_type = sanatize_text(c_type).upper()
                    value = sanatize_text(child.text)
                    if value is not None and value != '':
                        classification_fd.write(f'{drug_id}\t{c_type}\t{value}\n')

        #
        # Parse drug targets
        target_fd = output_writers['target']
        for target in drug_element.findall('./db:targets/db:target', self._ns):
            self.__parse_target(target, drug_id, 'DRUG_TARGET', target_fd)

        for carrier in drug_element.findall('./db:carriers/db:carrier', self._ns):
            self.__parse_target(carrier, drug_id, 'DRUG_CARRIER', target_fd)

        for transporter in drug_element.findall('./db:transporters/db:transporter', self._ns):
            self.__parse_target(transporter, drug_id, 'DRUG_TRANSPORTER', target_fd)

        for enzyme in drug_element.findall('./db:enzymes/db:enzyme', self._ns):
            self.__parse_target(enzyme, drug_id, 'DRUG_ENZYME', target_fd)

        #
        # Parse drug interactions
        interaction_fd = output_writers['interaction']
        for interaction in drug_element.findall('./db:drug-interactions/db:drug-interaction', self._ns):
            self.__parse_drug_interaction(interaction, drug_id, interaction_fd)

        #
        # Parse drug atc code categories
        atc_fd = output_writers['atc']
        for atc_code in drug_element.findall('./db:atc-codes/db:atc-code', self._ns):
            self.__parse_atc_code(atc_code, drug_id, atc_fd)

        #
        # Parse mesh categories
        mesh_fd = output_writers['mesh']
        for mesh_id in drug_element.findall('./db:categories/db:category/db:mesh-id', self._ns):
            mesh_id_text = sanatize_text(mesh_id.text)
            if mesh_id_text is not None and mesh_id_text != '':
                mesh_fd.write(f'{drug_id}\tMESH_CATEGORY\t{mesh_id.text}\n')

        #
        # Parse drug pathways
        pathway_fd = output_writers['pathway']
        for pathway in drug_element.findall('./db:pathways/db:pathway', self._ns):
            self.__parse_pathway(pathway, drug_id, pathway_fd)

    def parse_drugbank_xml(self, filepath, output_dp, filename='full database.xml'):
        """ Parse Drugbank xml file
        Parameters
        ----------
        filepath : str
            absolute file path of the drugbank zip file
        output_dp : str
            path of the output directory
        filename : str
            name of the xml file in the drugbank zip (default "full database.xml")
        """
        output_writers = {key: SetWriter(join(output_dp, fn)) for key, fn in self._filemap.items()}
        output_writers['pathway'].clear_on_flush = False

        with ZipFile(filepath, 'r') as dbzip:
            with dbzip.open(filename, force_zip64=True) as xmlfile:
                print_section_header("Parsing Drugbank XML file (%s)" % (bcolors.OKGREEN + filepath + "/" + filename + bcolors.ENDC))
                start = timer()
                nb_entries = 0
                for event, elem in ET.iterparse(xmlfile):
                    # Check the length of the drug element as pathways also contain drug elements
                    if elem.tag == '{http://www.drugbank.ca}drug' and len(elem) > 2:
                        nb_entries += 1
                        if nb_entries % 5 == 0:
                            speed = nb_entries / (timer() - start)
                            msg = prc_sym + "Processed (%d) entries.  Speed: (%1.5f) entries/second" % (nb_entries, speed)
                            print("\r" + msg, end="", flush=True)
                        self.__parse_drug(elem, output_writers)
                        elem.clear()

                        # Flush the output buffers
                        for writer in output_writers.values():
                            writer.flush()
                print(done_sym + " Took %1.2f Seconds." % (timer() - start), flush=True)

        for writer in output_writers.values():
            writer.close()


def main(argv):
    parser = DrugBankParser()

    path = '/Users/pasquale/workspace/drugbank/drugbank_all_full_database.xml.zip'
    parser.parse_drugbank_xml(path, 'drugbank/')


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    main(sys.argv[1:])
