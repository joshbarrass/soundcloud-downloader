## Soundcloud downloader

import requests
import os, sys

version = "0.1.5"

class Track(object):
    def __init__(self,json):
        self.json = json
        self.ID = json["id"]
        self.duration = json["duration"]/1000
        self.title = json["title"]
        self.genre = json["genre"]
        self.artwork_url = json["artwork_url"]
        self.downloadable = json["downloadable"]
        self.stream_url = json["stream_url"]
        if "?" in self.stream_url:
            self.stream_url += "&client_id={client}"
        else:
            self.stream_url += "?client_id={client}"
        self.download_url = json["download_url"]
        if "?" in self.download_url:
            self.download_url += "&client_id={client}"
        else:
            self.download_url += "?client_id={client}"
        self.username = json["user"]["username"]

    def __repr__(self):
        return "{name}.Track({username} - {title})".format(name=__name__,username=self.username,title=self.title)
        

class Soundcloud(object):
    def __init__(self):
        # Client ID found by <script crossorigin src="https://a-v2.sndcdn.com/assets/app-8fdd2ad-f455fe7-3.js"></script>
        # Just making a note of that in case it changes
        self.CLIENT_ID = "QyPi1UIiAXHektIfaZyKDQSp25ZaerWL"
        self.BASEURL = "https://www.soundcloud.com"
        self.APIURL = "https://api-v2.soundcloud.com"
        self.APIv1URL = "https://api.soundcloud.com"
        self.s = requests.session()
        self.s.headers["User-Agent"] = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0"
        self.s.get(self.BASEURL)

    def normalise_dir(self,directory):
        directory = directory.rstrip("/")
        directory = directory.rstrip("\\")
        directory = directory.replace("~",os.environ["HOME"])

    def get_track(self,ID):
        TRACK_URL = "{baseurl}/tracks/{ID}?client_id={client}"
        print "Getting track with ID {ID}...".format(ID=ID)
        r = self.s.get(TRACK_URL.format(baseurl=self.APIv1URL,ID=ID,client=self.CLIENT_ID))
        r.raise_for_status()
        return Track(r.json())

    def download_artwork(self,directory,track):
        print "Downloading album artwork..."
        r = self.s.get(track.artwork_url.format(client=self.CLIENT_ID),stream=True)
        with open(directory+"/folder.jpg","wb") as output:
            for block in r.iter_content(1024):
                output.write(block)

    def get_playlist(self,url,directory=None,artwork=False):
        PLAYLIST_URL = "{baseurl}/playlists/{playlist}?client_id={client}"

        if not isinstance(directory,str):
            download = False
        else:
            download = True
            
        
        print "Connecting to {url}...".format(url=url)
        r = self.s.get(url)
        r.raise_for_status()
        print "Connected! Extracting playlist ID..."
        # Extract playlist ID from iOS URI
        if '<meta property="al:ios:url"' not in r.content:
            raise ValueError("Can't find iOS URL to derive playlist from.")
        
        index = r.content.index('<meta property="al:ios:url"')
        closing_index = r.content[index:].index(">")
        uri_tag = r.content[index:index+closing_index+1]

        index = uri_tag.index("playlists:")
        closing_index = uri_tag[index+10:].index("\"")
        playlist_id = uri_tag[index+10:index+10+closing_index]
        print "Found playlist ID: {ID}".format(ID=playlist_id)

        print "Getting playlist information..."
        r = self.s.get(PLAYLIST_URL.format(baseurl=self.APIURL,playlist=playlist_id,client=self.CLIENT_ID))
        r.raise_for_status()
        playlist_json = r.json()
        print "\nGot playlist information!"
        print u"""  Title: {title}
  Genre: {genre}
  Created At: {created}
  Created By: {author}
  No. of Tracks: {tracks}""".format(title=playlist_json["title"],genre=playlist_json["genre"],created=playlist_json["created_at"],author=playlist_json["user"]["full_name"],tracks=len(playlist_json["tracks"]))
        if download:
            if not os.path.isdir(directory):
                print "\nMaking directory '{dire}'".format(dire=directory)
                try:
                    os.mkdir(directory)
                except:
                    print "Failed to make directory!"
                    return
            print "\nFetching tracks..."
            tracks = []
            for track in playlist_json["tracks"]:
                #print track
                tracks.append(self.get_track(track["id"]))
            print "Fetched {tracks} tracks.".format(tracks=len(tracks))
            for i in range(len(tracks)):
                #print "Fetching track {n}".format(n=i+1)
                track = tracks[i]
                if track.downloadable:
                    url = track.download_url.format(client=self.CLIENT_ID)
                else:
                    url = track.stream_url.format(client=self.CLIENT_ID)
                r = self.s.get(url, stream=True)
                try:
                    r.raise_for_status()
                except:
                    print "Error: Unable to download track {n}.".format(n=i+1)  
                    continue

                with open(directory+"/{no} - {track}.mp3".format(no=i+1,track=track.title),"wb") as output:
                    for block in r.iter_content(1024):
                        output.write(block)
                print "Downloaded track {n}".format(n=i+1)
            if artwork:
                self.download_artwork(directory,tracks[0])
        

        
