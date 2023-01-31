# coding:utf-8

import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from flask import Flask, request
from flask_testing import TestCase

sys.path.append("..")
from balthapp import *


class TestUploadPDF(unittest.TestCase):

    def create_app(self):
        test_app = Flask(__name__)
        return test_app

    def test_upload_invalid_payload(self):
        # Test case when the bad key is provided in the payload
        with self.client:
            response = self.client.post('/documents')
            self.assertEqual(response.status_code, 422)
            self.assertEqual(response.get_json(), {"error": "Invalid payload, only POST on 'pdf_file' key."})

    def test_upload_no_file_provided(self):
        # Test case when no file is provided in the post request
        with self.client:
            response = self.client.post('/documents', data={'pdf_file': ''})
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.get_json(), {"error": "No pdf file provided."})

    def test_upload_file_invalid_extension(self):
        # Test case when an invalid file extension is provided
        with open("test.txt", "w") as test_file:
            test_file.write("This is a test file.")
        with open("test.txt", "rb") as test_file:
            with self.client:
                response = self.client.post('/documents', data={'pdf_file': (test_file, 'test.txt')})
                self.assertEqual(response.status_code, 415)
                self.assertEqual(response.get_json(), {"error": "Invalid file EXT. Please upload a PDF file."})
        os.remove("test.txt")

    @patch('magic.Magic')
    def test_upload_file_invalid_file_mimetype(self, MagicMock):
        # Test case when a file with a different MIME type is provided
        with open("test.pdf", "w") as test_file:
            test_file.write("This is a test file.")
        with open("test.pdf", "rb") as test_file:
            MagicMock.return_value.id_buffer.return_value = "JPEG"
            with self.client:
                response = self.client.post('/documents', data={'pdf_file': (test_file, 'test.pdf')})
                self.assertEqual(response.status_code, 415)
                self.assertEqual(response.get_json(), {"error": "JPEGInvalid file type. Please upload a PDF file."})
        os.remove("test.pdf")

    def test_upload_file_invalid_size(self):
        # Test case when the file size exceeds the maximum limit of 10MB
        with open("test.pdf", "w") as test_file:
            test_file.write("A" * (1024 * 1024 * 20 + 1))
        with open("test.pdf", "rb") as test_file:
            with self.client:
                response = self.client.post('/documents', data={'pdf_file': (test_file, 'test.pdf')})
                self.assertEqual(response.status_code, 413)
                self.assertEqual(response.get_json(), {"error": "File size exceeded the maximum limit."})
        os.remove("test.pdf")

    if __name__ == '__main__':
        unittest.main()
