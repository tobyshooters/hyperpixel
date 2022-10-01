class Annotation {
  constructor(id, imageId, entry, sw, sh, build) {
    this.id = id;
    this.imageId = imageId;
    this.build = build;

    const { x, y, w, h, to } = entry;

    this.bbox = document.createElement("a");
    this.setPos(x, y);
    this.setSize(w, h);
    this.setAnchor(sw, sh);

    this.bbox.addEventListener("click", e => {
      e.stopPropagation();
      if (e.shiftKey) {
        e.preventDefault();
        if (this.to) {
          send({
            op: "DELETE",
            path: ["annotations", this.id],
          })
        }
        this.bbox.remove();
      }
    })
    this.bbox.addEventListener("mousedown", e => e.stopPropagation());

    this.linkInput = document.createElement("input");
    this.linkInput.type = "text";
    this.linkInput.style.width = "100%";
    this.linkInput.addEventListener("change", e => {
      const isInternal = e.target.value[0] === "/";

      if (isInternal) {
        this.setTo(e.target.value.slice(1));
      } else {
        const parts = e.target.value.match(/(https?:\/\/)(.*)/)
        const href = parts ? parts[0] : "https://" + e.target.value;
        this.setTo(href);
      }

      send({
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

    this.linkInput.addEventListener("click", e => e.preventDefault());
    this.linkInput.addEventListener("mouseup", e => e.stopPropagation());
    this.linkInput.addEventListener("mousedown", e => e.stopPropagation());
    this.bbox.appendChild(this.linkInput);

    this.setTo(to || "");

    if (this.to in db["images"]) {
      this.preview = document.createElement("img");
      this.preview.src = "./files/" + db["images"][this.to]["path"];
      this.preview.style.position = "absolute";
      this.preview.style.x = 0;
      this.preview.style.y = 0;
      this.preview.style.width = this.w * this.sw;
      this.preview.style.height = this.h * this.sh - 24;
      this.preview.style.objectFit = "cover";
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

    if (this.preview) {
      this.preview.style.width = this.w * this.sw;
      this.preview.style.height = this.h * this.sh - 24;
    }
  }

  setTo(to) {
    this.to = to;
    if (to.startsWith('http')) {
      this.bbox.href = to;
    } else {
      if (this.build) {
        this.bbox.href = "./" + to + ".html";
      } else{
        this.bbox.href = "./" + to;
      }
    }
    this.linkInput.value = to;
  }

  delete() {
    this.linkInput.remove();
    this.bbox.remove();
  }
}
