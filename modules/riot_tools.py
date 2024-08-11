import os
from dotenv import load_dotenv

import requests
import urllib.parse

load_dotenv()

API_KEY = os.getenv("RIOT_KEY")

AMERICA_URL = "https://americas.api.riotgames.com"
NA_URL = "https://na1.api.riotgames.com"
DD_URL = "https://ddragon.leagueoflegends.com"

def get_dd_version() -> str | None:
    '''
    Returns the latest Data Dragon version.
    '''
    resp = requests.get(DD_URL + "/api/versions.json")

    if resp.status_code == 200:
        return resp.json()[0]

def get_account_by_name(gameName: str, tagLine: str) -> dict | None:
    '''
    Get Riot account by Riot ID.\n
    Returns: AccountDto
    '''
    gameName = urllib.parse.quote(gameName)
    tagLine = urllib.parse.quote(tagLine)

    url = AMERICA_URL + f"/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}"
    resp = requests.get(url + f"?api_key={API_KEY}")

    if resp.status_code == 200:
        return resp.json()

def get_account_by_puuid(puuid: str) -> dict | None:
    '''
    Get Riot account by puuid.\n
    Returns: AccountDto
    '''
    puuid = urllib.parse.quote(puuid)

    url = AMERICA_URL + f"/riot/account/v1/accounts/by-puuid/{puuid}"
    resp = requests.get(url + f"?api_key={API_KEY}")

    if resp.status_code == 200:
        return resp.json()   

def get_summoner_by_name(gameName: str, tagLine: str) -> dict | None:
    '''
    Get summoner by Riot ID.\n
    Returns: merge(SummonerDTO, AccountDto)
    '''
    if not (account := get_account_by_name(gameName, tagLine)):
        return None
    
    puuid = urllib.parse.quote(account['puuid'])

    url = NA_URL + f"/lol/summoner/v4/summoners/by-puuid/{puuid}"
    resp = requests.get(url + f"?api_key={API_KEY}")

    if resp.status_code == 200:
        summoner = resp.json()
        summoner.update(account)
        return summoner
    
def get_summoner_by_puuid(puuid: str) -> dict | None:
    '''
    Get summoner by puuid.\n
    Returns: merge(SummonerDTO, AccountDto)
    '''
    if not (account := get_account_by_puuid(puuid)):
        return None
    
    puuid = urllib.parse.quote(puuid)

    url = NA_URL + f"/lol/summoner/v4/summoners/by-puuid/{puuid}"
    resp = requests.get(url + f"?api_key={API_KEY}")

    if resp.status_code == 200:
        summoner = resp.json()
        summoner.update(account)
        return summoner
    
def get_summoner_icon(iconId: int) -> str | None:
    '''
    Returns summoner icon link.
    '''
    version = get_dd_version()
    return DD_URL + f"/cdn/{version}/img/profileicon/{iconId}.png"

def get_stats_by_summoner(summonerId: str) -> list[dict] | None:
    '''
    Get summoner stats.\n
    Returns: list[LeagueEntryDTO]
    '''
    summonerId = urllib.parse.quote(summonerId)

    url = NA_URL + f"/lol/league/v4/entries/by-summoner/{summonerId}"
    resp = requests.get(url + f"?api_key={API_KEY}")

    if resp.status_code == 200:
        return resp.json()
    
def get_matchId_by_puuid(puuid: str, count: int = 20) -> list | None:
    '''
    Get match IDs.\n
    Returns: list[str]
    '''
    puuid = urllib.parse.quote(puuid)

    url = AMERICA_URL + f"/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
    resp = requests.get(url + f"&api_key={API_KEY}")

    if resp.status_code == 200:
        return resp.json()
    
def get_match_by_matchId(matchId: str) -> dict | None:
    '''
    Get match info by matchId.\n
    Returns: MatchDto
    '''
    matchId = urllib.parse.quote(matchId)

    url = AMERICA_URL + f"/lol/match/v5/matches/{matchId}"
    resp = requests.get(url + f"?api_key={API_KEY}")

    if resp.status_code == 200:
        return resp.json()
