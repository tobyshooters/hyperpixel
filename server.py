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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/<user>")
def user(user):
    paths = sorted(glob.glob(f"./static/{user}_*.jpg"))
    return render_template("listing.html", user=user, paths=paths)


@app.route("/<user>/<image_id>", methods=['GET', 'POST'])
def user_image(user, image_id):
    if request.method == 'POST':
        image = request.files.get('file', '')
        image = Image.open(image)
        image.save(f"./static/{user}_{image_id}.jpg")
        return "success", 200
    else:
        annotations = imageAnnotations[(user, image_id)]
        return render_template(
            "edit.html",
            user=user,
            imageId=image_id,
            annotations=annotations
        )


@app.route("/<user>/<image_id>/<annotation_id>", methods=['POST'])
def user_image_annotation(user, image_id, annotation_id):
    if request.json:
        imageAnnotations[(user, image_id)][annotation_id] = request.json
    else:
        if annotation_id in imageAnnotations[(user, image_id)]:
            del imageAnnotations[(user, image_id)][annotation_id]

    with open('./static/annotations.pkl', 'wb') as f:
        pickle.dump(imageAnnotations, f)

    return "success", 200


if __name__ == "__main__":
    app.run(debug=True)
