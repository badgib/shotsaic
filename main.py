#!/usr/bin/python3

# import all needed libraries
import queue
import threading
import time
import os
import itertools
import sys
import random
import secrets

# these need to be installed beforehand
import requests
from flask import Flask, request, render_template,jsonify, send_from_directory

import base36
import cloudscraper
from bs4 import BeautifulSoup

import numpy as np
from PIL import Image # pillow
from skimage import img_as_float # scikit_image
from skimage.metrics import mean_squared_error

# from flask():
#
# the idea of the first parameter is to give flask an idea of what belongs to your application
# this name is used to find resources on the filesystem, can be used by extensions to improve
# debugging information and a lot more.
# 
# so it’s important what you provide there. if you are using a single module
# __name__ is always the correct value. if you however are using a package
# it’s usually recommended to hardcode the name of your package there
app = Flask(__name__)

# defining image directory
images_directory = "static/images/output/"

# setting some global lists
processed_paths = list()
matched_paths = list()
path_coords = list()

# initiate flags
exitFlag = 0
runningFlag = 0

# define IMAGE_UPLOADS directory for flask
app.config["IMAGE_UPLOADS"] = "static/images/"

uploaded_name = ""

get_image("Thread-1")

# make get_image class which will run concurrently in multiple threads
class get_image(threading.Thread):

    # __init__ is run everytime class is created. used to initiate stuff. runs once
    def __init__(self, threadID, name, q):

        # initiate threading and let it do it's magic
        threading.Thread.__init__(self)

        # and add little data to pass around
        self.threadID = threadID
        self.name = name

        # q stands for queue
        self.q = q

    # create run method. used to inform about process state and run our own method
    def run(self):

        # just prints out starting info
        print("Starting " + self.name)

        # calls our method passing along some vars. self.name is just to inform which thread done what
        process_data(self.name, self.q)

        # just prints out that it's done with all queue workload and can exit
        # or in other words process_data has ended it's job and executes this
        # next line which prints out information and ends
        print("Exiting " + self.name)

# this method is outside of get_image class and processes data as needed
# as input it expects threadName and q (queue)
def process_data(threadName, q):

    # run this loop until exitFlag is false
    while not exitFlag:

        # lock the queue so the data can be safely read. yeah threading sucks :)
        queueLock.acquire()

        # check if queue is not empty THIS IF HAS ELSE WAY DOWN BELOW!
        if not workQueue.empty():

            # save first item from queue to local variable for future use
            data = q.get()

            # ASAP release the lock so other processes can access queue
            queueLock.release()

            # just for verbose purposes. can be removed without harm
            #print("%s processing id: %s" % (threadName, str(data)))

            # create scraper because of cloudflare
            scraper = cloudscraper.create_scraper()

            # build an url with iterated suffix
            url = 'https://prnt.sc/' + str(data)

            # save response to local variable r using scraper
            r = scraper.get(url)

            # using soup parse html. to get same results in different environments
            # hard define the use of html.parser
            soup = BeautifulSoup(r.text, features="html.parser")

            # also using soup find certain img element
            image = soup.find("img", {"image-id": data})

            # if image is found
            if image:

                # get src value of found image
                imageURL = image['src']

                # TODO: change the method for defining valid URLs
                
                # if imageURL has more than 31 characters then print
                # information and id. image is probably missing
                if len(imageURL) > 68:
                    
                    print("url too long. image id: " + data)
                
                # if imageURL has less than 31 characters then print
                # intormation and id. image is probably missing
                elif len(imageURL) < 31:
                    
                    print("url too short. image id: " + data)
                
                elif not imageURL.startswith("http"):

                    print("url does not start with \"http\"!")
                    
                # if imageURL has 31, 43, 58 or 68 chars then it's OK
                # typical url is https://i.imgur.com/1X2X3X4.png
                # also: https://image.prntscr.com/image/1X2X3X4.png
                elif len(imageURL) == 31 or len(imageURL) == 43 or len(imageURL) == 58 or len(imageURL) == 68:
                        
                    # using requests get an image
                    img = requests.get(imageURL)

                    # if image is larger than 2kb then use it
                    # placeholder image for deleted ones weighs 503b
                    if len(img.content) > 2048:
                        
                        # get file extension so the data can be unloaded propertly
                        file_ext = os.path.splitext(imageURL)[-1]

                        # combine id with extension to make a proper filename
                        file_name = "temp/" + str(data) + file_ext

                        # save the image to drive
                        with open(file_name, 'wb') as f:
                            f.write(img.content)
                            print(data + file_ext + " saved; size: " + str(len(img.content)) + "b")
                    
                    # if smaller than 2kb then discard it
                    else:
                        
                        print("image too small to be of any use, discarding. size: " + str(len(img.content)) + "b, id: " + data)

                # if url length is weird, shouldn't happen, but who knows...
                else:
                    
                    print("url bad, error bad, you never read this should, ugh " + data)
                    
            # if image is not found
            else:
                
                print("image missing! something went very wrong... " + data)

        # this else is for if WAY BACK UP!
        # if queue is empty then
        else:

            # release the lock on queue
            queueLock.release()

        # just wait a moment -@kitboga
        # a random moment. in seconds
        # 1-3 to be exact
        time.sleep(1 + random.randint(0, 2))

