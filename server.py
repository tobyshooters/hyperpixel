from flask import (
    Flask,
    render_template,
    request
)
import glob
from PIL import Image

app = Flask(__name__, template_folder=".")


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/<user>")
def user(user):
    paths = glob.glob(f"./static/{user}_*.jpg")
    return render_template("listing.html", user=user, paths=paths)

@app.route("/<user>/<image_id>", methods=['GET', 'POST'])
def user_image(user, image_id):
    if request.method == 'POST':
        image = request.files.get('file', '')
        image = Image.open(image)
        image.save(f"./static/{user}_{image_id}.jpg")
        return "success", 200
    else:
        return render_template("edit.html", user=user, imageId=image_id)
