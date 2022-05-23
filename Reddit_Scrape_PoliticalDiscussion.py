import math
import json
import requests
import itertools
import numpy as np
import time
from datetime import datetime, timedelta
import praw
from praw.models import Comment
import csv

subreddit = 'PoliticalDiscussion'

def make_request(uri, max_retries = 5):
    def fire_away(uri):
        response = requests.get(uri)
        assert response.status_code == 200
        return json.loads(response.content)
    current_tries = 1
    while current_tries < max_retries:
        try:
            time.sleep(1)
            response = fire_away(uri)
            return response
        except:
            time.sleep(1)
            current_tries += 1
    return fire_away(uri)


def pull_posts_for(subreddit, start_at, end_at):

    def map_posts(posts):
        return list(map(lambda post: {
            'id': post['id'],
            'created_utc': post['created_utc'],
            'prefix': 't4_'
        }, posts))

    SIZE = 500
    URI_TEMPLATE = r'https://api.pushshift.io/reddit/search/submission?subreddit={}&after={}&before={}&size={}'

    post_collections = map_posts( \
        make_request( \
            URI_TEMPLATE.format( \
                subreddit, start_at, end_at, SIZE))['data'])
    n = len(post_collections)
    while n == SIZE:
        last = post_collections[-1]
        new_start_at = last['created_utc'] - (10)

        more_posts = map_posts( \
            make_request( \
                URI_TEMPLATE.format( \
                    subreddit, new_start_at, end_at, SIZE))['data'])

        n = len(more_posts)
        post_collections.extend(more_posts)
    return post_collections


def give_me_intervals(start_at, number_of_days_per_interval = 1):

    end_at = math.ceil(datetime.utcnow().timestamp())

    ## 1 day = 86400,
    period = (86400 * number_of_days_per_interval)
    end = start_at + period
    yield (int(start_at), int(end))
    padding = 1
    while end <= end_at:
        start_at = end + padding
        end = (start_at - padding) + period
        yield int(start_at), int(end)

#########################################################################################################################################

Counter = 0

start_at = math.floor(\
    (datetime.utcnow() - timedelta(days=2920)).timestamp())
posts = []
for interval in give_me_intervals(start_at, 1):
    pulled_posts = pull_posts_for(
        subreddit, interval[0], interval[1])

    posts.extend(pulled_posts)
    time.sleep(.500)

reddit = praw.Reddit(client_id='XXXXXXXXXXXXXXXXX', client_secret='XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', user_agent='my_user_agent')

print(len(posts))
limitvariable = None
print(len(np.unique([ post['id'] for post in posts ])))

with open('D:\\ELASTIC_SEARCH\\Reddit_' + subreddit + '.csv', 'w',encoding="utf-8") as csv_output:
        comment_writer = csv.writer(csv_output)
        comment_writer.writerow(["Subreddit","Create_Date", "Upvote_Ratio", "Title", "Comment"])
        posts_from_reddit = []
        comments_from_reddit = []
        try:
            for submission_id in np.unique([ post['id'] for post in posts ]):
                print("Posts Completed = ", Counter)
                Counter += 1
                try:

                    submission = reddit.submission(id=submission_id)
                    print("LENGTH = ", len(submission.comments))
                    if len(submission.comments) > 200:
                        limitvariable = 0
                    else:
                        limitvariable = None
                    submission.comments.replace_more(limit=limitvariable)
                except Exception as e:
                    print("ERROR OCCURED 1")
                    continue




                try:

                    for comment in submission.comments.list():
                            if isinstance(comment, praw.models.Comment):
                                comment_writer.writerow([subreddit, submission.created_utc, submission.upvote_ratio, submission.title, comment.body.replace("\n"," ")])
                except:
                    print("ERROR OCCURED 1")
                    continue
        except:
            print(e)
            print("ERROR OCCURED OUTER LOOP")
