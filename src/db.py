import datetime
import sqlite3
import psycopg2


class DataBase(object):
    POSTS_TABLE_NAME = "posts"
    DEFAULT_VOTE = 0
    VOTES_FIELD_NAME = "votes"
    SCORE_FIELD_NAME = "score"
    POST_DATA_FIELD_NAME = "post_data"
    ID_FIELD_NAME = "id"
    DATE_TIME_FIELD_NAME = 'date_time'

    def __init__(self, value_char, equals_operator) -> None:
        super().__init__()
        self.value_char = value_char
        self.equals_operator = equals_operator

    @staticmethod
    def _calculate_score(votes, item_hour_age, gravity=1.8):
        _votes = (votes - 1) if votes > 0 else votes
        return _votes / pow((item_hour_age + 2), gravity)

    @staticmethod
    def _get_post_dict(post_values):
        ret_dict_keys = (DataBase.ID_FIELD_NAME, DataBase.DATE_TIME_FIELD_NAME, DataBase.POST_DATA_FIELD_NAME, DataBase.VOTES_FIELD_NAME, DataBase.SCORE_FIELD_NAME)
        post_dict = dict(zip(ret_dict_keys, post_values))
        post_score = DataBase._calculate_score(post_dict.get(DataBase.VOTES_FIELD_NAME), post_dict.get(DataBase.SCORE_FIELD_NAME))
        post_dict[DataBase.SCORE_FIELD_NAME] = post_score
        return post_dict

    def get_db_connection(self):
        raise NotImplementedError()

    def create_post(self, post_data):
        with self.get_db_connection() as db_connection:
            db_cursor = db_connection.cursor()
            try:
                db_cursor.execute(
                    "INSERT INTO {table_name} ({date_time}, {post_data_field}, {vote_field}) VALUES ((CURRENT_TIMESTAMP),{VAL},{VAL}) {retid}"
                    .format(table_name=self.POSTS_TABLE_NAME, vote_field=self.VOTES_FIELD_NAME, post_data_field=self.POST_DATA_FIELD_NAME,
                            date_time=self.DATE_TIME_FIELD_NAME, VAL=self.value_char, retid=self._returning_id_str()),
                    (post_data, self.DEFAULT_VOTE))
                new_id = self._get_last_row_id(db_cursor)
                db_connection.commit()
            finally:
                db_cursor.close()
        return self.get_post(new_id)

    def _returning_id_str(self):
        raise NotImplementedError

    def _get_last_row_id(self, db_cursor):
        raise NotImplementedError()

    def _get_posts_list(self):
        with self.get_db_connection() as db_connection:
            db_cursor = db_connection.cursor()
            try:
                db_cursor.execute(self._select_post_query())
                result = db_cursor.fetchall()
            finally:
                db_cursor.close()
        return result

    def _select_post_query(self):
        return "SELECT {id_field}, {date_time}, {post_data_field}, {vote_field}, {hours_past} FROM {table_name}".format(
            table_name=self.POSTS_TABLE_NAME, id_field=self.ID_FIELD_NAME, date_time=self.DATE_TIME_FIELD_NAME,
            post_data_field=self.POST_DATA_FIELD_NAME, vote_field=self.VOTES_FIELD_NAME, hours_past=self._get_past_hours_query())

    def _get_past_hours_query(self):
        raise NotImplementedError

    def list_posts(self):
        posts_list = self._get_posts_list()
        return [self._get_post_dict(post_tuple) for post_tuple in posts_list]

    def get_post(self, post_id):
        with self.get_db_connection() as db_connection:
            db_cursor = db_connection.cursor()
            try:
                db_cursor.execute("{select_post} WHERE {id_field} {equals} {val_char}".format(
                    select_post=self._select_post_query(), id_field=self.ID_FIELD_NAME, val_char=self.value_char,
                    equals=self.equals_operator), (post_id,))
                result = db_cursor.fetchall()
            finally:
                db_cursor.close()
        if len(result) is 1:
            post_values = result[0]
            return self._get_post_dict(post_values)
        return None

    def edit_post_data(self, post_id, post_data):
        with self.get_db_connection() as db_connection:
            db_cursor = db_connection.cursor()
            try:
                db_cursor.execute(
                    "UPDATE {table_name} SET {post_data_field} = {val_char} WHERE {id_field} {equals} {val_char}".format(
                    table_name=self.POSTS_TABLE_NAME, id_field=self.ID_FIELD_NAME,
                    post_data_field=self.POST_DATA_FIELD_NAME, val_char=self.value_char, equals=self.equals_operator), (post_data, post_id))
                db_connection.commit()
            finally:
                db_cursor.close()
        post = self.get_post(post_id)
        return post is not None and post[self.POST_DATA_FIELD_NAME] == post_data

    def _edit_post_votes(self, post_id, is_up):
        post = self.get_post(post_id)
        if post is None:
            return False
        post_votes = post.get(self.VOTES_FIELD_NAME, self.DEFAULT_VOTE)
        new_post_votes = post_votes + 1 if is_up else post_votes - 1
        with self.get_db_connection() as db_connection:
            db_cursor = db_connection.cursor()
            try:
                db_cursor.execute(
                    "UPDATE {table_name} SET {vote_field} = {val_char} WHERE {id_field} {equals} {val_char}".format(
                        id_field=self.ID_FIELD_NAME, table_name=self.POSTS_TABLE_NAME,
                        vote_field=self.VOTES_FIELD_NAME, val_char=self.value_char, equals=self.equals_operator),
                    (new_post_votes, post_id))
                db_connection.commit()
            finally:
                db_cursor.close()
        new_post = self.get_post(post_id)
        return new_post is not None and new_post.get(self.VOTES_FIELD_NAME) == new_post_votes

    def vote_up(self, post_id):
        return self._edit_post_votes(post_id, True)
    def vote_down(self, post_id):
        return self._edit_post_votes(post_id, False)