# # from https://www.101computing.net/number-only/
# def inputInteger(message):
#     while True:
#         try:
#             userInput = int(input(message))
#         except:
#             print("Not an integer! Try again.")
#             continue
#         else:
#             return userInput

# below globals are specific for image downloader

# initiate thread name list. used to differentiate threads
# changing this lists length will change the amount of threads that will run tasks
threadList = ["Thread 1", "Thread 2", "Thread 3", "Thread 4"]

# instantiate queueLock
queueLock = threading.Lock()

# initiate workQueue
workQueue = queue.Queue()

# initiate thread list and id
exitFlag = 0

def get_images(num, fid):

    # grab global variables
    global images_directory
    global runningFlag
    
    # if no process is currently running
    if not runningFlag:

        # set runningFLag to true so no other process can run
        runningFlag = 1
        
        # process and save imageAmount
        imageAmount = int(num)

        # process and save first imageID
        imageID = str(fid)

        # initiate local thread list and id
        threads = []
        threadID = 1
        
        # create new threads
        for tName in threadList:

            # threads will run get_image method
            thread = get_image(threadID, tName, workQueue)
            
            # start the thread, duh!
            thread.start()

            # add this thread to the threads list
            threads.append(thread)

            # increment threadID
            threadID += 1

        # lock the queue
        queueLock.acquire()

        # fill the queue
        for i in range(0, imageAmount):

            # put imageID in the queue
            workQueue.put(imageID)

            # sneakily increment imageID
            # why this way? because it's alphanumeric with lowercase
            # prnt.sc uses this method so it's the cleanest, oneline implementation
            imageID = base36.dumps(base36.loads(imageID) + 1)

        # release the lock from queue
        queueLock.release()

        # wait for queue to empty
        while not workQueue.empty():

            pass

        # notify threads it's time to exit
        global exitFlag
        exitFlag = 1

        # wait for all threads to complete
        for t in threads:

            t.join()
            
        # just to notify that all is done and code finished
        print("Exiting Main Thread")

        # this loop checks for image validity for all images in temp directory
        for filename in os.listdir("temp/"):

            try:
                img = Image.open("temp/" + filename) # open the image file
                img.verify()                         # verify that it is, in fact, an image
                
                # move valid image to output directory for later use
                os.rename("temp/" + filename, images_directory + filename)
            
            # if img.verify() fails it means image is not valid so it can be removed and so it is
            except (IOError, SyntaxError) as e:
                print(filename + " broken - removing")
                os.remove("temp/" + filename)
               
        # generate response to inform user that process is done and about amount of images read for use
        response = "total images: " + str(len(os.listdir(images_directory)))
        
        # reset flags
        runningFlag = 0
        exitFlag = 0
        
        # return response
        return response
    
    #if runningFlag is true then return "still running"
    else:
        
        return "still running"
    
    
# some code below based on: https://github.com/dvdtho/python-photo-mosaic    
    
# disabled for now because it potentially breaks clickable overlay
def shuffle_first_items(lst, i):
    
#     if not i:
#
#         return lst
#
#     first_few = lst[:i]
#     remaining = lst[i:]
#     random.shuffle(first_few) 
#     return first_few + remaining
    return lst
    
# define bound method for simplicity later on
def bound(low, high, value):
    
    return max(low, min(high, value))

# define class that is really not needed for web app but it doesn't break anything so meh
class ProgressCounter:
    
    def __init__(self, total):
        
        self.total = total
        self.counter = 0

    def update(self):
        
        self.counter += 1
        sys.stdout.write("Progress: %s%% %s" % (round(100 * self.counter / self.total, 2), " " + str(self.counter) + "/" + str(self.total) + "     \r"))
        sys.stdout.flush()

# define method that gets mean square error between two images
def img_mse(im1, im2):

    try:
        
        return mean_squared_error(img_as_float(im1), img_as_float(im2))
    
    except ValueError:
        
        print(f'RMS issue, Img1: {im1.size[0]} {im1.size[1]}, Img2: {im2.size[0]} {im2.size[1]}')
        raise KeyboardInterrupt

