class Annotation {
  // NOTE: sendDB is set to null on STATIC builds.

  constructor({id, imageId, annotation, otherImages, sendDB}) {
    this.id = id;
    this.imageId = imageId;
    this.sendDB = sendDB;

    const { x, y, w, h, to } = annotation;

    this.bbox = document.createElement("a");
    this.setPos(x, y);
    this.setSize(w, h);

    if (this.sendDB) {
      this.bbox.addEventListener("click", e => {
        e.stopPropagation();
        if (e.shiftKey) {
          e.preventDefault();
          if (this.to) {
            this.sendDB({
              op: "DELETE",
              path: ["annotations", this.id],
            })
          }
          this.bbox.remove();
        }
      })
    }
    this.bbox.addEventListener("mousedown", e => e.stopPropagation());

    this.linkInput = document.createElement("input");
    this.linkInput.type = "text";
    this.linkInput.style.width = "100%";

    if (this.sendDB) {
      this.linkInput.addEventListener("change", e => {
        const isInternal = e.target.value[0] === "/";

        if (isInternal) {
          this.setTo(e.target.value.slice(1));
        } else {
          const parts = e.target.value.match(/(https?:\/\/)(.*)/)
          const href = parts ? parts[0] : "https://" + e.target.value;
          this.setTo(href);
        }

        this.sendDB({
          op: "PUT",
          path: ["annotations", this.id],
          data: {
            type: isInternal ? "internal" : "external",
            from: this.imageId,
            to: this.to,
            x: this.x,
            y: this.y,
            w: this.w,
            h: this.h
          }
        })
      });
    }

    this.linkInput.addEventListener("click", e => e.preventDefault());
    this.linkInput.addEventListener("mouseup", e => e.stopPropagation());
    this.linkInput.addEventListener("mousedown", e => e.stopPropagation());
    this.bbox.appendChild(this.linkInput);

    this.setTo(to || "");

    if (this.to in otherImages) {
      this.preview = document.createElement("img");
      this.previewType = "image";

      this.preview.src = "./files/" + otherImages[this.to]["path"];
      this.preview.style.position = "absolute";
      this.preview.style.x = 0;
      this.preview.style.y = 0;
      this.preview.style.objectFit = "cover";
      this.preview.style.width = this.w * this.sw;
      this.preview.style.height = this.h * this.sh - 24;
      this.bbox.appendChild(this.preview);

    } else if (this.to.startsWith("http")) {
      this.preview = document.createElement("iframe");
      this.previewType = "iframe";

      this.preview.src = this.to;
      this.preview.style.position = "absolute";
      this.preview.style.x = 0;
      this.preview.style.y = 0;
      this.preview.frameBorder = "0";
      this.preview.style.transformOrigin = "0 0";
      this.preview.style.transform = "scale(0.2)";
      this.preview.style.width = 5 * this.w * this.sw;
      this.preview.style.height = 5 * (this.h * this.sh - 24);
      this.bbox.appendChild(this.preview);
    }
  }

  setAnchor(sw, sh) {
    this.sw = sw;
    this.sh = sh;
    this.setPos(this.x, this.y);
    this.setSize(this.w, this.h);
  }

  setPos(x, y) {
    this.x = x;
    this.y = y;
    this.bbox.style.left = (this.x * this.sw) + "px";
    this.bbox.style.top = (this.y * this.sh) + "px";
  }

  setSize(w, h) {
    this.w = w;
    this.h = h;
    this.bbox.style.width = (this.w * this.sw) + "px";
    this.bbox.style.height = (this.h * this.sh) + "px";

    if (this.previewType === "image") {
      this.preview.style.width = this.w * this.sw;
      this.preview.style.height = this.h * this.sh - 24;
    } else if (this.previewType === "iframe") {
      this.preview.style.width = 5 * this.w * this.sw;
      this.preview.style.height = 5 * (this.h * this.sh - 24);
    }
  }

  setTo(to) {
    this.to = to;
    if (to.startsWith('http')) {
      this.bbox.href = to;
    } else {
      if (this.sendDB) {
        this.bbox.href = "./" + to;
      } else{
        this.bbox.href = "./" + to + ".html";
      }
    }
    this.linkInput.value = to;
  }

  delete() {
    this.linkInput.remove();
    this.bbox.remove();
  }
}
