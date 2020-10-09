from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

bp = Blueprint("blog", __name__)


@bp.route("/")
def index():
    """Show all the posts, most recent first."""
    db = get_db()
    posts = db.execute(
        "SELECT p.id, body, mood, date, created, author_id, username"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    pposts =[]
    for post in posts:
        try:
            if post["author_id"] == g.user["id"]:
                pposts.append(post)
        except TypeError:
            pass

    return render_template("blog/index.html", posts=pposts)


def get_post(id, check_author=True):
    """Get a post and its author by id.

    Checks that the id exists and optionally that the current user is
    the author.

    :param id: id of post to get
    :param check_author: require the current user to be the author
    :return: the post with author information
    :raise 404: if a post with the given id doesn't exist
    :raise 403: if the current user isn't the author
    """
    post = (
        get_db()
        .execute(
            "SELECT p.id, body, mood, date, created, author_id, username"
            " FROM post p JOIN user u ON p.author_id = u.id"
            " WHERE p.id = ?",
            (id,),
        )
        .fetchone()
    )

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))
    check_author=True
    if check_author and post["author_id"] != g.user["id"]:
        abort(403)

    return post


@bp.route("/create", methods=("GET", "POST"))
@login_required
def create():
    """Create a new post for the current user."""
    if request.method == "POST":
        body = request.form["body"]
        mood = request.form["mood"]        
        date = request.form["date"]
        error = None

        if not mood:
            error = "Mood is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO post (body, mood, date, author_id) VALUES (?, ?, ?, ?)",
                (body, mood, date, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/create.html")


@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    """Update a post if the current user is the author."""
    post = get_post(id)

    if request.method == "POST":
        body = request.form["body"]
        mood = request.form["mood"]
        date = request.form["date"]
        error = None

        if not mood:
            error = "Mood is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE post SET body = ?, mood = ?, date = ? WHERE id = ?", (body, mood, date, id)
            )
            db.commit()
            return redirect(url_for("blog.index"))

    return render_template("blog/update.html", post=post)


@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    """Delete a post.

    Ensures that the post exists and that the logged in user is the
    author of the post.
    """
    get_post(id)
    db = get_db()
    db.execute("DELETE FROM post WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("blog.index"))

@bp.route("/tracker")
@login_required
def tracker():
    db = get_db()
    posts = db.execute(
        "SELECT p.id, body, mood, date, created, author_id, username"
        " FROM post p JOIN user u ON p.author_id = u.id"
        " ORDER BY created DESC"
    ).fetchall()
    pposts =[]
    xposts =[]

    for i in range(30):
        xposts.append(0)

    for post in posts:
        try:
            if post["author_id"] == g.user["id"]:
                pposts.append(post)
        except TypeError:
            pass
    
    numbers = [1,2,3,4,5]

    for ppost in pposts:
        if ppost["mood"] in numbers:
            xposts[int(ppost['date'].day)-1]=ppost["mood"]
    

    return render_template("blog/tracker.html", posts=xposts)
