from flask import Blueprint, render_template, request, redirect, url_for
import datetime

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    return render_template("index.html", current_year=datetime.date.today().year)

@bp.route("/shareview")
def share():
    return render_template("shareview.html", current_year=datetime.date.today().year)

@bp.route("/visualise")
def visualise():
    return render_template("visualise.html", current_year=datetime.date.today().year)

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # for now, accept anything and go to the podcast-logging page
        return redirect(url_for("main.podcast_log"))
    return render_template("login.html", current_year=datetime.date.today().year)

@bp.route("/podcast-log", methods=["GET", "POST"])
def podcast_log():
    if request.method == "POST":
        # grab form data (you can save to DB here later)
        title    = request.form.get("title")
        series   = request.form.get("series")
        time     = request.form.get("time")
        genre    = request.form.get("genre")
        platform = request.form.get("platform")
        rating   = request.form.get("rating")
        # for now, just redirect back to the form
        return redirect(url_for("main.podcast_log"))

    return render_template("PodcastLog.html", current_year=datetime.date.today().year)

@bp.route("/frienddash")
def frienddash():
    return render_template("frienddash.html", current_year=datetime.date.today().year)

@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # grab form data if you want:
        first = request.form["first_name"]
        last  = request.form["last_name"]
        user  = request.form["username"]
        email = request.form["email"]
        pwd   = request.form["password"]
        # for now, ignore and just send them into the app:
        return redirect(url_for("main.podcast_log"))
    return render_template("signup.html", current_year=datetime.date.today().year)
