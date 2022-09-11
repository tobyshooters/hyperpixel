import os
import json
import sys
import signal
import subprocess
import pickle
import random
import copy

from flask import (
    Flask,
    render_template,
    request,
    send_from_directory
)

from PIL import Image

if len(sys.argv) == 2:
    directory = os.path.expanduser(sys.argv[1])
else:
    directory = "./static"

app = Flask(__name__, template_folder=".")

schema = """
db = {
    id: {
        path: string
        text: string
        annotations: {
            id: {
                type: "internal" | "external",
                href: string,
                x: float[0, 1],
                y: float[0, 1],
                w: float[0, 1],
                h: float[0, 1],
            }
        }
        backlinks: [ id: string ]
    }
}

"""

def ocr(path):
    path.replace(" ", "\ ")
    cmd = ["tesseract", path, "stdout"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return p.stdout


def move(db, old, new):
    # Copy over data to new id
    db[new] = copy.deepcopy(db[old])
    del db[old]

    # Loop through things that point at old
    for imageId in db[new]["backlinks"]:
        for a in db[imageId]["annotations"].values():
            if a["type"] == "internal" and a["href"][1:] == old:
                print(f"Moving link at {imageId} from {old} to {new}")
                a["href"] = "/" + new

    # Loop through things old points at
    for a in db[new]["annotations"].values():
        if a["type"] == "internal":
            print(f"Moving backlink at {a['href']} from {old} to {new}")
            db[a["href"]]["backlinks"].remove(old)
            db[a["href"]]["backlinks"].append(new)

    with open(f"{directory}/db.pkl", "wb") as f:
        pickle.dump(db, f)

    return db


def hydrate_db():
    """
    Checks <directory> for files that aren't in db yet.
    For convenience, sets the image_id to the path without the extension.
    """
    global db
    existing = [e["path"] for e in db.values()]

    for f in os.listdir(directory):
        ext = f.split(".")[-1]
        if ext not in ["jpeg", "jpg", "png"]:
            continue

        if f not in existing:
            image_id = f.replace(".", "_").replace(" ", "_")
            dest = os.path.join(directory, f)
            print(f"Loading {f} from {dest}")

            text = ocr(dest).lower()

            db[image_id] = {
                "path": f,
                "annotations": {},
                "backlinks": [], 
                "text": text,
            }

    with open(f"{directory}/db.pkl", "wb") as f:
        pickle.dump(db, f)


@app.route("/files/<filename>")
def file(filename):
    """
    We serve static files with the `/files/` prefix.
    This is to support serving files from an arbitrary <directory>.

    The value of data specifies the endpoint that needs to be hit to serve the
    file. Thus, if a file is at `{directory}/{f}`, its value is `{files}/{f}`

    Note, the image_id is independent of f.
    """
    return send_from_directory(directory, filename)


@app.route("/")
def index():
    global db
    hydrate_db()
    query = request.args.get('query')

    if query:
        data = {
            k: os.path.join("files", v["path"] )
            for k, v in db.items()
            if query.lower() in v["text"]
            or query.lower() in k.lower()
        }
    else:
        data = {
            k: os.path.join("files", v["path"] )
            for k, v in db.items()
        }

    return render_template("listing.html", data=data, query=query)


@app.route("/<image_id>", methods=['GET', 'POST', 'DELETE'])
def edit(image_id):
    """
    Since the db is specific to a single directory, when an image is uploaded
    via the interface, we persist it at `{directory}/{f}`.
    """
    global db
    if request.method == 'GET':
        links = {
            # TODO: slicing off / is weird!
            a["href"]: os.path.join("files", db[a["href"][1:]]["path"])
            for a in db[image_id]["annotations"].values()
        }
        return render_template(
            "edit.html",
            imageId=image_id,
            data=db.get(image_id, {}),
            links=links,
        )

    elif request.method == 'DELETE':
        f = db[image_id]["path"]
        dest = os.path.join(directory, f)
        if os.path.exists(dest):
            os.remove(dest)
        del db[image_id]

        with open(f"{directory}/db.pkl", "wb") as f:
            pickle.dump(db, f)

        return "ok"

    else:
        f = request.files.get('file', '')
        image = Image.open(f)
        dest = os.path.join(directory, f.filename)
        image.save(dest)

        # Run OCR on image
        text = ocr(dest).lower()

        if image_id not in db:
            db[image_id] = {
                "path": f.filename,
                "annotations": {},
                "backlinks": [],
                "text": text
            }
        else:
            # Preserves annotations + backlinks
            db[image_id]["path"] = f.filename
            db[image_id]["text"] = text

        with open(f"{directory}/db.pkl", "wb") as f:
            pickle.dump(db, f)

        return "success", 200


@app.route("/<image_id>/<annotation_id>", methods=['POST'])
def annotate(image_id, annotation_id):
    global db
    if request.json:
        db[image_id]["annotations"][annotation_id] = request.json

        # Internal link! Track the backlinks
        if request.json["href"][0] == "/":
            _image_id = request.json["href"].split("/")[1]

            if _image_id in db:
                db[_image_id]["backlinks"].append(image_id)

    else:
        if annotation_id in db[image_id]["annotations"]:
            del db[image_id]["annotations"][annotation_id]
            for entry in db.values():
                entry["backlinks"] = [
                    other_id
                    for other_id in entry["backlinks"]
                    if other_id != image_id
                ]

    with open(f"{directory}/db.pkl", "wb") as f:
        pickle.dump(db, f)

    return "success", 200


@app.route("/rename", methods=['POST'])
def rename():
    global db
    move(db, request.json["from"], request.json["to"])
    return "success", 200


if __name__ == "__main__":
    # Load database
    print(f"Running at {directory}")
    if os.path.exists(f"{directory}/db.pkl"):
        with open(f"{directory}/db.pkl", "rb") as f:
            db = pickle.load(f)
            print(db.keys())
    else:
        db = {}

    # Run Flask server
    app.run(debug=True)
