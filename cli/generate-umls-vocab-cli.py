#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from clarify.ds.umls import UMLSVocab
import config

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    uv = UMLSVocab(config.mrrel_file, config.mrconso_file)
    uv.build()

    # Save the UMLS vocab
    logger.info("Saving UMLS vocab object at {} ...".format(config.umls_vocab_file))
    uv.save(config.umls_vocab_file)
