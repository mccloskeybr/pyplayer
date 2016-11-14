import urllib
import urlparse
from BeautifulSoup import BeautifulSoup
from HTMLParser import HTMLParser
import pafy
import pygame
import random
import os
import sys
import subprocess
import thread
import time

TEMP_ADDRESS = 'C:/temp/'
color_format = {
    'WHITE' : '\33[97m',
    'GREEN' : '\33[92m',
    'RED' : '\33[91m',
    'END' : '\033[0m'
}

class Playlist():
    def __init__(self, oggpaths):
        self.oggpaths = oggpaths
        self.prevsongs = []
        self.index = 0
        self.shuffle = False

    """ plays the song at a specific index (default is next in queue) """
    def play_song(self, index=None):
        if index != None:
            self.index = index

        pygame.mixer.music.load(self.oggpaths[self.index])
        pygame.mixer.music.play(1)

        if len(self.prevsongs) == 0 or self.prevsongs[-1] != self.index:
            self.prevsongs.append(self.index)

        if self.shuffle:
            self.index = random.randint(0, len(self.oggpaths) - 1)
        else:
            self.index = (self.index + 1) % len(self.oggpaths)

    """ skips the current song """
    def skip_song(self):
        pygame.mixer.music.stop()
        self.play_song()

    """ play pervious song """
    def previous_song(self):
        #get rid of current song
        self.prevsongs.pop()
        #play previous
        self.play_song(self.prevsongs.pop())

    """ restart the current song """
    def restart_song(self):
        self.play_song(self.prevsongs.pop())

    """ get index of the current song """
    def get_current_song_index(self):
        return self.prevsongs[-1]

    """ gets index of queued song in the playlist """
    def get_index(self):
        return self.index

    """ get songs in playlist """
    def get_songs(self):
        return self.oggpaths

    """ returns song title (default is current song) """
    def get_song_title(self, index=None):
        if index == None:
            if len(self.prevsongs) > 0:
                index = self.prevsongs[-1]
            else:
                return None
        title_bits = self.oggpaths[index].split('\\')
        return title_bits[-1][:-4]

    """ get state of shuffle """
    def get_shuffle(self):
        return self.shuffle

    """ set index of current song """
    def set_index(self, index):
        self.index = index

    """ set whether player should shuffle or not """
    def set_shuffle(self, shuffle):
        self.shuffle = shuffle

    def delete_song(self, index):
        if index < 0 or index >= len(self.oggpaths):
            print " ERR: Index out of bounds."
        else:
            if raw_input(" Are you sure you want to delete %s?(y, N) " %(self.get_song_title(index))) == 'y':
                os.remove(self.oggpaths[index])

##################################################

""" return url to desired song
searches for a specified song on youtube, user picks desired from list of results
"""
def search_youtube():
    search = str(raw_input(' What song do you want to search for?: ')).replace(' ', '+')
    url = 'http://www.youtube.com/results?search_query=%s' %search

    print " Searching..."

    html = urllib.urlopen(url).read()
    bs = BeautifulSoup(html)

    urls = []
    titles = []
    for tag in bs.findAll('a', href=True):
        tag = urlparse.urljoin(url, tag['href'])
        if 'watch?v' in tag and tag not in urls:
            urls.append(tag)
            titles.append(get_title_from_url(tag))

    for i in range(len(titles)):
        print ' [%d] : %s' %(i, titles[i])

    desired = int(raw_input(" Index of desired video?(-1 to abort): "))
    if desired == -1:
        return None
    return urls[desired]


""" returns path of file """
def download_from_url(url, new_path=None):
    if url != None:
        if new_path == None:
            new_path = raw_input(" Path to save directory?: ")
        if not new_path.endswith('/'):
            new_path += '/'

        title = get_title_from_url(url)
        aacpath = TEMP_ADDRESS + title + '.m4a'
        oggpath = new_path + title + '.ogg'

        to_dl = pafy.new(url).getbestaudio(preftype="m4a")
        to_dl.download(aacpath, quiet=False)

        subprocess.call(["ffmpeg", "-i", aacpath, "-acodec", "libvorbis", "-ab",
                      "256k", oggpath], shell=False)

        os.remove(aacpath)
        print " ***File successfully downloaded to %s!***" %oggpath
        return oggpath


