from flask import Flask, redirect, render_template, request, session, url_for
from dotenv import dotenv_values, load_dotenv
from authlib.integrations.flask_client import OAuth
import gsheets
from pathlib import Path
from os import getenv


app = Flask(__name__)

load_dotenv(Path('/etc/secrets/.env'))

app_config = {
    'OAUTH2_CLIENT_ID': getenv('OAUTH2_CLIENT_ID'),
    'OAUTH2_CLIENT_SECRET': getenv('OAUTH2_CLIENT_SECRET'),
    'OAUTH2_META_URL': getenv('OAUTH2_META_URL'),
    'SECRET_KEY': getenv('FLASK_SECRET_KEY'),
}

app.secret_key = app_config['SECRET_KEY']

oauth = OAuth(app)
oauth.register(
    name='FlaskX',
    client_id=app_config['OAUTH2_CLIENT_ID'],
    client_secret=app_config['OAUTH2_CLIENT_SECRET'],
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=app_config["OAUTH2_META_URL"],
)


@app.route("/sign-in")
def signIn():
    redirect_uri = url_for("signInWithGoogle", _external=True)
    return oauth.FlaskX.authorize_redirect(redirect_uri)


@app.route("/sign-in-with-google")
def signInWithGoogle():
    token = oauth.FlaskX.authorize_access_token()
    session['user'] = token
    gsheets.addNewUser(session.get('user')['userinfo']['email'], session.get(
        'user')['userinfo']['name'])
    return redirect(url_for('home'))


@app.route("/sign-out")
def signOut():
    session.pop('user', None)
    return redirect(url_for('home'))


@app.route("/")
def home():
    all_posts = None
    if session.get('user'):
        all_posts = gsheets.getAllPostsByUser(
            session.get('user')['userinfo']['email'])
    return render_template("home/index.html", posts=all_posts, session=session.get('user'))
#  pretty=json.dumps(session.get('user'), indent=4)


@app.route("/posts")
def posts():
    if session.get('user') is None:
        return redirect(url_for('home'))
    all_posts = gsheets.getAllPostsExcept(
        session.get('user')['userinfo']['email'])
    return render_template("posts/index.html", posts=all_posts, session=session.get('user'),)


@app.route("/posts/new", methods=["POST"])
def addPost():
    if session.get('user') is None:
        return redirect(url_for('home'))
    post = gsheets.addPost([session.get('user')['userinfo']['email'], session.get(
        'user')['userinfo']['name'], request.form.get(
            "title"), request.form.get("content")])
    return render_template("posts/_partials/post_template.html", post=post, session=session.get('user'))


@app.route("/post/<string:post_id>", methods=["GET"])
def showPost(post_id=None, post=None):
    if session.get('user') is None:
        return redirect(url_for('home'))
    post = post if post_id is None else gsheets.getPostByUUID(post_id)
    return render_template("posts/_partials/post_template.html", post=post, session=session.get('user'))


@app.route("/posts/edit/<string:post_id>", methods=["GET", "PUT"])
def editPost(post_id):
    if session.get('user') is None:
        return redirect(url_for('home'))
    if request.method == "PUT":
        post = gsheets.updatePost(post_id, [request.form.get(
            "title"), request.form.get("content")])
        return showPost(post_id=post_id)
    post = gsheets.getPostByUUID(post_id)
    return render_template("posts/_partials/edit.html", post=post, session=session.get('user'))


@app.route("/post/<string:post_id>/delete", methods=["DELETE"])
def deletePost(post_id):
    if session.get('user') is None:
        return redirect(url_for('home'))
    gsheets.deletePost(post_id)
    return ''


@app.route("/users")
def users():
    if session.get('user') is None:
        return redirect(url_for('home'))
    all_users = gsheets.getAllUsers()
    return render_template("users/index.html", users=all_users, session=session.get('user'),)

if __name__ == "__main__":
    app.run()
