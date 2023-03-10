#!/usr/bin/env python3
# coding: utf-8
"""
Created on January 20th, 2023
@title: Balth App
@version: 2.1
# Add details in help string
@author: Balthazar Méhus
@society: CentraleSupélec
@abstract: Python PDF extraction and storage - Easy client to request on Balthapp
"""

import argparse


class Args:

    def __init__(self):
        self._parser = argparse.ArgumentParser(
            prog="Balthclient for Balthapp",
            description="""Send a local PDF file to the balthapp Flask API to get the extracted text and metadata.""",
            epilog="""
            By Balthazar Mehus /
            MS SIO 22-23 /
            CentraleSupélec
            -> See the README file and Have fun ;)
            """
        )
        self._group = self._parser.add_mutually_exclusive_group()
        self._add_args(self._group)
        self._parser.add_argument("-dc",
                                  "--downloadcontract",
                                  dest="downloadAPIcontract",
                                  nargs='?',
                                  help="Download the API contract (.yaml)")
        self.parsed_args = self._parser.parse_args()

    def _add_args(self, group):
        """ Create a mutually exclusive required CLI parameters for our client app
        :param group:
        :return: one of the 3 available parameters : postfile_pdfpath, getmetadata_uuid, gettext_uuid
        """
        group.add_argument("-pf",
                           "--postfile",
                           dest="postfile_pdfpath",
                           type=str,
                           help="Firstly, by providing only one local path, "
                                "post a PDF file to the API. Returning the job ID.")

        group.add_argument("-gm",
                           "--getmetadata",
                           dest="getmetadata_uuid",
                           type=str,
                           help="Then, after --postfile only, by providing the received job ID "
                                "(UUID, ex:76310ab9-01d9-49c3-927c-1bafaa0a52a8), "
                                "get a the extracted metadata from the corresponding posted PDF.")

        group.add_argument("-gt",
                           "--gettext",
                           dest="gettext_uuid",
                           type=str,
                           help="Finaly, after --getmetada only, by providing the received job ID, "
                                "(UUID, ex:76310ab9-01d9-49c3-927c-1bafaa0a52a8), "
                                "get a the extracted text from the corresponding posted PDF.")