""" returns the title of the paramter youtube video link """
def get_title_from_url(url):
    html = urllib.urlopen(url).read()
    bs = BeautifulSoup(html, convertEntities=BeautifulSoup.HTML_ENTITIES)
    title = str(bs.find('span', {"class" : "watch-title"}))
    title = title[title.find('title=')+7:]
    title = title[:title.find('>')-1]
    title = title.decode("utf-8").encode("ascii", "ignore")
    return HTMLParser().unescape(title)


""" return list consisting of urls to songs
open desired playlist .txt file from given path and reassign currentPlaylist, print out songs in list
"""
def open_playlist(path=None):
    if path == None:
        path = raw_input(" Enter path to playlist: ")
    try:
        if path[len(path) - 1] != '/':
            path += '/'

        paths = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('.ogg'):
                    paths.append(os.path.abspath(path + file))
                    print os.path.abspath(path + file)

        if len(paths) > 0:
            print " ***Opened playlist successfully!***"
            return paths
        else:
            print " Error ocurred when opening playlist."
            return []

    except:
        print "ERR: Directory not found"
        return None

""" opens a new directory for music to be placed into """
def new_playlist(path=None):
    if path == None:
        path = raw_input(" Enter path to new playlist: ")
    if not os.path.exists(path):
        os.makedirs(path)


""" plays music continuously, switching to the next in the queue when the song
is finished
"""
def run_player(thread_id, playlist):
    while (True):
        if not pygame.mixer.music.get_busy():
            playlist.play_song()
        time.sleep(5)

""" prints the pyplayer banner """
def print_banner():
    print " ***********************************"
    print " * PYPLAYER :: PYTHON MEDIA PLAYER *"
    print " ***********************************"


