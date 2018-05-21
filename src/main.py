from threading import Thread

from bottle import *

import db
from server import MyWSGIRefServer

CWD_PATH = os.path.dirname(os.path.realpath(__file__))
SRC_ROOT_PATH = os.path.normpath(os.path.join(CWD_PATH, os.path.pardir))

TEST_DB_PATH = os.path.join(SRC_ROOT_PATH, "test.db")

application = Bottle()


@application.hook('before_request')
def strip_path():
    request.environ['PATH_INFO'] = request.environ['PATH_INFO'].rstrip('/')


@application.route('/posts', method='POST')
def create_post():
    print(request.headers)
    if not request.content_type == 'application/json':
        return {"error": "not JSON"}
    post_text = request.json.get('text')
    if post_text:
        new_id = db.DataBase(TEST_DB_PATH).create_post(post_text)
        return {"id": new_id}
    else:
        return {"error": "not sure yet"}


@application.route('/posts', method='GET')
def list_posts():
    posts_list = db.DataBase(TEST_DB_PATH).list_posts()
    return {"posts": posts_list}


def start_server():
    server = MyWSGIRefServer(host='0.0.0.0', port=8080)
    server_thread = Thread(target=application.run, kwargs={"server": server})
    server_thread.start()
    return server


if __name__ == '__main__':
    start_server()
