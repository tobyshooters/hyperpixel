import os
import sys
import json

assert len(sys.argv) == 2
dbpath = sys.argv[1] + "/db.json"

db = json.load(open(dbpath, "r"))

if os.path.exists("build"):
    os.system("rm -rf build")

os.mkdir("build")
os.mkdir("build/files")

os.system("cp index.html build/index.html")
os.system("cp annotation.js build/annotation.js")

with open("build/db.js", "w") as db_f:
    db_f.write("const db = ");
    db_f.write(json.dumps(db))
    db_f.write(";")

for image_id, data in db["images"].items():
    print(f"Processing {image_id}")

    src = f"{sys.argv[1]}/{data['path']}".replace(" ", "\ ")
    os.system(f"cp {src} build/files")

    # Copy read.html template
    target = f"build/{image_id}.html"
    os.system(f"cp read.html {target}")

    # Splice in the image_id
    os.system(f'sed s/%imageId%/{image_id}/ {target} > tmp.html')
    os.system(f'mv tmp.html {target}')