# define method for resizing and cropping images to target aspect ratio
def resize_box_aspect_crop_to_extent(img, target_aspect, centerpoint=None):
    
    width = img.size[0]
    height = img.size[1]

    if not centerpoint:
        
        centerpoint = (int(width / 2), int(height / 2))

    requested_target_x = centerpoint[0]
    requested_target_y = centerpoint[1]
    aspect = width / float(height)

    if aspect > target_aspect:
        
        # then crop the left and right edges:
        new_width = int(target_aspect * height)
        new_width_half = int(new_width/2)
        target_x = bound(new_width_half, width-new_width_half, requested_target_x)
        left = target_x - new_width_half
        right = target_x + new_width_half
        resize = (left, 0, right, height)

    else:
        
        # ...crop the top and bottom: 
        new_height = int(width / target_aspect)
        new_height_half = int(new_height/2)
        target_y = bound(new_height_half, height-new_height_half, requested_target_y)
        top = target_y - new_height_half
        bottom = target_y + new_height_half
        resize = (0, top, width, bottom)

    return resize

# define method to crop an image to target aspect. centerpoint can be provided to focus crop on one
# side. i.e. centerpoing = (width, height)
def aspect_crop_to_extent(img, target_aspect, centerpoint=None):

    resize = resize_box_aspect_crop_to_extent(img, target_aspect, centerpoint)
    return img.crop(resize)

# define config class to contain all needed variables
class Config:
    
    def __init__(self, tile_ratio=1920/800, tile_width=50, enlargement=8, color_mode='RGB'):
        
        self.tile_ratio = tile_ratio   # 2.4
        self.tile_width = tile_width   # height/width of mosaic tiles in pixels
        self.enlargement = enlargement # mosaic image will be this many times wider and taller than original
        self.color_mode = color_mode 

    @property
    def tile_height(self):
        
        return int(self.tile_width / self.tile_ratio)

    @property
    def tile_size(self):
        
        return self.tile_width, self.tile_height # PIL expects (width, height)

# define container to import, process, hold and compare all of the tiles
class TileBox:

    def __init__(self, tile_paths, config):
        
        self.config = config
        self.tiles = list()
        self.prepare_tiles_from_paths(tile_paths)
        
    def __process_tile(self, tile_path):
        
        with Image.open(tile_path) as i:
            
            img = i.copy()  
        img = aspect_crop_to_extent(img, self.config.tile_ratio)
        large_tile_img = img.resize(self.config.tile_size, Image.ANTIALIAS).convert(self.config.color_mode)
        processed_paths.append(tile_path)
        self.tiles.append(large_tile_img)
        return True

    def prepare_tiles_from_paths(self, tile_paths):
        
        print('Reading tiles from provided list...')
        progress = ProgressCounter(len(tile_paths))
        
        for tile_path in tile_paths:
            
            progress.update()
            self.__process_tile(tile_path)

        print('\nProcessed tiles.')
        return True

    def best_tile_block_match(self, tile_block_original):
        
        match_results = [img_mse(t, tile_block_original) for t in self.tiles] 
        best_fit_tile_index = np.argmin(match_results)
        return best_fit_tile_index

    def best_tile_from_block(self, tile_block_original, reuse=False):
        
        if not self.tiles:
            
            print('Ran out of images.')
            raise KeyboardInterrupt
        
        i = self.best_tile_block_match(tile_block_original)
        matched_paths.append(processed_paths[i])
        match = self.tiles[i].copy()
        
        if not reuse:
            
            del self.tiles[i]
            del processed_paths[i]
            
        return match
# define class for processing original image with scaling and cropping as set
class SourceImage:
    
    def __init__(self, image_path, config):
        
        print('Processing main image...')
        self.image_path = image_path
        self.config = config

        with Image.open(self.image_path) as i:
            
            img = i.copy()
            
        w = img.size[0] * self.config.enlargement
        h = img.size[1] * self.config.enlargement
        large_img = img.resize((w, h), Image.ANTIALIAS)
        w_diff = (w % self.config.tile_width)/2
        h_diff = (h % self.config.tile_height)/2
        
        # if necesary, crop the image slightly so a whole number
        # of tiles can be used horizontally and vertically
        if w_diff or h_diff:
            
            large_img = large_img.crop((w_diff, h_diff, w - w_diff, h - h_diff))

        self.image =  large_img.convert(self.config.color_mode)
        print('Main image processed.')

