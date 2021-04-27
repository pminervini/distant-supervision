#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
import json
import config
import pickle

from clarify.ds.linking import ExactEntityLinking

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def link_sentences(linker: ExactEntityLinking, sents_fname: str, output_fname: str):
    t = time.time()
    
    with open(sents_fname, encoding="utf-8", errors="ignore") as rf, open(output_fname, "w", encoding="utf-8", errors="ignore") as wf:
        for idx, sent in enumerate(rf):
            if idx % 1000000 == 0 and idx != 0:
                logger.info("Checked {} sentences for entity linking".format(idx))
            sent = sent.strip()
            if not sent:
                continue
            # Skip short or very long sentences
            if (len(sent) < config.min_sent_char_len_linker) or (len(sent) > config.max_sent_char_len_linker):
                continue
            text2span = linker.link(sent)
            if text2span is None:
                continue
            jdata = {"sent": sent, "matches": text2span}
            wf.write(json.dumps(jdata) + "\n")
    
    t = (time.time() - t) // 60
    logger.info("Took %d mins" % t)


if __name__ == "__main__":
    with open(config.umls_vocab_file, "rb") as rf:
        uv = pickle.load(rf)

    # linker = ExactEntityLinking(uv.entity_text_to_cuis.keys(), config.case_sensitive_linker)
    linker = ExactEntityLinking(uv[2]["entity_text_to_cuis"].keys(), config.case_sensitive_linker)

    link_sentences(linker, config.medline_unique_sents_file, config.medline_linked_sents_file)
