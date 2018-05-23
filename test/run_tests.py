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
ID_FIELD_NAME = db.DataBase.ID_FIELD_NAME
POST_DATA_FIELD_NAME = db.DataBase.POST_DATA_FIELD_NAME
VOTES_FIELD_NAME = db.DataBase.VOTES_FIELD_NAME
DATE_TIME_FIELD = db.DataBase.DATE_TIME_FIELD_NAME
POST_DATA_PAYLOAD_KEY = main.POST_DATA_PAYLOAD_KEY


def create_table(data_base, table_name):
    with data_base.get_db_connection() as db_conn:
        db_conn.execute(
            "CREATE TABLE {table_name} ({id_field} INTEGER PRIMARY KEY, {date_time} TEXT NOT NULL, {post_data_field} TEXT NOT NULL, {vote_field} INTEGER NOT NULL)"
                .format(table_name=table_name, vote_field=VOTES_FIELD_NAME, date_time=db.DataBase.DATE_TIME_FIELD_NAME,
                        id_field=db.DataBase.ID_FIELD_NAME, post_data_field=db.DataBase.POST_DATA_FIELD_NAME))
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
        r = requests.post(self.POSTS_URL, json={POST_DATA_PAYLOAD_KEY: post_text})
        self.assert_headers(r)
        assert (r.status_code == http.HTTPStatus.CREATED)
        return r.json()

    def assert_headers(self, r):
        assert (r.headers.get('Content-Type') == 'application/json')

    def _assert_post_response(self, post_id, post_text, votes, response_dict):
        assert (response_dict.get(ID_FIELD_NAME) == post_id)
        assert (response_dict.get(POST_DATA_FIELD_NAME) == post_text)
        assert (response_dict.get(VOTES_FIELD_NAME) == votes)
        assert (response_dict.get(DATE_TIME_FIELD) is not None)

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
        post = self.create_post(post_text)
        self._assert_post_response(1, post_text, 0, post)

    def test_get_post(self):
        post_text = "sampleText"
        post_id = self.create_post(post_text).get(ID_FIELD_NAME)
        r = requests.get("{}/{}".format(self.POSTS_URL, post_id))
        self.assert_headers(r)
        assert (r.status_code == http.HTTPStatus.OK)
        self._assert_post_response(post_id, post_text, 0, r.json())

    def test_negative_get_post(self):
        r = requests.get("{}/{}".format(self.POSTS_URL, 6))
        self.assert_headers(r)
        assert (r.status_code == http.HTTPStatus.NOT_FOUND)

    def test_edit_post(self):
        post_text = "sampleText"
        post_id = self.create_post(post_text).get(ID_FIELD_NAME)
        r = requests.get("{}/{}".format(self.POSTS_URL, post_id))
        self.assert_headers(r)
        assert (r.status_code == http.HTTPStatus.OK)
        self._assert_post_response(post_id, post_text, 0, r.json())

        new_post_text = "Images And Words"
        r = requests.post("{}/{}".format(self.POSTS_URL, post_id), json={POST_DATA_PAYLOAD_KEY: new_post_text})
        self.assert_headers(r)
        assert (r.status_code == http.HTTPStatus.OK)
        self._assert_post_response(post_id, new_post_text, 0, r.json())

    def test_edit_non_existing_post(self):
        post_text = "sampleText"
        non_exist_id = 666
        r = requests.post("{}/{}".format(self.POSTS_URL, non_exist_id), json={POST_DATA_PAYLOAD_KEY: post_text})
        self.assert_headers(r)
        assert (r.status_code == http.HTTPStatus.NOT_FOUND)

    def test_voting(self):
        post_text = "sampleText"
        post_id = self.create_post(post_text).get(ID_FIELD_NAME)
        r = requests.get("{}/{}".format(self.POSTS_URL, post_id))
        self._assert_post_response(post_id, post_text, 0, r.json())

        r = requests.post("{}/{}/upvote".format(self.POSTS_URL, post_id), json={})
        self.assert_headers(r)
        assert (r.status_code == http.HTTPStatus.OK)
        self._assert_post_response(post_id, post_text, 1, r.json())

        r = requests.post("{}/{}/downvote".format(self.POSTS_URL, post_id), json={})
        self.assert_headers(r)
        assert (r.status_code == http.HTTPStatus.OK)
        self._assert_post_response(post_id, post_text, 0, r.json())


if __name__ == "__main__":
    pytest.main([TEST_FILE_PATH, '-s'])
