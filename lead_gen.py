#!/usr/bin/env python
# -*- coding: utf-8 -*-

import http
import argparse
import logging
import csv
import json
import re
import csv
import time
from polyglot.detect import Detector
from polyglot.detect import base
from pycld2 import error as pclderror
from user_agent import get_random_user_agent

try:
    from instagram_private_api import (
        Client, __version__ as client_version, errors)
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from instagram_private_api import (
        Client, __version__ as client_version)

# --funcs and classes for execution
def max_circle(func_to_get, where_to_take, what_to_get, number):
    result_list = []
    results = func_to_get(where_to_take) # ex. api.user_followers(user_id)
    result_list.extend(results.get(what_to_get, [])) # ex. followers.extend(results.get('users', []))

    next_max_id = results.get('next_max_id')
    while next_max_id:
        results = func_to_get(where_to_take, max_id=next_max_id)
        result_list.extend(results.get(what_to_get, []))
        if len(result_list) >= number:       # get only first 600 or so
            break
        next_max_id = results.get('next_max_id')

    return result_list
# user_id = pk
def getFeed(user_id = '2958144170', limit = 60):
    result_posts = []
    results = api.user_feed(user_id)
    result_posts.extend(results.get('items', []))

    next_max_id = results.get('next_max_id')
    while next_max_id:
        results = api.user_feed(user_id, max_id=next_max_id)
        result_posts.extend(results.get('items', []))
        if len(result_posts) >= limit:       # get only first 600 or so
            break
        next_max_id = results.get('next_max_id')

    result_posts.sort(key=lambda x: x['taken_at'])
    return result_posts

'''def getFeedGen(user_id = '2958144170', limit = 60):
    results = api.user_feed(user_id)
    next_max_id = results.get('next_max_id')

    while next_max_id:
        results = api.user_feed(user_id, max_id=next_max_id)
        yield results.get('items', [])
        if len(result_posts) >= limit:  # get only first 600 or so
            break
        next_max_id = results.get('next_max_id')'''

# return all list
def getHashtag(generate_rank=Client.generate_uuid(), hashtag = 'cats', limit = 60):
    rank_token = generate_rank
    has_more = True
    tag_results = []
    while has_more and rank_token and len(tag_results) < limit:
        results = api.tag_search(
            hashtag, rank_token, exclude_list=[t['id'] for t in tag_results])
        tag_results.extend(results.get('results', []))
        has_more = results.get('has_more')
        rank_token = results.get('rank_token')
    return tag_results

# yield a bit (12 or default instagram number)
def getHashtagGen(generate_rank=Client.generate_uuid(), hashtag = 'cats', limit = 60):
    rank_token = generate_rank
    has_more = True
    id_tag_results = []
    while has_more and rank_token and len(id_tag_results) < limit:
        results = api.tag_search(hashtag, rank_token, exclude_list=id_tag_results)
        id_tag_results.extend(i['id'] for i in results.get('results', []))
        has_more = results.get('has_more')
        rank_token = results.get('rank_token')
        yield results.get('results', [])


def getCode(s):
    match = re.search('\d[\s+\-\(]*\d[\s+\-\(]*\d', s)
    if match:
        return ''.join(c for c in match.group() if c.isdigit())
    else:
        return ''

def plusList(l):
    return '\n'.join(l)

