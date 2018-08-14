#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

# create logger
logger = logging.getLogger("logging")
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s",
                              "%Y-%m-%d %H:%M:%S")
# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)
