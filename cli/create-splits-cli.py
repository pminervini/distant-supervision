#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import config
import os

from clarify.utils import JsonlReader
from clarify.ds.umls import UMLSVocab
from clarify.ds.splits import get_groups_texts_from_umls_vocab, align_groups_to_sentences, pruned_triples, \
    filter_triples_with_evidence, split_lines, report_data_stats, remove_overlapping_sents, write_final_jsonl_file, \
    create_data_split

import logging

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    # Load UMLS vocab object
    logger.info("Loading UMLS vocab object `{}` ...".format(config.umls_vocab_file))
    uv = UMLSVocab.load(config.umls_vocab_file)

    # See if the file was created before, read it
    if os.path.exists(config.groups_linked_sents_file):
        pos_groups = set()
        neg_groups = set()

        logger.info("Reading groups linked file `{}` ...".format(config.groups_linked_sents_file))
        for jdata in JsonlReader(config.groups_linked_sents_file):
            pos_groups.update(jdata["groups"]["p"])
            neg_groups.update(jdata["groups"]["n"])

    else:
        # 1. Collect all possible group texts from their CUIs
        groups_texts = get_groups_texts_from_umls_vocab(uv)

        # group_texts is a set of tab-separated surface form pairs,
        # corresponding to CUI pairs appearing in the values of uv.relation_text_to_groups

        # 2. Search for text alignment of groups (this can take up to 80~90 mins)

        # config.medline_linked_sents_file -> umls_linked_sentences.jsonl (list of {"sent": sentence, "matches": ..})
        pos_groups, neg_groups = align_groups_to_sentences(groups_texts, config.medline_linked_sents_file,
                                                           config.groups_linked_sents_file)
        # config.groups_linked_sents_file -> linked_sentences_to_groups.jsonl
        #   {"sent": .., "matches": .., "groups": {"p": ["a\tb", "c\td", ..], "n": ..}}

    # 3. From collected groups and pruning relations criteria, get final triples
    triples = pruned_triples(uv, pos_groups, neg_groups, config.min_rel_group, config.max_rel_group)

    # triples: list of (s, p, o) triples, where entities and relation types are represented by their surface forms

    # 4. Collect evidences and filter triples based on sizes of collected bags
    triples, group_to_data = filter_triples_with_evidence(triples, config.bag_size, k_tag=config.k_tag,
                                                          expand_rels=config.expand_rels)

    logger.info(" *** No. of triples (after filtering) *** : {}".format(len(triples)))

    E = set()
    R = set()

    with open(config.triples_file, "w") as wf:
        for ei, rj, ek in triples:
            E.update([ei, ek])
            R.add(rj)
            wf.write("{}\t{}\t{}\n".format(ei, rj, ek))

    with open(config.entities_file, "w") as wf:
        for e in E:
            wf.write("{}\n".format(e))

    with open(config.relations_file, "w") as wf:
        for r in R:
            wf.write("{}\n".format(r))

    logger.info(" *** No. of entities *** : {}".format(len(E)))
    logger.info(" *** No. of relations *** : {}".format(len(R)))

    # 5. Split into train, dev and test at triple level to keep zero triples overlap
    train_triples, dev_triples, test_triples = create_data_split(triples)
    train_lines = split_lines(train_triples, group_to_data)
    dev_lines = split_lines(dev_triples, group_to_data)
    test_lines = split_lines(test_triples, group_to_data)

    # Remove any overlapping test and dev sentences from training
    logger.info("Train stats before removing overlapping sentences ...")
    report_data_stats(train_lines, train_triples)
    train_lines, train_triples = remove_overlapping_sents(train_lines, test_lines)
    train_lines, train_triples = remove_overlapping_sents(train_lines, dev_lines)

    logger.info("Train stats after removing dev + test overlapping sentences ...")
    report_data_stats(train_lines, train_triples)

    # Triples should be of form (e1, r(e1,e2)/r(e2,e1), e2) when relation class is expanded
    if config.expand_rels:
        temp = set()
        for line in train_lines:
            temp.add((line["e1"], line["relation"], line["e2"]))
        train_triples = set(temp)
        # dev
        temp = set()
        for line in dev_lines:
            temp.add((line["e1"], line["relation"], line["e2"]))
        dev_triples = set(temp)
        # test
        temp = set()
        for line in test_lines:
            temp.add((line["e1"], line["relation"], line["e2"]))
        test_triples = set(temp)

    logger.info("Final stats ...")
    print("TRAIN")
    report_data_stats(train_lines, train_triples)
    print("DEV")
    report_data_stats(dev_lines, dev_triples)
    print("TEST")
    report_data_stats(test_lines, test_triples)

    with open(config.train_triples_file, "w") as wf:
        for ei, rj, ek in train_triples:
            wf.write("{}\t{}\t{}\n".format(ei, rj, ek))

    with open(config.dev_triples_file, "w") as wf:
        for ei, rj, ek in dev_triples:
            wf.write("{}\t{}\t{}\n".format(ei, rj, ek))

    with open(config.test_triples_file, "w") as wf:
        for ei, rj, ek in test_triples:
            wf.write("{}\t{}\t{}\n".format(ei, rj, ek))

    # 6. Write actual train, dev, test files with sentence, group and relation
    logger.info("Creating training file at `{}` ...".format(config.train_file))
    write_final_jsonl_file(train_lines, config.train_file)
    logger.info("Creating development file at `{}` ...".format(config.dev_file))
    write_final_jsonl_file(dev_lines, config.dev_file)
    logger.info("Creating testing file at `{}` ...".format(config.test_file))
    write_final_jsonl_file(test_lines, config.test_file)