class SqliteDataBase(DataBase):

    def __init__(self, db_location) -> None:
        super().__init__("?", "LIKE")
        self.db_location = db_location

    def get_db_connection(self):
        return sqlite3.connect(self.db_location)

    def _get_last_row_id(self, db_cursor):
        return db_cursor.lastrowid

    def _returning_id_str(self):
        return ""

    def _get_past_hours_query(self):
        return r"(STRFTIME('%s',DATETIME('now')) - STRFTIME('%s',{date_time})) / 3600".format(
            date_time=self.DATE_TIME_FIELD_NAME)


class PostgreSqlDataBase(DataBase):

    def __init__(self, host, db_name, user="postgres", password="mysecretpassword"):
        super().__init__("%s", "=")
        self.host = "'%s'" % host
        self.db_name = "'%s'" % db_name
        self.user = "'%s'" % user
        self.password = "'%s'" % password

    def get_db_connection(self):
        return psycopg2.connect(
            "dbname={dbname} user={user} host={host} password={password}".format(dbname=self.db_name, user=self.user,
                                                                                 host=self.host, password=self.password))

    def _get_last_row_id(self, db_cursor):
        return db_cursor.fetchone()[0]

    def _returning_id_str(self):
        return "RETURNING id"

    def _get_past_hours_query(self):
        return r"EXTRACT(EPOCH FROM current_timestamp-{date_time}::timestamp)/3600".format(
            date_time=self.DATE_TIME_FIELD_NAME)


if __name__ == '__main__':
    import os
    CWD_PATH = os.path.dirname(os.path.realpath(__file__))
    SRC_ROOT_PATH = os.path.normpath(os.path.join(CWD_PATH, os.path.pardir))

    TEST_DB_PATH = os.path.join(SRC_ROOT_PATH, "test.db")
    db = DataBase(TEST_DB_PATH)
    with db.get_db_connection() as db_conn:
        try:
            db_conn.execute(
                "CREATE TABLE {table_name} ({id_field} INTEGER PRIMARY KEY, {date_time} TEXT NOT NULL, {post_data_field} TEXT NOT NULL, {vote_field} INTEGER NOT NULL)"
                    .format(table_name=DataBase.POSTS_TABLE_NAME, id_field=DataBase.ID_FIELD_NAME, date_time=DataBase.DATE_TIME_FIELD_NAME,
                            post_data_field=DataBase.POST_DATA_FIELD_NAME, vote_field=DataBase.VOTES_FIELD_NAME))
        except sqlite3.OperationalError as e:
            pass
        else:
            db_conn.commit()

    print(db.list_posts())
    post_id = db.create_post("bla bla bla").get(DataBase.ID_FIELD_NAME)
    print(db.list_posts())
    print(db.edit_post_data(post_id, "yada yada yada"))
    print(db.list_posts())
    print(db.list_posts())
    print(db.vote_down(post_id))
    print(db.vote_down(post_id))
    print(db.list_posts())
