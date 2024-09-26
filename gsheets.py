from gspread import authorize
from google.oauth2.service_account import Credentials
from uuid import uuid4
from dotenv import dotenv_values
from functools import lru_cache

env_variables = dotenv_values()

gsheets_scopes = [env_variables.get('GSHEETS_SCOPES')]
gsheets_credentials = Credentials.from_service_account_file(
    env_variables.get('GSHEETS_CREDENTIALS'), scopes=gsheets_scopes)

gsheets = authorize(gsheets_credentials)

gsheets_workbook_id = env_variables.get('GSHEETS_WORKBOOK_ID')

workbook = gsheets.open_by_key(gsheets_workbook_id)

worksheet_posts = workbook.worksheet('posts')
worksheet_users = workbook.worksheet('users')

_POSTS = []
_USERS = []


def _getIndexByUUID(uuid: str):
    return next((index for index, post in enumerate(_POSTS) if post['uuid'] == uuid), None)


def _postExists(uuid):
    return worksheet_posts.find(uuid)


@lru_cache(maxsize=128)
def getAllPosts():
    global _POSTS
    _POSTS = worksheet_posts.get_all_records()
    return _POSTS if len(_POSTS) > 0 else None

@lru_cache(maxsize=128)
def getAllPostsByUser(email: str):
    global _POSTS
    getAllPosts()
    return [post for post in _POSTS if post['email'] == email]


@lru_cache(maxsize=128)
def getAllPostsExcept(email: str):
    global _POSTS
    getAllPosts()
    return [post for post in _POSTS if post['email'] != email]

def getPostByUUID(uuid: str):
    cell = _postExists(uuid)
    if not cell:
        return None
    row_values = worksheet_posts.row_values(cell.row)
    return {
        'uuid': row_values[0],
        'email': row_values[1],
        'username': row_values[2],
        'title': row_values[3],
        'content': row_values[4],
        'date': row_values[5],
        'time': row_values[6],
    }


def getCachedPostByUUID(uuid: str):
    idx = _getIndexByUUID(uuid)
    getAllPosts.cache_clear()
    if not idx:
        return None
    return _POSTS[idx]


def addPost(values: list):
    global _POSTS
    _UUID = str(uuid4())
    values.insert(0, _UUID)
    values.insert(5, 'date')
    values.insert(6, 'time')
    worksheet_posts.append_row(values)
    _POSTS.insert(0, {
        'uuid': values[0],
        'email': values[1],
        'username': values[2],
        'title': values[3],
        'content': values[4],
        'date': 'date',
        'time': 'time',
    })
    getAllPostsByUser.cache_clear()
    getAllPosts.cache_clear()
    return _POSTS[0]


def updatePost(uuid: str, values: list):
    global _POSTS
    cell = _postExists(uuid)
    if not cell:
        return None
    row_no: int = cell.row
    worksheet_posts.update(range_name=f'D{row_no}:E{row_no}', values=[values])
    getAllPosts.cache_clear()
    getAllPostsByUser.cache_clear()
    idx = _getIndexByUUID(uuid)
    if idx:
        _POSTS[idx] = {
            'title': values[0],
            'content': values[1],
        }
    return _POSTS[idx]


def deletePost(uuid: str):
    cell = _postExists(uuid)
    if not cell:
        return None
    row_no: int = cell.row
    worksheet_posts.delete_rows(row_no)
    idx = _getIndexByUUID(uuid)
    if idx:
        _POSTS.pop(idx)
    getAllPosts.cache_clear()
    getAllPostsByUser.cache_clear()


@lru_cache(maxsize=128)
def getAllUsers():
    global _USERS
    _USERS = worksheet_users.get_all_records()
    return _USERS if len(_USERS) > 0 else None


def addNewUser(email: str, username: str):
    _emails: list = worksheet_users.col_values(1)
    if _emails.count(email) > 0:
        return None
    worksheet_users.append_row([email, username])
    getAllUsers.cache_clear()
    return {
        'email': email,
        'username': username
    }


# debug

# addNewUser('y7l2X@example.com', 'test1')
# addNewUser('e@mail.com', 'homosapiens')
# print(getAllUsers())

# addPost(['e@mail.com', 'homosapiens', 'HTMX is awesome!',
#         "I just learned about HTMX and it's awesome!", 'date', 'time'])
# addPost(['e@mail.com', 'homosapiens', 'This post is generated by ChatGPT',
#         "I'm a robot. I'm writing this post using ChatGPT.", 'date', 'time'])
# addPost(['e@mail.com', 'homosapiens', "I'm tired...",
#         "It's 3am and I want to sleep.", 'date', 'time'])
# addPost(['e@mail.com', 'homosapiens', 'Hello world!',
#         'Hello world!', 'date', 'time'])
# print(getAllPosts())
# deletePost('f3a14334-a4d1-4250-981e-1f4106df30f3')
# updatePost('2493e977-9e99-4be5-9814-14605f512fa0', [
#            'HTMX is awesome ⚡', "I just learned about HTMX and it's awesome!"])
# print(getAllPosts())
