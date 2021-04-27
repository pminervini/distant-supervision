# -*- coding: utf-8 -*-

import logging
import collections
import time

from flashtext import KeywordProcessor

from typing import Iterable

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class ExactEntityLinking:
    def __init__(self, entities: Iterable[str], case_sensitive: bool = True):
        self.linker = KeywordProcessor(case_sensitive=case_sensitive)

        logger.info("Building Trie data structure with flashText for exact match entity linking (|E|={}) ...".format(len(entities)))

        t = time.time()
        self.linker.add_keywords_from_list(list(set(entities)))
        t = (time.time() - t) // 60

        logger.info("Took %d mins" % t)

    def link(self, text: str):
        spans = sorted(
            [(start_span, end_span) for _, start_span, end_span in self.linker.extract_keywords(text, span_info=True)],
            key=lambda span: span[0])
        if not spans:
            return

        # Remove overlapping matches, if any
        filtered_spans = list()
        for i in range(1, len(spans)):
            span_prev, span_next = spans[i - 1], spans[i]
            if span_prev[1] < span_next[0]:
                filtered_spans.append(spans[i])
        spans = filtered_spans[:]

        matches_texts = [text[s:e] for s, e in spans]
        # Check if any entity is present more than once, drop this sentence
        counts = collections.Counter(matches_texts)
        skip = False

        for _, count in counts.items():
            if count > 1:
                skip = True
                break
        if skip:
            return

        text2span = {matches_texts[i]: spans[i] for i in range(len(spans))}

        return text2span
