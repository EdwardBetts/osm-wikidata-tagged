#!/usr/bin/python3

from flask import Flask, render_template, request, redirect, url_for, jsonify
from lookup import database, model
import re

re_qid = re.compile(r"^Q[1-9]\d+$")

app = Flask(__name__)
app.config.from_object("config.default")
database.init_app(app)


def read_qid_arg():
    qid = request.args.get("qid")
    if not qid:
        return
    qid = qid.strip().upper()
    if not qid:
        return
    if not re_qid.match(qid):
        return

    return qid


def read_bool(field):
    v = request.args.get(field)
    if not v:
        return False
    v = v.strip()
    return v and v != "0"


def do_lookup(qid):
    hits = []
    seen = set()
    for cls in model.Point, model.Polygon, model.Line:
        q = cls.query.filter(cls.tags["wikidata"] == qid)
        for hit in q.all():
            identifier = hit.identifier
            if identifier in seen:
                continue
            seen.add(identifier)
            hits.append(hit)

    return hits


@app.route("/item/<qid>")
def detail_page(qid):
    hits = do_lookup(qid)
    return render_template("index.html", qid=qid, hits=hits)


@app.route("/api/item/<qid>")
def api_item(qid):
    include_geojson = read_bool("geojson")
    include_kml = read_bool("kml")

    hits = []
    for hit in do_lookup(qid):
        hit_dict = {"type": hit.type, "id": hit.id, "tags": hit.tags}
        if include_geojson:
            hit_dict["geojson"] = hit.geojson()
        if include_kml:
            hit_dict["kml"] = hit.kml
        hits.append(hit_dict)

    response = jsonify(wikidata={"qid": qid}, osm=hits)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.route("/")
def index():
    qid = read_qid_arg()
    if qid:
        return redirect(url_for("detail_page", qid=qid))

    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0")
