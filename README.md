## hyperpixel
Everything is an image.

Install:
- pip: `tornado`,`pillow`
- brew/apt: `tesseract-ocr`


### authoring

To run: `python3 server.py <directory>`

This will listen for new files in `<directory>` as well as persist uploaded
images to  to `<directory>.` The metadata is saved to `<directory>/db.json`.

For authoring, `inbox.html` and `edit.html` correspond to top-level
navigation and individual image editing interfaces.


### publishing

```
cd publish
python3 publish.py <directory>
cd build
python3 -m http.server
open localhost:8000
```

The creation of the static build is done with: `python3 publish.py
<directory>`. For publishing, `index.template` and `read.template` are roughly
equivalent to `inbox` and `edit`, with editing functionality stripped out. This
allows for a read-only static build which can be uploaded to a personal server.
