# -*- coding: utf-8 -*-

import logging
import collections
import pickle

from nltk.corpus import stopwords

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class DrugBankVocab:
    """Class to hold UMLS entities, relations and their triples.

    """
    def __init__(self):
        self.db_meta_path = 'drugbank/db_meta.txt'
        self.db_ddi_path = 'drugbank/db_ddi.txt'

    def build(self):
        """Parses UMLS MRREL.RRF and MRCONSO.RRF files to build mappings between
        entities, their texts and relations.

        """
        self.entity_text_to_cuis = collections.defaultdict(set)
        self.cui_to_entity_texts = collections.defaultdict(set)

        logger.info(f'Reading DrugBank concepts from {self.db_meta_path} ..')
        with open(self.db_meta_path, 'r') as f:
            for line in f:
                s, p, o = line.split('\t')

                s = s.strip()
                p = p.strip()
                o = o.strip()

                if p in {'NAME', 'SYNONYM'}:
                    # Ignore entities with char len = 2
                    if len(o) <= 2:
                        continue

                    self.cui_to_entity_texts[s].add(o)
                    self.entity_text_to_cuis[o].add(s)

                    s = s.replace('_', ' ')
                    o = o.replace('_', ' ')

                    self.cui_to_entity_texts[s].add(o)
                    self.entity_text_to_cuis[o].add(s)

        logger.info("Collected {} unique CUIs and {} unique entities texts.".format(len(self.cui_to_entity_texts),
                                                                                    len(self.entity_text_to_cuis)))
        self.relation_text_to_groups = collections.defaultdict(set)

        logger.info(f'Reading DrugBank triples from {self.db_ddi_path} ..')
        with open(self.db_ddi_path, 'r') as f:
            for line in f:
                s, p, o, d = line.split('\t')

                s = s.strip()
                p = p.strip()
                o = o.strip()
                d = d.strip()

                if p in {'DRUG_INTERACTION'}:
                    self.relation_text_to_groups[d].add((s, o))

        all_groups = set()
        num_of_triples = 0
        for groups in self.relation_text_to_groups.values():
            all_groups.update(groups)
            num_of_triples += len(groups)
        num_of_groups = len(all_groups)

        logger.info("Collected {} unique relation texts.".format(len(self.relation_text_to_groups)))
        logger.info("Collected {} triples with {} unique groups.".format(num_of_triples, num_of_groups))

    def save(self, fname):
        args = (self.db_meta_path, self.db_ddi_path)
        kwargs = {}
        data = {
            "entity_text_to_cuis": self.entity_text_to_cuis,
            "cui_to_entity_texts": self.cui_to_entity_texts,
            "relation_text_to_groups": self.relation_text_to_groups
        }
        save_data = (args, kwargs, data)
        with open(fname, "wb") as wf:
            pickle.dump(save_data, wf)

    @staticmethod
    def load(fname):
        with open(fname, "rb") as rf:
            load_data = pickle.load(rf)
        uv = DrugBankVocab(load_data[0][0], load_data[0][1], **load_data[1])
        uv.entity_text_to_cuis = load_data[2]["entity_text_to_cuis"]
        uv.cui_to_entity_texts = load_data[2]["cui_to_entity_texts"]
        uv.relation_text_to_groups = load_data[2]["relation_text_to_groups"]
        return uv
