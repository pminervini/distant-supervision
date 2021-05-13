#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from clarify.ds.drugbank import DrugBankVocab
import config

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    uv = DrugBankVocab()
    uv.build()

    # Save the DrugBank vocab
    logger.info("Saving DrugBank vocab object at {} ...".format(config.drugbank_vocab_file))
    uv.save(config.drugbank_vocab_file)
