from flask import (
    Flask,
    render_template,
    request
)
import os
import glob
import pickle
from PIL import Image
from collections import defaultdict

app = Flask(__name__, template_folder=".")

if os.path.exists("./static/annotations.pkl"):
    with open('./static/annotations.pkl', 'rb') as f:
        imageAnnotations = pickle.load(f)
else:
    imageAnnotations = defaultdict(dict)

if os.path.exists("./static/backlinks.pkl"):
    with open('./static/backlinks.pkl', 'rb') as f:
        imageBacklinks = pickle.load(f)
else:
    imageBacklinks = defaultdict(list)


@app.route("/")
def index():
    paths = sorted(glob.glob("./static/*.jpg"))
    ids = [p.split("/")[-1].split(".")[0] for p in paths]
    return render_template("listing.html", ids=ids)


@app.route("/<image_id>", methods=['GET', 'POST'])
def image(image_id):
    if request.method == 'POST':
        image = request.files.get('file', '')
        image = Image.open(image)
        image.save(f"./static/{image_id}.jpg")
        return "success", 200
    else:
        annotations = imageAnnotations[image_id]
        backlinks = imageBacklinks[image_id]
        return render_template(
            "edit.html",
            imageId=image_id,
            annotations=annotations,
            backlinks=backlinks,
        )


@app.route("/<image_id>/<annotation_id>", methods=['POST'])
def image_annotation(image_id, annotation_id):
    if request.json:
        imageAnnotations[image_id][annotation_id] = request.json

        # Internal link! Track the backlinks
        if request.json["href"][0] == "/":
            [_, _image_id] = request.json["href"].split("/")
            if os.path.exists(f"./static/{_image_id}.jpg"):
                imageBacklinks[_image_id].append(image_id)

    else:
        if annotation_id in imageAnnotations[image_id]:
            del imageAnnotations[image_id][annotation_id]
            for k, v in imageBacklinks.items():
                imageBacklinks[k] = [x for x in v if x != image_id]


    with open('./static/annotations.pkl', 'wb') as f:
        pickle.dump(imageAnnotations, f)

    with open('./static/backlinks.pkl', 'wb') as f:
        pickle.dump(imageBacklinks, f)

    return "success", 200


if __name__ == "__main__":
    app.run(debug=True)
