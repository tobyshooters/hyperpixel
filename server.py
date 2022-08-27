from flask import (
    Flask,
    render_template,
    request
)
import os
import pickle
from PIL import Image

app = Flask(__name__, template_folder=".")

"""
db = {
    id: {
        path: string
        annotations; {
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
if os.path.exists("./static/db.pkl"):
    with open('./static/db.pkl', 'rb') as f:
        db = pickle.load(f)
else:
    db = {}


@app.route("/")
def index():
    data = {
        k: v["path"]
        for k, v in db.items()
    }
    return render_template("listing.html", data=data)


@app.route("/<image_id>", methods=['GET', 'POST'])
def image(image_id):
    if request.method == 'POST':
        f = request.files.get('file', '')
        image = Image.open(f)
        path = f"./static/{f.filename}"
        image.save(path)

        db[image_id] = {
            "path": path,
            "annotations": {},
            "backlinks": []
        }

        return "success", 200
    else:
        return render_template(
            "edit.html",
            imageId=image_id,
            data=db.get(image_id, {}),
        )


@app.route("/<image_id>/<annotation_id>", methods=['POST'])
def image_annotation(image_id, annotation_id):
    if request.json:
        db[image_id]["annotations"][annotation_id] = request.json

        # Internal link! Track the backlinks
        if request.json["href"][0] == "/":
            [_, _image_id] = request.json["href"].split("/")

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

    with open('./static/db.pkl', 'wb') as f:
        pickle.dump(db, f)

    return "success", 200


if __name__ == "__main__":
    app.run(debug=True)
