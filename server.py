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
            self.db = {
                "images": {},
                "annotations": {}
            }

        self.hydrate()


    def persist(self):
        with open(f"{directory}/db.json", "w") as f:
            json.dump(self.db, f, indent=2)


    def hydrate(self):
        existing_images = [
            data["path"]
            for data in self.db["images"].values()
        ]

        files_in_directory = os.listdir(self.directory)

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

        self.persist()


    def op(self, op, path, data):
        print("OP:", op, path, data)

        if op == "SUBSCRIBE":
            self.callbacks.append(data)
            data(self.db)

        if op == "PUT":
            location = self.db
            for i in range(len(path) - 1):
                location = location[path[i]]

            location[path[-1]] = data

        if op == "DELETE":
            location = self.db
            for i in range(len(path) - 1):
                location = location[path[i]]

            if path[0] == "images":
                f = location[path[-1]]["path"]
                os.remove(os.path.join(self.directory, f))

            del location[path[-1]]

        if op == "RENAME":
            old_image_id = path[-1]
            new_image_id = data
            self.rename(old_image_id, new_image_id)


        for cb in self.callbacks:
            cb(self.db)

        self.persist()


    def rename(self, old_image_id, new_image_id):
        dup = copy.deepcopy(self.db["images"][old_image_id])
        self.db["images"][new_image_id] = dup

        del self.db["images"][old_image_id]

        for a_id, annotation in self.db["annotations"].items():

            if annotation["from"] == old_image_id:
                annotation["from"] = new_image_id

            if annotation["to"] == old_image_id:
                annotation["to"] = new_image_id

        self.persist()



if len(sys.argv) == 2:
    directory = os.path.expanduser(sys.argv[1])
else:
    directory = "./static"

db = DB(directory)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("listing.html")


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
            def cb(db):
                if self.ws_connection:
                    self.write_message(json.dumps(db))

            db.op("SUBSCRIBE", message["path"], cb)

        else:
            data = message["data"] if "data" in message  else None
            db.op(message["op"], message["path"], data)


if __name__ == "__main__":
    app = tornado.web.Application([
        (r'/files/(.*)', tornado.web.StaticFileHandler, {
            "path": directory 
        }),
        (r'/ws', WSHandler),
        (r'/upload', UploadHandler),
        (r'/', IndexHandler),
        (r'/(.*)', EditHandler),
    ], debug=True)

    app.listen(5000)
    tornado.ioloop.IOLoop.current().start()