# define class holding mosaic
class MosaicImage:

    def __init__(self, original_img, target, config):
        
        self.config = config
        self.target = target
        self.image = original_img
        
        # switch to below one to use blank canvas instead of original image
        # self.image = Image.new(original_img.mode, original_img.size)
        self.x_tile_count = int(original_img.size[0] / self.config.tile_width)
        self.y_tile_count = int(original_img.size[1] / self.config.tile_height)
        self.total_tiles  = self.x_tile_count * self.y_tile_count
        print(f'Mosaic will be {self.x_tile_count:,} tiles wide and {self.y_tile_count:,} tiles high ({self.total_tiles:,} total).')

    # adds tile to the mosaic at provided coords
    def add_tile(self, tile, coords):
        
        try:
            self.image.paste(tile, coords)
            
        except TypeError as e:
            
            print('Maybe the tiles are not the right size. ' + str(e))

    def save(self):
        
        self.image.save(self.target)

# tiling starts from the middle so it looks better
def coords_from_middle(x_count, y_count, y_bias=1, shuffle_first=0, ):

    x_mid = int(x_count/2)
    y_mid = int(y_count/2)
    coords = list(itertools.product(range(x_count), range(y_count)))
    coords.sort(key=lambda c: abs(c[0]-x_mid)*y_bias + abs(c[1]-y_mid))
    coords = shuffle_first_items(coords, shuffle_first)
    return coords

# define main method to create mosaic
# this reads, processes, and keeps in memory a copy of the source image, and all the tiles while processing
# arguments:
# source_path   - filepath to the source image for the mosiac
# target        - filepath to save the mosiac
# tile_ratio    - height/width of mosaic tiles in pixels
# tile_width    - width of mosaic tiles in pixels
# enlargement   - mosaic image will be this many times wider and taller than the original
# reuse         - should tiles be reused?
# color_mode    - L for greyscale or RGB for color
# tile_paths    - list of filepaths to your tiles
# shuffle_first - currently disabled, returns input ;)
def create_mosaic(source_path, target, tile_ratio=1920/800, tile_width=75, enlargement=8, reuse=True, color_mode='RGB', tile_paths=None, shuffle_first=30):

    config = Config(
        tile_ratio = tile_ratio,        # height/width of mosaic tiles in pixels
        tile_width = tile_width,        # height/width of mosaic tiles in pixels
        enlargement = enlargement,      # the mosaic image will be this many times wider and taller than the original
        color_mode = color_mode,        # L for greyscale or RGB for color
    )
    
    # pull in and process original image
    print('Setting Up Target image')
    source_image = SourceImage(source_path, config)

    # setup mosaic
    mosaic = MosaicImage(source_image.image, target, config)

    # assest tiles, and save if needed, returns directories where the small and large pictures are stored
    print('Assessing Tiles')
    tile_box = TileBox(tile_paths, config)

    try:
        
        progress = ProgressCounter(mosaic.total_tiles)
        
        for x, y in coords_from_middle(mosaic.x_tile_count, mosaic.y_tile_count, y_bias=config.tile_ratio, shuffle_first=shuffle_first):
            
            progress.update()
            
            # make a box for this sector
            box_crop = (x * config.tile_width, y * config.tile_height, (x + 1) * config.tile_width, (y + 1) * config.tile_height)

            # get original image data for this sector
            comparison_block = source_image.image.crop(box_crop)

            # get best image name that matches the original sector image
            tile_match = tile_box.best_tile_from_block(comparison_block, reuse=reuse)
            path_coords.append([x, y])
            
            # add best match to mosaic
            mosaic.add_tile(tile_match, box_crop)

            # saving every sector
            mosaic.save() 

    except KeyboardInterrupt:
        
        print('\nStopping, saving partial image...')

    finally:
        
        mosaic.save()

