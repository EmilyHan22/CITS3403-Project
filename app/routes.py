from flask import Blueprint, render_template
import datetime

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    return render_template("index.html", current_year=datetime.date.today().year)

@bp.route("/share")
def share():
    return render_template("shareview.html", current_year=datetime.date.today().year)

@bp.route("/visualise")
def visualise():
    return render_template("visualise.html", current_year=datetime.date.today().year)
