## hyperpixel

![Preview of system](static/preview.png?raw=true "Title")

Text dominates the software experience. Visual aesthetics are so difficult to
program in the web, that commodity blogging templates have come to dominate.
Everything looks the same.

Hyperpixel is an image-centric authoring specification.

It is built on two core primitive: images and transcluded links.
- Each image is hosted at a URL
- Sub-regions of an image can link to other URLs
- Backlinks are present

You navigate through the graph of images by clicking on links, much like
traditional hypertext. What makes this different is the authoring experience:
*instead of opening up a text-editor, pull out a pen and paper, open up
photoshop, or take some screenshots.*

### authoring

Hyperpixel is built with a very simple local server pattern. You run the server
on your local computer, and ask it to point to some directory of files on your
filesystem. It more-or-less follows
[this](https://gist.github.com/tobyshooters/5aa0b729e961661156f903817e56226b)
vanilla js micro-framework.

```
> python3 server.py <directory>
```

The system has two kinds of pages:
1. *Inbox* at `localhost:1234/`, corresponding to `inbox.html`
2. *Image pages* at `localhost:1234/<image-id>`, corresponding to `edit.html`

To add a new image into the system, you can navigate to an
`localhost:1234/<url>` and either use the file picker or drag-and-drop onto
page.

Once on an *image page* with an image, you can create a link by clicking and
dragging and then typing a URL in the white address bar. Local URLs to other
images are prefixed with `/`, but you can also just link to an existing URL on
the world wide web.

You can delete links with a shift-click.

The system is synchronized with a single `<directory>` of your filesystem. It
will listen for new files in `<directory>` as well as persist uploaded images
to `<directory>`. The metadata with associated OCR, links, and backlinks is
saved to `<directory>/db.json`.

Existing images show up in the *inbox*. If an image is already within the link
network, it'll show up in the left column. Unlinked images show up in the
right.

You can search for images from the *inbox*. This relies on OCR detection.


### requirements

- pip: `tornado`,`pillow`
- brew/apt: `tesseract-ocr`


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
