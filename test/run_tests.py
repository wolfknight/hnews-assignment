import http
import os
import sys
from time import sleep

import requests
import pytest

TEST_FILE_PATH = os.path.realpath(__file__)
CWD_PATH = os.path.dirname(TEST_FILE_PATH)
ROOT_PATH = os.path.normpath(os.path.join(CWD_PATH, os.path.pardir))
sys.path.append(os.path.join(ROOT_PATH, "src"))

import db
import main

TEST_DB_NAME = "test.db"


def create_table(data_base, table_name):
    with data_base.get_db_connection() as db_conn:
        db_conn.execute(
            "CREATE TABLE %s (id INTEGER PRIMARY KEY, post_data TEXT NOT NULL, score INTEGER NOT NULL)" % table_name)
        db_conn.commit()


class TestClass(object):
    test_server = None
    SERVER_URL = "http://localhost:8080"
    POSTS_URL = "{server}/posts".format(server=SERVER_URL)

    @classmethod
    def remove_test_db(cls):
        db_path = TestClass.get_test_db_path()
        if os.path.exists(db_path):
            os.remove(db_path)

    @classmethod
    def get_test_db_path(cls):
        return os.path.join(ROOT_PATH, TEST_DB_NAME)

    @classmethod
    def create_test_db(cls):
        cls.remove_test_db()
        create_table(db.DataBase(cls.get_test_db_path()), "posts")

    @classmethod
    def setup_class(cls):
        print("Starting the server")
        cls.test_server = main.start_server()
        sleep(2)  # Wait for server to be up. TODO - Change sleep to a condition based wait

    @classmethod
    def teardown_class(cls):
        if cls.test_server is not None:
            print("Stopping the server")
            cls.test_server.stop()

    def setup_method(self, method):
        self.create_test_db()

    def teardown_method(self, method):
        self.remove_test_db()

    def create_post(self, post_text):
        r = requests.post(self.POSTS_URL, json={"post_data": post_text})
        self.assert_headers(r)
        assert (r.status_code == http.HTTPStatus.CREATED)
        post_id = r.json().get("id")
        return post_id

    def assert_headers(self, r):
        assert (r.headers.get('Content-Type') == 'application/json')

    def test_is_db_exist(self):
        db_path = TestClass.get_test_db_path()
        assert os.path.exists(db_path)

    def test_list_posts_empty(self):
        r = requests.get(self.POSTS_URL)
        self.assert_headers(r)
        assert (r.status_code == http.HTTPStatus.OK)
        assert (r.json() == {'posts': []})

    def test_create_post(self):
        post_text = "sampleText"
        post_id = self.create_post(post_text)
        assert (post_id == 1)

    def test_get_post(self):
        post_text = "sampleText"
        post_id = self.create_post(post_text)
        r = requests.get("{}/{}".format(self.POSTS_URL, post_id))
        self.assert_headers(r)
        assert (r.status_code == http.HTTPStatus.OK)
        assert (r.json() == {'id': post_id, 'post_data': post_text, 'score': 0})

    def test_negative_get_post(self):
        r = requests.get("{}/{}".format(self.POSTS_URL, 6))
        self.assert_headers(r)
        assert (r.status_code == http.HTTPStatus.NOT_FOUND)


if __name__ == "__main__":
    pytest.main([TEST_FILE_PATH, '-s'])
