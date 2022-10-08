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

For publishing, `index.html` and `read.html` are equivalent. This allows for a
read-only static build which can be uploaded to a personal server.

The creation of the static build is done with: `python3 publish.py <directory>`

This secondary code path is quite messy at the moment and has some hard-coded
paths for my own deployment to a blog. Please contact me if you want to figure
that out.

For e.g. I run:
```
cd ~/dev/hyperpixels
python3 publish.py ~/dev/hyperpixel-blog
cp -r build ~/dev/blog/hyperpixel
```

