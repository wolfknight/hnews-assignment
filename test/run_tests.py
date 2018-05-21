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

    def test_is_db_exist(self):
        db_path = TestClass.get_test_db_path()
        assert os.path.exists(db_path)

    def test_list_posts_empty(self):
        r = requests.get("http://localhost:8080/posts")
        assert (r.headers.get('Content-Type') == 'application/json')
        assert (r.json() == {'posts': []})
        assert (r.status_code == http.HTTPStatus.OK)

    def test_create_post(self):
        r = requests.post("http://localhost:8080/posts", json={"text": "sampleText"})
        assert (r.headers.get('Content-Type') == 'application/json')
        assert (r.json().get("id") == 1)
        assert (r.status_code == http.HTTPStatus.OK)


if __name__ == "__main__":
    pytest.main([TEST_FILE_PATH, '-s'])
