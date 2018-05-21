import sqlite3


class DataBase(object):
    def __init__(self, db_location) -> None:
        super().__init__()
        self.db_location = db_location
        self.table_name = "posts"
        self.DEFAULT_SCORE = 0

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
        return new_id

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
        return [{"id": post_tuple[0], "data": post_tuple[1], "score": post_tuple[2]} for post_tuple in posts_list]


if __name__ == '__main__':
    import os
    CWD_PATH = os.path.dirname(os.path.realpath(__file__))
    SRC_ROOT_PATH = os.path.normpath(os.path.join(CWD_PATH, os.path.pardir))

    TEST_DB_PATH = os.path.join(SRC_ROOT_PATH, "test.db")
    db = DataBase(TEST_DB_PATH)
    print(db.list_posts())
    db.create_post("bla bla bla")
    print(db.list_posts())
    db.create_post("bla bla bla")
    print(db.list_posts())
    db.create_post("bla bla bla")
    print(db.list_posts())
