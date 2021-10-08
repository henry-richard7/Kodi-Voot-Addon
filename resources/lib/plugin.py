from __future__ import unicode_literals

# noinspection PyUnresolvedReferences
from codequick import Route, Resolver, Listitem, run
from codequick.utils import urljoin_partial, bold
import requests
import xbmcgui
import re
import urllib
import inputstreamhelper

apiUrl = 'https://psapi.voot.com/media/voot/v1/'
headers = {

    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36",
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br",
    "content-type": "application/json; charset=utf-8",
    "referer": "https://www.voot.com/",
    "usertype": "svod",
    "Content-Version": "V4",
    "origin": "https://www.voot.com"
}

languages = ['Hindi', 'Marathi', 'Tamil', 'English', 'Telugu',
             'Kannada', 'Bengali', 'Gujarati', 'Tulu']


def direct_link(movie_id):
    response = requests.get(
        f"https://wapi.voot.com/ws/ott/getMediaInfo.json?platform=Web&pId=2&mediaId={movie_id}").json()
    return response["assets"]["Files"][3]["URL"]


@Route.register
def root(plugin, content_type="segment"):
    Movies_Languages_item = {
        "label": "Voot Movies",
        "callback": voot_movies_languages
    }

    Shows_Languages_item = {
        "label": "Voot Shows",
        "callback": voot_shows_languages
    }

    yield Listitem.from_dict(**Movies_Languages_item)
    yield Listitem.from_dict(**Shows_Languages_item)


@Route.register
def voot_movies_languages(plugin):
    for language in languages:
        item = Listitem()
        item.label = language
        item.info["plot"] = f"Watch Voot {language} Movies for free!"
        item.set_callback(list_voot_movies, lang=language, page_no="1")
        yield item


@Route.register
def voot_shows_languages(plugin):
    for language in languages:
        item = Listitem()
        item.label = language
        item.info["plot"] = f"Watch Voot {language} Shows for free!"
        item.set_callback(list_voot_shows, lang=language, page_no="1")
        yield item


@Route.register
def list_voot_movies(plugin, lang, page_no):
    url = '%svoot-web/content/generic/movies-by-language?language=include:%s&sort=mostpopular:desc&&page=%s&responseType=common' % (
        apiUrl, lang, page_no)
    movies = requests.get(url, headers=headers).json()

    next_page = int(movies["page"]) + 1
    for movie in movies["result"]:
        item = Listitem()
        item.label = movie["fullTitle"]
        item.art["thumb"] = f'http://v3img.voot.com/{movie["imageUri"]}'
        item.art["fanart"] = f'http://v3img.voot.com/{movie["imageUri"]}'
        item.info["plot"] = movie["fullSynopsis"]
        item.set_callback(play_video, video_id=movie["id"])

        yield item
    yield Listitem.next_page(page_no=next_page, lang=lang, callback=list_voot_movies)


@Route.register
def list_voot_shows(plugin, lang, page_no):
    url = f"https://psapi.voot.com/jio/voot/v1/voot-web/content/generic/filtered-shows?sort=mostpopular:desc&language=include:{lang}&page={page_no}&responseType=common"
    jd = requests.get(url, headers=headers).json()
    shows = jd['result']
    next_page = int(jd["page"]) + 1
    for show in shows:
        item = Listitem()
        item.label = show["fullTitle"]
        item.art["thumb"] = f'http://v3img.voot.com/{show["imageUri"]}'
        item.art["fanart"] = f'http://v3img.voot.com/{show["imageUri"]}'
        item.info["plot"] = show["fullSynopsis"]
        item.set_callback(list_seasons, show_id=show["id"], Page_No="1")

        yield item
    yield Listitem.next_page(page_no=next_page, lang=lang, callback=list_voot_shows)


@Route.register
def list_seasons(plugin, show_id, Page_No):
    url = '%svoot-web/content/generic/season-by-show?sort=season:desc&id=%s&page=%s&responseType=common' % (
        apiUrl, show_id, Page_No)

    jd = requests.get(url, headers=headers).json()
    next_page = int(jd["page"]) + 1
    seasons = jd["result"]

    for season in seasons:
        item = Listitem()
        item.label = season["fullTitle"]
        item.art["thumb"] = f'http://v3img.voot.com/{season["imageUri"]}'
        item.art["fanart"] = f'http://v3img.voot.com/{season["imageUri"]}'
        item.info["plot"] = season["fullSynopsis"]
        item.set_callback(list_episodes, season_id=season["id"], Page_No="1")
        yield item
    yield Listitem.next_page(Page_No=next_page, show_id=show_id, callback=list_seasons)


@Route.register
def list_episodes(plugin, season_id, Page_No):
    url = '%svoot-web/content/generic/series-wise-episode?sort=episode:desc&id=%s&&page=%s&responseType=common' % (
        apiUrl, season_id, Page_No)

    jd = requests.get(url, headers=headers).json()
    next_page = int(jd["page"]) + 1

    episodes = jd["result"]
    for episode in episodes:
        item = Listitem()
        item.label = episode["fullTitle"]
        item.art["thumb"] = f'http://v3img.voot.com/{episode["imageUri"]}'
        item.art["fanart"] = f'http://v3img.voot.com/{episode["imageUri"]}'
        item.info["plot"] = episode["fullSynopsis"]
        item.set_callback(play_video, video_id=episode["id"])
        yield item
    yield Listitem.next_page(Page_No=next_page, season_id=season_id, callback=list_episodes)


@Resolver.register
def play_video(plugin, video_id):
    return Listitem().from_dict(**{
        "label": "Playing",
        "callback": direct_link(video_id),
        "properties": {
            "inputstream.adaptive.manifest_type": "hls",
            "inputstream": "inputstream.adaptive"

        }
    })
