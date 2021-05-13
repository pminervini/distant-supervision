#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
import config

from clarify.ds.sentences import MEDLINESents

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    ms = MEDLINESents(config.medline_file, config.medline_unique_sents_file)
    t = time.time()
    ms.extract_unique_sentences()
    t = (time.time() - t) // 60
    logger.info("Took {} mins!".format(t))
