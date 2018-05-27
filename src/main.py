import http
import json
from threading import Thread

from bottle import *

import db
from server import MyWSGIRefServer

POST_DATA_PAYLOAD_KEY = 'post_data'

POSTS_PATH = '/posts'
db_obj = db.PostgreSqlDataBase("database", "postgres")
CACHE_PATH = "/tmp/c_nan"
changed = False
posts_list = None
application = Bottle()


@application.hook('before_request')
def strip_path():
    request.environ['PATH_INFO'] = request.environ['PATH_INFO'].rstrip('/')


@application.route(POSTS_PATH, method='POST')
def create_post():
    print(request.headers)
    if not request.content_type == 'application/json':
        return {"error": "not JSON"}
    post_text = request.json.get(POST_DATA_PAYLOAD_KEY)
    if not post_text:
        response.status = http.HTTPStatus.BAD_REQUEST
        return {"error": "No post text was given under {}".format(POST_DATA_PAYLOAD_KEY)}
    post_dict = db_obj.create_post(post_text)
    if post_dict:
        response.status = http.HTTPStatus.CREATED
        update_changed_status(True)
        return post_dict
    response.status = http.HTTPStatus.INTERNAL_SERVER_ERROR
    return {"error": "Failed to create post for {}".format(post_text)}


def update_changed_status(status):
    global changed
    changed = status


def load_from_cache():
    if posts_list is not None:
        print("from mem")
        return posts_list
    with open(CACHE_PATH) as f:
        print("from cache")
        global posts_list
        posts_list = json.load(f)
    return posts_list


def save_to_cache(obj):
    global posts_list
    posts_list = obj
    with open(CACHE_PATH, "w") as f:
        json.dump(obj, f)
    update_changed_status(False)


@application.route(POSTS_PATH, method='GET')
def list_posts():
    is_sort_top = request.query.sort == "top"
    if is_sort_top and os.path.exists(CACHE_PATH) and not changed:
        ret_list = load_from_cache()
    else:
        posts_list = db_obj.list_posts()
        ret_list = posts_list
        if is_sort_top:
            print("calc sort")
            sorted_list = sorted(posts_list, key=lambda k: k[db.DataBase.SCORE_FIELD_NAME], reverse=True)
            save_to_cache(ret_list)
            ret_list = sorted_list
    return {"posts": ret_list}


@application.route('{posts_path}/<post_id:int>'.format(posts_path=POSTS_PATH), method='POST')
def edit_post(post_id):
    print(request.headers)
    if not request.content_type == 'application/json':
        return {"error": "not JSON"}
    post_text = request.json.get(POST_DATA_PAYLOAD_KEY)
    if not post_text:
        response.status = http.HTTPStatus.BAD_REQUEST
        return {"error": "No text was provided for {post_data}".format(post_data=POST_DATA_PAYLOAD_KEY)}
    is_edited = db_obj.edit_post_data(post_id, post_text)
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
    is_vote_registered = db_obj.vote_up(post_id) if action == "upvote" else db_obj.vote_down(post_id)
    if is_vote_registered:
        update_changed_status(True)
        return get_post(post_id)
    else:
        response.status = http.HTTPStatus.NOT_FOUND
        return {"error": "ID {} not found".format(post_id)}


@application.route('{posts_path}/<post_id:int>'.format(posts_path=POSTS_PATH), method='GET')
def get_post(post_id):
    post_data = db_obj.get_post(post_id)
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