# define method to process input from website and run code to make mosaic happen
def make_mosaic(tileS, enlar, mode):
    
    global runningFlag
    
    # if runningFlag is false and user uploaded an image to the server
    if not runningFlag and uploaded_name:
        
        # set runningFlag to true
        runningFlag = 1
        
        # clear all lists to begin propertly
        matched_paths.clear()
        processed_paths.clear()
        path_coords.clear()
        
        # also get tile width in int form
        tile = int(tileS)
        
        # get global images_directory
        global images_directory

        # generate unique name for mosaic
        unique_out_name = secrets.token_urlsafe(6)
        
        # generate temporary list of paths
        paths_temp = [os.path.join(images_directory, name) for name in os.listdir(images_directory)]
        
        # yeah... i know... but it works fine, when before it was not, so...
        colorM = 0
        
        if mode == "RGB":
            
            colorM ='RGB'
            
        elif mode == "L":
            
            colorM ='L'

        else:
            
            print("error! wrong color mode selected! using RGB")
            colorM ='RGB'    
        
        # and now the fun part! all this is going to finally start processing mosaic
        create_mosaic(
            source_path = "static/images/" + uploaded_name, 
            target = unique_out_name + ".png",
            tile_paths = paths_temp,
            tile_ratio = 100/100,
            tile_width = tile,
            enlargement = int(enlar),
            reuse = False,
            color_mode = colorM,
        )

        # for some reason it did not want to save directly there so now it's getting moved
        os.rename(unique_out_name + ".png", "static/images/" + unique_out_name + ".png")

        # prepare heading lines of HTML file 
        html_data = "<!DOCTYPE html><html><body><div class=\"image\"><img src=\"images/" + unique_out_name + ".png\" usemap=\"#" + unique_out_name + "\">\n<map name=\"" + unique_out_name + "\">\n"
        html_data += "<style type=\"text/css\">@keyframes zoom {0% {transform: scale(0.1,0.1);}50% {transform: scale(1,1);}100% {transform: scale(0.1,0.1);}} .image img {animation: zoom 15s alternate; animation-iteration-count:infinite;}</style>\n"
        
        # get all matched paths and assign images to them
        for i in range(0, len(matched_paths)):
            
            # maybe there's better way, but this works
            tileX = int(str(path_coords[i]).replace("[", "").split(",")[0])
            tileY = int(str(path_coords[i]).replace("]", "").split(",")[1])
            
            # append all collected information to the HTML data
            html_data += "<area shape=\"rect\" coords=\"" + str(tileX * tile) + ", " + str(tileY * tile) + ", " + str((tileX * tile) + tile) + ", " + str((tileY * tile) + tile) + "\" href=\"" + str(os.path.relpath(matched_paths[i], "static/")) + "\">\n"
        
        # append finishing line so the code is nice
        html_data += "</div></map></body></html>"
        
        # make file with same unique name as mosaic name for ease of identification
        f = open("static/" + unique_out_name + ".html", "w+")
        
        # write all that juicy HTML code to that file and save it
        f.write(html_data)
        f.close()
        
        # open history file to append new mosaic to it
        last = open("static/history.html", "a+")
        last.write("<div><a href=\"" + unique_out_name + ".html\">" + unique_out_name + ".html</a></div>\n")
        last.close()
        
        # set runningFlag to false
        runningFlag = 0
        
        # return a link to the user if s/he still has the tab open
        return "<a href=\"static/" + unique_out_name + ".html\">click here</a>"
    
    # if running or no image provided
    else:

        # return information that something's wrong
        return "still running or missing image"

# define method to handle root requests
@app.route('/')
def home():
    
    # it just returns home template
    return render_template('home.html')

# define method to handle getting images from prnt.sc
@app.route('/get_images', methods=['GET','POST'])
def form_get_images():

    # from forms get input and send it to proper method
    num = request.form['num_of_images']
    fid = request.form['first_img_id']
    getsome = get_images(num,fid)
    
    # prepare result to be displayed eventually
    result = {
        
        "output": getsome
    }
    result = {str(key): value for key, value in result.items()}
    
    # return JSONified result
    return jsonify(result=result)

# define method to handle making mosaic from downloaded images
@app.route('/make_mosaic', methods=['GET','POST'])
def form_make_mosaic():
    
    # from forms get input and send it to proper method
    width = request.form['tile_width']
    enlar = request.form['enlargement']
    imode = request.form['img_mode']
    makesome = make_mosaic(width, enlar, imode)
    
    # prepare result to be displayed eventually
    result = {
        
        "output": makesome
    }
    result = {str(key): value for key, value in result.items()}
    
    # return JSONified result
    return jsonify(result=result)    

# define method to handle image uploading
@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
    
    # define global uploaded_name so it can also be used in mosaic
    global uploaded_name
    
    # check if it was POST or GET, ignore GET
    if request.method == 'POST':
        
        # get the file
        f = request.files['file']
        
        # get the filename
        uploaded_name = f.filename
        
        # save the file
        f.save(os.path.join(app.config["IMAGE_UPLOADS"], uploaded_name))
        
        # return some information to the user
        return 'file uploaded successfully'    

# define method to add no_cache to the requests
@app.after_request
def add_header(response):
    
    response.cache_control.no_cache = True
    return response

# define method to return favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# initiate the server
if __name__ == '__main__':
    
    app.run(host='0.0.0.0')