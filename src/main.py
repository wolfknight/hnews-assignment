import http
from threading import Thread

from bottle import *

import db
from server import MyWSGIRefServer

POSTS_PATH = '/posts'

CWD_PATH = os.path.dirname(os.path.realpath(__file__))
SRC_ROOT_PATH = os.path.normpath(os.path.join(CWD_PATH, os.path.pardir))

TEST_DB_PATH = os.path.join(SRC_ROOT_PATH, "test.db")

application = Bottle()


@application.hook('before_request')
def strip_path():
    request.environ['PATH_INFO'] = request.environ['PATH_INFO'].rstrip('/')


@application.route(POSTS_PATH, method='POST')
def create_post():
    print(request.headers)
    if not request.content_type == 'application/json':
        return {"error": "not JSON"}
    post_text = request.json.get('post_data')
    if post_text:
        post_dict = db.DataBase(TEST_DB_PATH).create_post(post_text)
        response.status = http.HTTPStatus.CREATED
        return post_dict
    else:
        return {"error": "not sure yet"}


@application.route(POSTS_PATH, method='GET')
def list_posts():
    posts_list = db.DataBase(TEST_DB_PATH).list_posts()
    return {"posts": posts_list}


@application.route('{posts_path}/<post_id:int>'.format(posts_path=POSTS_PATH), method='POST')
def edit_post(post_id):
    print(request.headers)
    if not request.content_type == 'application/json':
        return {"error": "not JSON"}
    post_text = request.json.get('post_data')
    if not post_text:
        response.status = http.HTTPStatus.BAD_REQUEST
        return {"error": "No post_data was provided"}
    is_edited = db.DataBase(TEST_DB_PATH).edit_post_data(post_id, post_text)
    if is_edited:
        return get_post(post_id)
    else:
        response.status = http.HTTPStatus.NOT_FOUND
        return {"error": "ID {} not found".format(post_id)}


@application.route('{posts_path}/<post_id:int>/<action>'.format(posts_path=POSTS_PATH), method='POST')
def vote_post(post_id, action):
    actions_list = ['downvote', 'upvote']
    if action not in actions_list:
        response.status = http.HTTPStatus.BAD_REQUEST
        return {"error": "Only the following actions are allowed {}".format(actions_list)}
    if not request.content_type == 'application/json':
        return {"error": "not JSON"}
    is_vote_registered = db.DataBase(TEST_DB_PATH).vote_up(post_id) if action == "upvote" else db.DataBase(TEST_DB_PATH).vote_down(post_id)
    if is_vote_registered:
        return get_post(post_id)
    else:
        response.status = http.HTTPStatus.NOT_FOUND
        return {"error": "ID {} not found".format(post_id)}


@application.route('{posts_path}/<post_id:int>'.format(posts_path=POSTS_PATH), method='GET')
def get_post(post_id):
    post_data = db.DataBase(TEST_DB_PATH).get_post(post_id)
    if post_data is None:
        response.status = http.HTTPStatus.NOT_FOUND
        return {"error": "ID {} not found".format(post_id)}
    return post_data


def start_server():
    server = MyWSGIRefServer(host='0.0.0.0', port=8080)
    server_thread = Thread(target=application.run, kwargs={"server": server})
    server_thread.start()
    return server


if __name__ == '__main__':
    start_server()