if __name__ == '__main__':
    os.system('cls')

    current_playlist = None
    pygame.mixer.init()

    print_banner()
    while True:
        cmd = raw_input(" >").strip()

        if "open" in cmd:
            if "help" in cmd:
                print " open <OPTIONAL path>"
                print " Opens a playlist at the desired path and saves in order to be played."
            else:
                if len(cmd) > 4:
                    songs = open_playlist(cmd[5:])
                else:
                    songs = open_playlist()

                if songs != None:
                    current_playlist = Playlist(songs)

        elif "list" in cmd:
            if "help" in cmd:
                print " list"
                print " Lists the songs in the current playlist (must have a playlist loaded to work)."
            else:
                try:
                    if current_playlist == None:
                        raise Exception(" ERR: Playlist not open.")
                    for i in range(len(current_playlist.get_songs())):
                        if i == current_playlist.get_current_song_index():
                            print (" {GREEN}[%d] : %s{END}" %(i, current_playlist.get_song_title(i))).format(**color_format)
                        else:
                            print (" {WHITE}[%d] : %s{END}" %(i, current_playlist.get_song_title(i))).format(**color_format)
                except Exception as inst:
                    print ("{RED}%s{END}" %inst.message).format(**color_format)

        elif "current" in cmd:
            if "help" in cmd:
                print " current"
                print " Prints the index and the name of the song currently playing."
            else:
                try:
                    if current_playlist == None:
                        raise Exception(" ERR: Playlist not open.")

                    title = current_playlist.get_song_title()

                    if title is None:
                        raise Exception( " ERR: No song playling.")
                    else:
                        print (" {GREEN}[%d] : %s{END}" %(current_playlist.get_current_song_index(), title)).format(**color_format)
                except Exception as inst:
                    print ("{RED}%s{END}" %inst.message).format(**color_format)

        elif "new" in cmd:
            if "help" in cmd:
                print " new <path <?>>"
                print " Creates a new directory specified in path."
            else:
                if len(cmd) > 3:
                    new_playlist(cmd[4:])
                else:
                    new_playlist()

        elif "play" in cmd:
            if "help" in cmd:
                print " play <index>"
                print " Plays the loaded playlist at the desired index (0 if none given) (must have a playlist loaded to work)."
            else:
                try:
                    if current_playlist == None:
                        raise Exception(" ERR: Playlist not open.")
                    if len(cmd) > 4:
                        try:
                            current_playlist.set_index(int(cmd[5:]))
                        except:
                            print " ERR: Invalid index."
                    else:
                        current_playlist.set_index(0)

                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    thread.start_new_thread(run_player, ('Thread-1',
                                                         current_playlist, ))
                except Exception as inst:
                    print ("{RED}%s{END}" %inst.message).format(**color_format)

        elif "shuffle" in cmd:
            if "help" in cmd:
                print " shuffle"
                print " Toggle the shuffle feature (play random songs after each other) (must have a playlist loaded to work)."
            else:
                try:
                    if current_playlist == None:
                        raise Exception(" ERR: Playlist not open.")
                    current_playlist.set_shuffle(not current_playlist.get_shuffle())
                    print " *** Shuffle : %s ***" %current_playlist.get_shuffle()
                except Exception as inst:
                    print ("{RED}%s{END}" %inst.message).format(**color_format)

        elif "skip" in cmd:
            if "help" in cmd:
                print " skip"
                print " Skips the current song in the playlist (must have a playlist loaded to work)."
            else:
                try:
                    if current_playlist == None:
                        raise Exception(" ERR: Playlist not open.")
                    #playlist automatically increments index after playing a song
                    current_playlist.skip_song()
                except Exception as inst:
                    print ("{RED}%s{END}" %inst.message).format(**color_format)

        elif "previous" in cmd:
            if "help" in cmd:
                print " previous"
                print " Plays the previous song in the playlist (must have a playlist loaded to work)."
            else:
                try:
                    if current_playlist == None:
                        raise Exception(" ERR: Playlist not open.")
                    current_playlist.previous_song()
                except Exception as inst:
                    print ("{RED}%s{END}" %inst.message).format(**color_format)

        elif "restart" in cmd:
            if "help" in cmd:
                print " restart"
                print " Restarts the current song in the playlist (must have a playlist loaded to work)."
            else:
                try:
                    if current_playlist == None:
                        raise Exception(" ERR: Playlist not open.")
                    current_playlist.restart_song()
                except Exception as inst:
                    print ("{RED}%s{END}" %inst.message).format(**color_format)

        elif "pause" in cmd:
            if "help" in cmd:
                print " pause"
                print " Pauses the music player."
            else:
                pygame.mixer.music.pause()

        elif "unpause" in cmd:
            if "help" in cmd:
                print " unpause"
                print " Unpauses the music player."
            else:
                pygame.mixer.music.unpause()

        elif "volume" in cmd:
            if "help" in cmd:
                print " volume <new volume [0.0, 1.0]>"
                print " Sets the volume to a desired float value (must be between 0.0 and 1.0 inclusive)."
            else:
                try:
                    new_volume = float(cmd[6:])
                    if new_volume < 0 or new_volume > 1:
                        raise Exception(" ERR: Volume out of bounds [0, 1.0].")
                    pygame.mixer.music.set_volume()
                except Exception as inst:
                    print ("{RED}%s{END}" %inst.message).format(**color_format)

        elif "download" in cmd:
            if "help" in cmd:
                print " download <OPTIONAL youtube url>"
                print " Searches for (no url provided) and downloads audio from a desired youtube video and converts it from AAC to OGG."
                print " Places the audio file in a directory of the user's choice."
                print " Possible thanks to pafy (yt download) and ffmpeg (convert aac to ogg)."
            else:
                if len(cmd) > 8:
                    download_path = download_from_url(cmd[9:])
                else:
                    download_path = download_from_url(search_youtube())

        elif "clear" in cmd:
            if "help" in cmd:
                print " clear"
                print " Clears/resets the command window."
            else:
                os.system('cls')
                print_banner()

        elif "version" in cmd:
            if "help" in cmd:
                print " version"
                print " Prints the current version of PyPlayer."
            else:
                print " PyPlayer v:1.0 by Brendan McCloskey (mccloskeydev)"

        elif "exit" in cmd:
            if "help" in cmd:
                print " exit"
                print " Exits the player."
            else:
                thread.exit()
                sys.exit(0)

        else:
            if "help" not in cmd:
                print " ERR: Command not recognized."

            print " *** HELP ***"
            print " COMMANDS: type <command> help to see help with specific functions"
            print " open <path>, new <path>, play <index>, list, current"
            print " download <url>, shuffle, skip, previous, restart, pause, unpause, volume <new volume [0.0, 1.0]>"
            print " help, clear, version, exit"

