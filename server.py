import os
import json
import sys
import signal
import subprocess
import json
import random
import copy
import io
from PIL import Image

import tornado.ioloop
import tornado.web
import tornado.websocket


def ocr(path):
    path.replace(" ", "\ ")
    cmd = ["tesseract", path, "stdout"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return p.stdout


class DB:
    """
    db = {
        images: {
            id: {
                path: string
                text: string
            }
        }
        annotations: {
            id: {
                type: "internal" | "external",
                from: image_id,
                to: image_id | href,

                x: float[0, 1],
                y: float[0, 1],
                w: float[0, 1],
                h: float[0, 1],
            }
        }
    }
    """

    def __init__(self, directory):
        self.directory = directory
        self.path = f"{directory}/db.json"
        self.callbacks = []

        if os.path.exists(self.path):
            with open(self.path, "r") as f:
                self.db = json.load(f)
        else:
            self.db = { "images": {}, "annotations": {} }

        self.hydrate_from_fs()

        with open(f"{directory}/db.json", "w") as f:
            json.dump(self.db, f, indent=2)


    def hydrate_from_fs(self):
        files_in_directory = os.listdir(self.directory)
        existing_images = [data["path"] for data in self.db["images"].values()]

        # Clean up images removed from file system
        to_delete = []
        for image_id, data in self.db["images"].items():
            if data["path"] not in files_in_directory:
                to_delete.append(image_id)

        for image_id in to_delete:
            del self.db["images"][image_id]

        # Load new images in the filesystem
        for f in files_in_directory:
            ext = f.split(".")[-1]
            if ext.lower() not in ["jpeg", "jpg", "png"]:
                continue

            if f not in existing_images:
                image_id = f.replace(".", "_").replace(" ", "_")
                dest = os.path.join(self.directory, f)
                print(f"Loading {f} from {dest}")

                text = ocr(dest).lower()

                self.db["images"][image_id] = {
                    "path": f,
                    "text": text,
                }


    def op(self, op, path, data):
        print("OP:", op, path, data)

        location = self.db
        for i in range(len(path) - 1):
            location = location[path[i]]

        if op == "SUBSCRIBE":
            # Add a function that's called on DB changes
            self.callbacks.append(data)

        elif op == "PUT":
            # Update data at a specific path of the DB
            location[path[-1]] = data

        elif op == "UPDATE":
            # Update data at a specific path of the DB
            location[path[-1]].update(data)

        if op == "DELETE":
            # Delete data at a specific path of the DB
            # Side effect: delete's images from the directory
            if path[0] == "images":
                f = location[path[-1]]["path"]
                os.remove(os.path.join(self.directory, f))

            del location[path[-1]]

        if op == "RENAME":
            # Reassign an image id, and propagate changes to DB
            old_image_id = path[-1]
            new_image_id = data

            dup = copy.deepcopy(self.db["images"][old_image_id])
            self.db["images"][new_image_id] = dup
            del self.db["images"][old_image_id]

            # Apply to all the annotations
            for a_id, annotation in self.db["annotations"].items():
                if annotation["from"] == old_image_id:
                    annotation["from"] = new_image_id
                if annotation["to"] == old_image_id:
                    annotation["to"] = new_image_id

        self.hydrate_from_fs()

        for cb in self.callbacks:
            cb(self.db)

        with open(f"{directory}/db.json", "w") as f:
            json.dump(self.db, f, indent=2)



if len(sys.argv) == 2:
    directory = os.path.expanduser(sys.argv[1])
else:
    directory = "./static"

db = DB(directory)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("inbox.html")


class EditHandler(tornado.web.RequestHandler):
    def get(self, image_id):
        self.render("edit.html")


class UploadHandler(tornado.web.RequestHandler):
    def post(self):
        image_id = self.get_argument("image_id")
        f = self.request.files.get('file', '')[0]

        dest = os.path.join(directory, f["filename"])
        with open(dest, "wb") as image:
            image.write(f["body"])

        text = ocr(dest).lower()

        db.op("PUT", ["images", image_id], {
            "path": f["filename"],
            "text": text,
        })

        self.write("ok")


class WSHandler(tornado.websocket.WebSocketHandler):
    def on_message(self, message):
        message = json.loads(message)

        if message["op"] == "SUBSCRIBE":
            def on_update(db):
                if self.ws_connection:
                    self.write_message(json.dumps(db))

            message["data"] = on_update

        db.op(message["op"], message["path"], message.get("data"))


if __name__ == "__main__":
    app = tornado.web.Application([
        (r'/files/(.*)', tornado.web.StaticFileHandler, { "path": directory }),
        (r'/js/(.*)', tornado.web.StaticFileHandler, { "path": "." }),
        (r'/ws', WSHandler),
        (r'/upload', UploadHandler),
        (r'/', IndexHandler),
        (r'/(.*)', EditHandler),
    ], debug=True)

    app.listen(1234)
    tornado.ioloop.IOLoop.current().start()