def writeToCsv(path, row, t): #column names /than rows with data
    with open(path, t, encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(row)

def readCsv(path):
    with open(path, encoding='utf-8') as f:
        reader = csv.reader(f)
        ids = [id for id in reader]
        ids = ids[1:]
        return [int(id[0]) for id in ids if int(id[0])]

def writeToCsvRows(path, rows, t): #column names /than rows with data
    with open(path, t, encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)

def getHashtagFeed(gen_token = Client.generate_uuid(), hashtag = 'cats', limit = 60):
    results = api.feed_tag(hashtag, gen_token)
    tgs = []
    tgs.extend(results.get('ranked_items', []))
    tgs.extend(results.get('items', []))
    more_available = results['more_available']
    while more_available:
        results = api.feed_tag(hashtag, gen_token)
        tgs.extend(results.get('ranked_items', []))
        tgs.extend(results.get('items', []))
        if len(tgs) >= limit:
            break
        more_available = results['more_available']
    return tgs # results['items'] returned

def getHashtagFeedGen(gen_token = Client.generate_uuid(), hashtag = 'cats', limit = 60):
    results = api.feed_tag(hashtag, gen_token)
    tgs_number = len(results.get('ranked_items', []))
    tgs_number += len(results.get('items', []))
    yield results.get('ranked_items', []) + results.get('items', [])
    more_available = results['more_available']
    while more_available:
        results = api.feed_tag(hashtag, gen_token)
        yield results.get('ranked_items', []) + results.get('items', [])
        tgs_number += len(results.get('ranked_items', []) + results.get('items', []))
        if tgs_number >= limit:
            break
        more_available = results['more_available']
    #return tgs # results['items'] returned

def getAllUsers(user_id = '2958144170', rank_token = Client.generate_uuid()):

    followers = []
    results = api.user_followers(user_id, rank_token)
    followers.extend(results.get('users', []))

    next_max_id = results.get('next_max_id')
    while next_max_id:
        results = api.user_followers(user_id, rank_token, max_id=next_max_id)
        followers.extend(results.get('users', []))
        next_max_id = results.get('next_max_id')

    followers.sort(key=lambda x: x['pk'])
    return [id['pk'] for id in followers]

def getAllUsersGen(user_id = '2958144170', rank_token = Client.generate_uuid()):

    followers = []
    results = api.user_followers(user_id, rank_token)
    followers = results.get('users', [])
    yield [id['pk'] for id in followers]

    next_max_id = results.get('next_max_id')
    while next_max_id:
        results = api.user_followers(user_id, rank_token, max_id=next_max_id)
        followers = results.get('users', [])
        yield [id['pk'] for id in followers]
        next_max_id = results.get('next_max_id')

    #followers.sort(key=lambda x: x['pk'])
    #return [id['pk'] for id in followers]

class Profile:
    def __init__ (self, id, api):

        profile = api.user_info(id)['user']
        # check info in user and pk
        self.pk = id

        self.is_private = profile['is_private']
        self.user_id = profile['pk']
        self.username = profile['username']
        self.name = profile['full_name']
        self.number_of_followers = profile['follower_count']
        self.email = [] # get mail - bio and post    +-> re #2
        self.phones = [] # get phone - bio and post  +-> re #3

        self.bio = profile['biography']

        self.hongkong = '' # func integration        +-> integrate ↓ #8

        self.localPostsNumber = 0 # helper ↓
        self.localPostsNumberBad = 0 # helper ↓
        self.lonlat = 0 # localPosts helper ↓

        self.localPosts = '' # check 3 post locations (+/-) +-> get ['locations'] #7
        self.language = '' # check bio and post (+)  +-> polyglot #5 <- install polyglot
        self.emoji = '' # check bio and post (+)     +-> if exists in string #1
        self.phonecode = '' # till phone not found   +-> re #4
        self.localTagWord = '' # check tags bio and post +-> get tags list #6

        #self.twtUserCountry = '' # maybe add checker -> twt.api + twt.api.country #9

    def get_mail(self, s):
        emails = re.findall("([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", s)
        if emails:
            self.email.extend(i for i in emails if i not in self.email)

    def is_flag(self, s):
        need = ['🇭🇰', '\U0001F1ED\U0001F1F0']
        if not self.emoji:
            for n in need:
                if n in s:
                    self.emoji = '+'
                    break

    def find_phone_numbers(self, s):
        phones = re.findall('\(*\+*[1-9]{0,3}\)*-*[1-9]{0,3}[-. /]*\(*[2-9]\d{2}\)*[-. /]*\d{3}[-. /]*\d{4} *e*x*t*\.* *\d{0,4}',s)#'[+]*([(]{0,1}[0-9]{1,4}[)]{0,1}[-\s\./0-9()]*){7,14}',s)
        if phones:
            self.phones.extend(i for i in phones if i not in self.phones)

    def checkPhoneCode(self):
        if self.phonecode != '+':
            if self.phones:
                for phone in self.phones:
                    code = getCode(phone)
                    if code == '852': #Hong Kong code
                        self.phonecode = '+'
                        break

    def checkLanguage(self, s):

        if self.language != '+':
            try:
                for language in Detector(str(s)).languages:
                    if 'chinese' in language.name.lower() or 'китайский' in language.name.lower(): #check Hong Kong is Chinese?
                        self.language = '+'
                        break
            except base.UnknownLanguage:
                print('polyglot cant')
            except pclderror:
                print('pcld cant')

    def checkLocation(self, item):
        if 'location' in item.keys():
            location = item.get('location',{}).get('name','')
            lng = item.get('location',{}).get('lng',0.0)
            lat = item.get('location',{}).get('lat',0.0)
            names = ['Hongkong', 'Hong Kong']

            if names[0] in location or names[1] in location:
                self.localPostsNumber += 1
            else:
                self.localPostsNumberBad += 1

            if (lng >= 113.83 and lng <= 114.407) and (lat >= 22.15 and lat <= 22.557):
                self.lonlat += 1

    def locationDecision(self):
        if self.localPostsNumber >= 3 or self.lonlat >= 3:
            self.localPosts = '+'
        elif self.localPostsNumberBad >= 3:
            self.localPosts = '-'

    def checkTagWord(self, s):
        if not self.localTagWord:
            chin = ['香港', '特別', '行政', '區']
            eng = ['hongkong', 'hong kong']
            text = str(s.lower())
            for i in chin + eng:
                if i in text:
                    self.localTagWord = "+"
                    break

    def hongkongUser(self):
        if not self.hongkong :
            if self.localPosts == '+' or self.language == '+' or self.emoji == '+' or self.phonecode == '+' or self.localTagWord == '+':
                self.hongkong = '+'

    def getFeedGen(self, limit = 60): #user_id = '2958144170',

        results = api.user_feed(self.user_id)
        next_max_id = results.get('next_max_id')
        yield results.get('items', [])
        posts_num = len(results.get('items', []))

        while next_max_id:
            results = api.user_feed(self.user_id, max_id=next_max_id)
            yield results.get('items', [])
            posts_num += len(results.get('items', []))
            if posts_num >= limit:  # get only first 600 or so
                break
            next_max_id = results.get('next_max_id')

    # test every func separately #11

# Execution
if __name__ == '__main__':

    logging.basicConfig()
    logger = logging.getLogger('instagram_private_api')
    logger.setLevel(logging.WARNING)

    # Example command:
    # python examples/savesettings_logincallback.py -u "yyy" -p "zzz" -ht "cats,dogs"
    parser = argparse.ArgumentParser(description='collect leads')
    parser.add_argument('-u', '--username', dest='username', type=str, required=True)
    parser.add_argument('-p', '--password', dest='password', type=str, required=True)
    parser.add_argument('-fdnum', '--number_of_posts', dest='numposts', type=str, required=True)
    parser.add_argument('-debug', '--debug', action='store_true')

    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)

    print('Client version: {0!s}'.format(client_version))
    users = [i.strip() for i in args.username.split(',')]
    passwords = [i.strip() for i in args.password.split(',')]
    if len(users) != len(passwords):
        assert 'You missed something'
    api = Client(users[0], passwords[0])
    #hashtags = [i.strip() for i in args.hashtag.split(',')]
    #post_am_by_hash = int(args.numtags)
    post_am_by_user = int(args.numposts)

    # Search by hashtag
    writeToCsv('path', ['PK','Account name',
    'Number of followers',
    'Email',
    'Phone number',
    'Name',
    'Hong Kong',
    'Location',
    'Language',
    'Emoji Flag',
    'Phone code',
    'Location tag/word',
    'Private account'], 'w')

    ids = readCsv('path')
    #writeToCsv('path', ['id'], 'w')

    def processwr(id, api):
        P = Profile(id, api)
        P.get_mail(P.bio)
        P.is_flag(P.bio)
        P.find_phone_numbers(P.bio)
        #P.checkLanguage(P.bio)
        P.checkTagWord(P.bio)
        #try:
        if not P.is_private:
            for posts in P.getFeedGen(post_am_by_user):
                for post in posts:
                    P.checkLocation(post)
                    caption = post.get('caption',{})
                    if caption:
                        text = caption.get('text','')
                        if text:
                            P.get_mail(text)
                            P.is_flag(text)
                            P.find_phone_numbers(text)
                            #P.checkLanguage(text)
                            P.checkTagWord(text)

        P.checkPhoneCode()
        P.locationDecision()
        P.hongkongUser()

        writeToCsv('path', [P.pk, P.username, P.number_of_followers, plusList(P.email), plusList(P.phones),
        P.name, P.hongkong, P.localPosts, P.language, P.emoji, P.phonecode, P.localTagWord, '+' if P.is_private else ''], 'a')

    indid = 0
    last_ids = []
    for id in ids:
    #time.sleep(1)
        try:
            indid += 1
            processwr(id, api)
        except errors.ClientThrottledError:
            print('id error - ', indid)
            time.sleep(10)
            api = Client(users[1], passwords[1])
            last_ids = ids[id:]
            for id in last_ids:
                try:
                    indid += 1
                    processwr(id, api)
                except errors.ClientThrottledError:
                    print('id error - second user - ', indid)
                    time.sleep(10)
                    api = Client(users[2], passwords[2])
                    last_ids = ids[id:]
                    for id in last_ids:
                        try:
                            indid += 1
                            processwr(id, api)
                        except errors.ClientThrottledError:
                            print('id error - third user - ', indid)
                            time.sleep(20)
                            api = Client(users[0], passwords[0])
                            last_ids = ids[id:]
                            for id in last_ids:
                                try:
                                    indid += 1
                                    processwr(id, api)
                                except errors.ClientThrottledError:
                                    print('id2 error - first user - ', indid)
                                    time.sleep(20)
                                    api = Client(users[1], passwords[1])
                                    last_ids = ids[id:]
                                    for id in last_ids:
                                        try:
                                            indid += 1
                                            processwr(id, api)
                                        except errors.ClientThrottledError:
                                            print('id2 error - second user - ', indid)
                                            time.sleep(20)
                                            api = Client(users[2], passwords[2])
                                            last_ids = ids[id:]
                                            for id in last_ids:
                                                try:
                                                    indid += 1
                                                    processwr(id, api)
                                                except errors.ClientThrottledError:
                                                    print('id2 error - third user - ', indid)
                                                    time.sleep(40)
                                                    api = Client(users[0], passwords[0])
                                                    last_ids = ids[id:]
                                                    for id in last_ids:
                                                        try:
                                                            indid += 1
                                                            processwr(id, api)
                                                        except errors.ClientThrottledError:
                                                            print('id3 error - first user - ', indid)
                                                            writeToCsv('path', list_ids, 'w')
        except:
            print('id error - indid -', indid)
            print('id stop - ', id)
            rest_ids = last_ids
            writeToCsv('path', rest_ids, 'w')

