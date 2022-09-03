import subprocess

def ocr(path):
    path.replace(" ", "\ ")
    cmd = ["tesseract", path, "stdout"]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
    return p.stdout

if __name__ == "__main__":
    ocr("/Users/cristobal/Desktop/influencer.png")
