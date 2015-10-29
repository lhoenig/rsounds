#!/usr/bin/python

import os
import sys
import requests
import subprocess
import praw
from mutagen.id3 import ID3, TIT2, TPE1, APIC
from termcolor import colored


post_filter = ['http://youtube.com/watch?', 
               'https://youtube.com/watch?', 
               'https://youtu.be/', 
               'http://youtu.be',
               'https://www.youtube.com/watch?',
               'http://www.youtube.com/watch?']

# determine if a link is wanted for downloading
def post_wanted(link):
    return any(link.startswith(url) for url in post_filter)


# set title, artist and album cover of an mp3 file
def write_tags(post, fname):
    audio = ID3(fname)
    cover = requests.get(post.thumbnail).content
    if len(post.title.split(' - ', 2)) == 2:
        audio.add(TIT2(encoding=3, text=post.title.split(' - ', 2)[1]))
        audio.add(TPE1(encoding=3, text=post.title.split(' - ', 2)[0]))
        audio.add(APIC(3, u'image/jpeg', 3, u'Albumcover', cover))
    else:
        audio.add(TIT2(encoding=3, text=post.title))
        audio.add(APIC(3, u'image/jpeg', 3, u'Albumcover', cover))
    audio.save()


# make a name a filename
def filtered_name(name):
    return name.replace('\"', '')\
               .replace('\'', '')\
               .replace('/', '_')\
               .replace('$', 'S')\
               .replace('%', '_')\
               .replace('\\','_')


# spawn a youtube-dl process that downloads the video and extracts the audio
def download_track(post):
    link = post.url
    name = filtered_name(post.title)
    fname = sr_title + '/' + name + '.mp3'
    
    invoke = 'youtube-dl --no-playlist -x --audio-format mp3 --audio-quality 320K -w -o \"' + sr_title + '/' + name + '.%(ext)s\" --max-filesize 40m ' + '\"' + link + '\"'
    p = subprocess.Popen(invoke, shell=True, 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.STDOUT)
    cline = ''
    for line in iter(p.stdout.readline, ''): 
        cline = line
        print line,
    retval = p.wait()
    
    if not ('max-filesize' in cline or \
            'too short' in cline or \
            'has been terminated' in cline or \
            'copyright claim' in cline or \
            'Abort' in cline or \
            'ERROR' in cline) and retval is 0:
        write_tags(post, fname)
        return True

    if retval != 0:
        return False
    return True


# called for every post in the feed
def process_post(post, num):
    try:
        link = post.url
        name = post.title
        fname = sr_title + '/' + filtered_name(name) + '.mp3'
        global tcount
        if post_wanted(link):
            if not os.path.isfile(fname):
                print colored('#' + str(num), 'yellow', 'on_red', attrs=['bold']) + \
                      colored(' Downloading ', 'green') + \
                      colored(name, 'yellow', 'on_magenta')
                fin = download_track(post)
                print
                tcount += 1
            else:
                print colored('#' + str(num), 'yellow', 'on_red', attrs=['bold']) + \
                      colored(' Skipping ', 'green') + \
                      colored(name, 'yellow', 'on_magenta')
                tcount += 1
    except KeyError:
        return


ua = "rsounds 0.1"
r = praw.Reddit(user_agent=ua)

sr_title = sys.argv[1] if len(sys.argv) == 2 else "music"

sr = r.get_subreddit(sr_title)
posts = sr.get_new(limit=None)

# global processed post counter
tcount = 1

# iterate over every post in the feed
while True:
    p = posts.next()
    if p is not None:
        process_post(p, tcount)
    else:
        break
