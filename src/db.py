import sqlite3


class DataBase(object):
    def __init__(self, db_location) -> None:
        super().__init__()
        self.db_location = db_location
        self.table_name = "posts"
        self.DEFAULT_SCORE = 0

    @staticmethod
    def _get_post_dict(post_values):
        ret_dict_keys = ("id", "post_data", "score")
        post_dict = dict(zip(ret_dict_keys, post_values))
        return post_dict

    def get_db_connection(self):
        return sqlite3.connect(self.db_location)

    def create_post(self, post_data):
        with self.get_db_connection() as db_connection:
            db_cursor = db_connection.cursor()
            try:
                db_cursor.execute("INSERT INTO {table_name} (post_data,score) VALUES (?,?)"
                                  .format(table_name=self.table_name), (post_data, self.DEFAULT_SCORE))
                new_id = db_cursor.lastrowid
                db_connection.commit()
            finally:
                db_cursor.close()
        return self._get_post_dict((new_id, post_data, self.DEFAULT_SCORE))

    def _get_posts_list(self):
        with self.get_db_connection() as db_connection:
            db_cursor = db_connection.cursor()
            try:
                db_cursor.execute("SELECT id, post_data, score FROM {table_name}".format(table_name=self.table_name))
                result = db_cursor.fetchall()
            finally:
                db_cursor.close()
        return result

    def list_posts(self):
        posts_list = self._get_posts_list()
        return [self._get_post_dict(post_tuple) for post_tuple in posts_list]

    def get_post(self, post_id):
        with self.get_db_connection() as db_connection:
            db_cursor = db_connection.cursor()
            try:
                db_cursor.execute("SELECT id, post_data, score FROM {table_name} WHERE id LIKE ?".format(table_name=self.table_name), (post_id,))
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
                db_cursor.execute("UPDATE {table_name} SET post_data = ? WHERE id LIKE ?".format(table_name=self.table_name), (post_data, post_id))
                db_cursor.fetchone()
            finally:
                db_cursor.close()
        post = self.get_post(post_id)
        return post is not None and post["post_data"] == post_data

    def _edit_post_score(self, post_id, is_up):
        post = self.get_post(post_id)
        if post is None:
            return False
        post_score = post.get("score", self.DEFAULT_SCORE)
        new_post_score = post_score + 1 if is_up else post_score - 1
        with self.get_db_connection() as db_connection:
            db_cursor = db_connection.cursor()
            try:
                db_cursor.execute("UPDATE {table_name} SET score = ? WHERE id LIKE ?".format(table_name=self.table_name),
                                  (new_post_score, post_id))
                db_cursor.fetchone()
            finally:
                db_cursor.close()
        new_post = self.get_post(post_id)
        return new_post is not None and new_post.get("score") == new_post_score

    def vote_up(self, post_id):
        return self._edit_post_score(post_id, True)

    def vote_down(self, post_id):
        return self._edit_post_score(post_id, False)


if __name__ == '__main__':
    import os
    CWD_PATH = os.path.dirname(os.path.realpath(__file__))
    SRC_ROOT_PATH = os.path.normpath(os.path.join(CWD_PATH, os.path.pardir))

    TEST_DB_PATH = os.path.join(SRC_ROOT_PATH, "test.db")
    db = DataBase(TEST_DB_PATH)
    with db.get_db_connection() as db_conn:
        try:
            db_conn.execute(
                "CREATE TABLE %s (id INTEGER PRIMARY KEY, post_data TEXT NOT NULL, score INTEGER NOT NULL)" % "posts")
        except sqlite3.OperationalError as e:
            pass
        else:
            db_conn.commit()

    print(db.list_posts())
    post_id = db.create_post("bla bla bla").get("id")
    print(db.list_posts())
    print(db.edit_post_data(post_id, "yada yada yada"))
    print(db.list_posts())
    print(db.vote_up(post_id))
    print(db.list_posts())
    print(db.vote_down(post_id))
    print(db.vote_down(post_id))
    print(db.list_posts())
