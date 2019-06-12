## Soundcloud downloader

import requests
import os, sys

version = "0.3.4"

class Track(object):
    def __init__(self,json):
        self.json = json
        self.ID = json["id"]
        self.duration = json["duration"]/1000
        self.title = json["title"]
        self.genre = json["genre"]
        self.artwork_url = json["artwork_url"]
        self.big_artwork_url = json["artwork_url"].replace("-large.jpg", "-t500x500.jpg")
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
        self.CLIENT_ID = "yboSNKExXO4W4cTLIwqfJbUTCSyRIT3a"
        self.BASEURL = "https://www.soundcloud.com"
        self.APIURL = "https://api-v2.soundcloud.com"
        self.APIv1URL = "https://api.soundcloud.com"
        self.s = requests.session()
        self.s.headers["User-Agent"] = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0"
        self.s.get(self.BASEURL)

    def get_track(self,ID):
        TRACK_URL = "{baseurl}/tracks/{ID}?client_id={client}"
        print "Getting track with ID {ID}...".format(ID=ID)
        r = self.s.get(TRACK_URL.format(baseurl=self.APIv1URL,ID=ID,client=self.CLIENT_ID))
        r.raise_for_status()
        return Track(r.json())

    def __download_artwork(self,directory,track):
        print "Downloading album artwork..."
        r = self.s.get(track.big_artwork_url.format(client=self.CLIENT_ID),stream=True)
        if r.status_code != 200:
            r = self.s.get(track.artwork_url.format(client=self.CLIENT_ID),stream=True)

        if r.status_code == 200:
            with open(os.path.join(directory,"folder.jpg"),"wb") as output:
                for block in r.iter_content(1024):
                    output.write(block)
        else:
            sys.stderr.write("Could not download artwork (status code "+str(r.status_code)+")")
            sys.stderr.flush()

    def __download_track(self,directory,track,name_format):
        name_format = name_format.rstrip(".mp3") + ".mp3"
        if track.downloadable:
            url = track.download_url.format(client=self.CLIENT_ID)
        else:
            url = track.stream_url.format(client=self.CLIENT_ID)
        r = self.s.get(url, stream=True)
        try:
            r.raise_for_status()
        except:
            print u"Error: Unable to download track '{track}'.".format(track=track.title)  

        with open(os.path.join(directory,unicode(name_format).format(track=track.title)),"wb") as output:
            for block in r.iter_content(1024):
                output.write(block)

    def __print_info(self,json_data):
        if json_data.haskey("tracks"):
            length = len(json_data["tracks"])
        else:
            length = 1
        print u"""  Title: {title}
  Genre: {genre}
  Created At: {created}
  Created By: {author}
  No. of Tracks: {tracks}""".format(title=json_data["title"],genre=json_data["genre"],created=json_data["created_at"],author=json_data["user"]["full_name"],tracks=length)

    def __get_id_from_url(self,url,to_find):
        print "Connecting to {url}...".format(url=url)
        r = self.s.get(url)
        r.raise_for_status()
        print "Connected!"

        if to_find[-1] != ":":
            to_find += ":"

        print "Extracting ID..."

        offset = len(to_find)
        # Extract ID from iOS URI
        if '<meta property="al:ios:url"' not in r.content:
            raise ValueError("Can't find iOS URL to derive playlist from.")
        
        index = r.content.index('<meta property="al:ios:url"')
        closing_index = r.content[index:].index(">")
        uri_tag = r.content[index:index+closing_index+1]

        index = uri_tag.index(to_find)
        closing_index = uri_tag[index+offset:].index("\"")
        ID = uri_tag[index+offset:index+offset+closing_index]
        print "Found ID: {ID}".format(ID=ID)
        return ID

    def __get_json_object(self,ID,url_format):
        """Requires {baseurl}, {ID} and {client} keys"""
        print "Getting information..."
        r = self.s.get(url_format.format(baseurl=self.APIURL,ID=ID,client=self.CLIENT_ID))
        r.raise_for_status()
        json_object = r.json()
        return json_object

    def __make_dir_if_not_exists(self,directory):
        if not os.path.isdir(directory):
            print "\nMaking directory '{dire}'".format(dire=directory)
            os.mkdir(directory)

    def download_playlist(self,url,directory=None,artwork=False,download=True):
        PLAYLIST_URL = "{baseurl}/playlists/{ID}?client_id={client}"

        if not isinstance(directory,str):
            download = False
            
        ID = self.__get_id_from_url(url,"playlists")
        playlist_json = self.__get_json_object(ID,PLAYLIST_URL)
        
        self.__print_info(playlist_json)
        
        if download:
            self.__make_dir_if_not_exists(directory)
                
            print "\nFetching tracks..."
            tracks = []
            for track in playlist_json["tracks"]:
                #print track
                tracks.append(self.get_track(track["id"]))
            print "Fetched {tracks} tracks.".format(tracks=len(tracks))
            for i in range(len(tracks)):
                #print "Fetching track {n}".format(n=i+1)
                track = tracks[i]
                self.__download_track(directory,track,"{no} - {track}".format(no=i+1,track="{track}"))
                print "Downloaded track {n}".format(n=i+1)
                
        if artwork:
            self.__download_artwork(directory,tracks[0])

    def download_track(self,url,directory=None,artwork=False,download=True):
        TRACK_URL = "{baseurl}/tracks/{ID}?client_id={client}"

        if not isinstance(directory,str):
            download = False
            
        ID = self.__get_id_from_url(url,"sounds")
        track_json = self.__get_json_object(ID,TRACK_URL)
        
        if download:
            self.__make_dir_if_not_exists(directory)
            
            print "\nFetching track..."
            track = self.get_track(track_json["id"])
            print "Fetched track."

            self.__download_track(directory,track,"{track}")
            print u"Downloaded track '{track}'.".format(track=track.title)
            
        if artwork:
            self.__download_artwork(directory,track)
