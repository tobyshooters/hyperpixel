import os
import sys
from flask import (
    Flask,
    render_template,
    request,
    send_from_directory
)
import pickle
from PIL import Image

from ocr import ocr

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
                id || href
                x: float[0, 1],
                x: float[0, 1],
                w: float[0, 1],
                h: float[0, 1],
            }
        }
        backlinks: [ id: string ]
    }
}

"""

def hydrate_db():
    """
    Checks <directory> for files that aren't in db yet.
    For convenience, sets the image_id to the path without the extension.
    """
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

            print(f"Saving {f} at {image_id}")
            db[image_id] = {
                "path": f,
                "annotations": {},
                "backlinks": [],
                "text": text,
            }


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


@app.route("/<image_id>", methods=['GET', 'POST'])
def edit(image_id):
    """
    Since the db is specific to a single directory, when an image is uploaded
    via the interface, we persist it at `{directory}/{f}`.
    """
    if request.method == 'GET':
        return render_template(
            "edit.html",
            imageId=image_id,
            data=db.get(image_id, {}),
        )

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
            db[image_id]["path"] = path
            db[image_id]["text"] = text

        return "success", 200


@app.route("/<image_id>/<annotation_id>", methods=['POST'])
def annotate(image_id, annotation_id):
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

    return "success", 200


if __name__ == "__main__":
    try:
        # Load database
        print(f"Running at {directory}")
        if os.path.exists(f"{directory}/db.pkl"):
            with open(f"{directory}/db.pkl", "rb") as f:
                db = pickle.load(f)
        else:
            db = {}

        hydrate_db()

        # Run Flask server
        app.run(debug=True)

    finally:
        # Save db before quiting
        print("Peristing db before quiting.")
        with open(f"{directory}/db.pkl", "wb") as f:
            pickle.dump(db, f)
