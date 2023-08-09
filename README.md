# shotsaic

## OLD STUFF

this one was a fun project!

i found out that prnt.scr stores screenshots without hashing the filenames. they instead opted for iterating them... which is a huge mistake (for them)

and in the meantime i had an idea of making a mosaic from different images... and that's how this thing was made

this script does a couple things. it downloads images from prnt.scr and makes sure the files are, indeed, images, not just placeholders and not 'this image has been deleted'

admittedly it does that in a crude way... but hey! it works (well it worked a couple years ago. not sure if it still will)
other part of this script processes sent image and (using user-defined settings) starts creating the mosaic, replacing pixels with downloaded images

after it creates the mosaic it also creates an overlay in html, making a grid of clickable 'pixels' so the user can click on a specific 'pixel' and see the image used

it also spins a small server in flask to host a very crude website to take images and settings and also display the results and history

## it was a very fun project!

## some results:
https://imgur.com/a/3zdqP1D

