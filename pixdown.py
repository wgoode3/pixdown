from bs4 import BeautifulSoup
import os, sys, shutil, requests, re, glob, imageio

help_dialog = "please specify the pixiv url wrapped in quotes \"image_url\""
image_url = "https://i.pximg.net/img-original/img/"
mode = ".jpg"

"""
natural sorting from:
https://blog.codinghorror.com/sorting-for-humans-natural-sort-order/
"""

def sort_nicely(l):
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    l.sort(key=alphanum_key)

def gifify(folder_name):
    filenames = glob.glob("{}/*{}".format(folder_name, mode))
    sort_nicely(filenames)
    images = []
    for filename in filenames:
        images.append(imageio.imread(filename))

    gif_filename = folder_name + "x.gif"
    imageio.mimsave(gif_filename, images, format='GIF', duration=0.1)

if len(sys.argv) == 1:
    print help_dialog
else:
    base_url = sys.argv[1]
    image_id = base_url.split("=")[-1]
    soup = BeautifulSoup(requests.get(base_url).text, 'html.parser')
    os.makedirs(str(image_id))
    src = ""
    for img in soup.find_all('img'):
      if image_id in img['src']:
          src = img['src']
          break
    image_url += src.split("/img/")[-1].split("_")[0] + "_ugoira{}"

    r = requests.get(image_url.format("1") + mode, headers={'referer': base_url})
    if r.status_code == 404:
        print "switching to png mode"
        mode = ".png"
    
    image_url += mode

    frame = 0
    r = requests.get(image_url.format(frame) + mode, headers={'referer': base_url})
    if r.status_code == 404:
        frame += 1

    done = False
    while not done:
        r = requests.get(image_url.format(frame), headers={'referer': base_url}, stream=True)
        print frame, r
        if r.status_code == 200:
            if frame < 10:
                num = "00{}".format(frame)
            elif frame < 100:
                num = "0{}".format(frame)
            else:
                num = frame
            with open("{}/{}{}".format(image_id, num, mode), 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        else:
            done = True
        frame += 1

    gifify(str(image_id))
    os.system("gifsicle {0}x.gif --optimize --colors 256 > {0}.gif".format(image_id))
    os.system("rm {}x.gif".format(image_id))
    os.system("ffmpeg -r 12 -i {0}/\%03\d{1} -c:v libvpx-vp9 -b:v 2M -pass 1 -r 24 -f webm /dev/null -y && ffmpeg -r 12 -i {0}/\%03\d{1} -c:v libvpx-vp9 -b:v 2M -pass 2 -r 24 {0}.webm -y".format(image_id, mode))