'''    userHB = api.username_info(args.user_to_parse)
    userHB_id = userHB['user']['pk']
    iterb = 0
    leniterb = 0
    writeToCsvRows('path', [[userHB_id]], 'a')
    print('userHB_id - ', userHB_id)

    for plus_ids in getAllUsersGen(userHB_id):
        ids = [[j] for j in plus_ids]
        writeToCsvRows('path', ids, 'a')
        #plus_ids = [userHB_id] + userHB_followers
        iterb += 1
        leniterb += len(ids)
        print('iterb ', iterb, ' - ', len(plus_ids))
        for id in plus_ids:
            try:
                #time.sleep(1)

                P = Profile(id, api)
                P.get_mail(P.bio)
                P.is_flag(P.bio)
                P.find_phone_numbers(P.bio)
                P.checkLanguage(P.bio)
                P.checkTagWord(P.bio)
                #try:
                if not P.is_private:
                    for posts in P.getFeedGen(post_am_by_user):
                        for post in posts:
                            P.checkLocation(post)
                            caption = post.get('caption', {})
                            if caption:
                                text = caption.get('text', '')
                                if text:
                                    P.get_mail(text)
                                    P.is_flag(text)
                                    P.find_phone_numbers(text)
                                    P.checkLanguage(text)
                                    P.checkTagWord(text)

                P.checkPhoneCode()
                P.locationDecision()
                P.hongkongUser()

                writeToCsv('path', [P.username, P.number_of_followers, plusList(P.email), plusList(P.phones),
                P.name, P.hongkong, P.localPosts, P.language, P.emoji, P.phonecode, P.localTagWord, '+' if P.is_private else '-'], 'a')

            except errors.ClientThrottledError:
                print('user id error')
                list_ids = plus_ids[id:]
                writeToCsv('path', list_ids, 'w')
                time.sleep(1)
                exit()
    print('leniterb - ', leniterb)
    try:

        P = Profile(userHB_id, api)
        P.get_mail(P.bio)
        P.is_flag(P.bio)
        P.find_phone_numbers(P.bio)
        P.checkLanguage(P.bio)
        P.checkTagWord(P.bio)
        #try:
        if not P.is_private:
            for posts in P.getFeedGen(post_am_by_user):
                for post in posts:
                    P.checkLocation(post)
                    caption = post.get('caption',{})
                    if caption:
                        text = caption.get('text','')
                        if text:
                            P.get_mail(text)
                            P.is_flag(text)
                            P.find_phone_numbers(text)
                            P.checkLanguage(text)
                            P.checkTagWord(text)

        P.checkPhoneCode()
        P.locationDecision()
        P.hongkongUser()

        writeToCsv('path', [P.username, P.number_of_followers, plusList(P.email), plusList(P.phones),
        P.name, P.hongkong, P.localPosts, P.language, P.emoji, P.phonecode, P.localTagWord, '+' if P.is_private else '-'], 'a')

    except errors.ClientThrottledError:
        print('userHB_id error')'''
