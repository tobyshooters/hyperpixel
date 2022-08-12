from PIL import Image
from flask import (
    Flask,
    render_template,
    request
)

app = Flask(__name__, template_folder=".")


@app.route("/")
@app.route("/<user>")
@app.route("/<user>/<image_id>")
def user(user=None, image_id=None):
    return render_template("index.html", user=user, imageId=image_id)


@app.route("/<user>/<image_id>", methods=['POST'])
def user_image(user, image_id):
    image = request.files.get('file', '')
    image = Image.open(image)
    image.save(f"static/{user}_{image_id}.jpg")
    return f"success", 200

