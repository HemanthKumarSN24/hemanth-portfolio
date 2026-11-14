#!/usr/bin/env python3
"""
Social Media Automation Engine — SN Hemanth
Posts text + media to X (Twitter), Instagram, LinkedIn once API keys are in ~/.hermes/.env
Usage: python3 social_media_engine.py post --platform twitter --text "..." --media path.jpg
"""

import os, sys, json, argparse, requests

ENV_PATH = os.path.expanduser('~/.hermes/.env')

def load_env():
    cfg = {}
    if os.path.exists(ENV_PATH):
        for line in open(ENV_PATH):
            if '=' in line and not line.startswith('#'):
                k, _, v = line.strip().partition('=')
                cfg[k] = v
    return cfg

def post_twitter(cfg, text, media_path=None):
    """X/Twitter API v2 — needs TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET"""
    try:
        import tweepy
        auth = tweepy.OAuth1UserHandler(
            cfg['TWITTER_API_KEY'], cfg['TWITTER_API_SECRET'],
            cfg['TWITTER_ACCESS_TOKEN'], cfg['TWITTER_ACCESS_SECRET'])
        api = tweepy.API(auth)
        if media_path and os.path.exists(media_path):
            media = api.media_upload(media_path)
            api.update_status(status=text, media_ids=[media.media_id])
        else:
            api.update_status(status=text)
        return {'status': 'posted', 'platform': 'twitter'}
    except ImportError:
        return {'status': 'error', 'msg': 'pip install tweepy first'}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)[:100]}

def post_instagram(cfg, image_path, caption):
    """Instagram Graph API — needs IG_USER_ID, IG_ACCESS_TOKEN (Business/Creator account required)"""
    try:
        user_id = cfg['IG_USER_ID']
        token = cfg['IG_ACCESS_TOKEN']
        # Step 1: upload media
        r = requests.post(f'https://graph.facebook.com/v18.0/{user_id}/media', data={
            'image_url': image_path, 'caption': caption, 'access_token': token})
        creation_id = r.json().get('id')
        if not creation_id:
            return {'status': 'error', 'msg': r.json().get('error', {}).get('message', 'upload failed')}
        # Step 2: publish
        r2 = requests.post(f'https://graph.facebook.com/v18.0/{user_id}/media_publish',
                          data={'creation_id': creation_id, 'access_token': token})
        return {'status': 'posted', 'platform': 'instagram', 'id': r2.json().get('id')}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)[:100]}

def post_linkedin(cfg, text):
    """LinkedIn API — needs LINKEDIN_ACCESS_TOKEN (from OAuth flow)"""
    try:
        token = cfg['LINKEDIN_ACCESS_TOKEN']
        author = cfg.get('LINKEDIN_PERSON_URN', 'urn:li:person:YOUR_URN')
        r = requests.post('https://api.linkedin.com/v2/ugcPosts',
            headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
                     'X-Restli-Protocol-Version': '2.0.0'},
            json={
                'author': author,
                'lifecycleState': 'PUBLISHED',
                'specificContent': {
                    'com.linkedin.ugc.ShareContent': {
                        'shareCommentary': {'text': text},
                        'shareMediaCategory': 'NONE'
                    }
                },
                'visibility': {'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'}
            })
        return {'status': 'posted' if r.status_code == 201 else 'error',
                'code': r.status_code, 'msg': r.text[:100] if r.status_code != 201 else ''}
    except Exception as e:
        return {'status': 'error', 'msg': str(e)[:100]}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('action', choices=['post', 'check'])
    p.add_argument('--platform', choices=['twitter', 'instagram', 'linkedin'])
    p.add_argument('--text', default='')
    p.add_argument('--media', default=None)
    args = p.parse_args()

    cfg = load_env()

    if args.action == 'check':
        keys = ['TWITTER_API_KEY', 'IG_USER_ID', 'IG_ACCESS_TOKEN', 'LINKEDIN_ACCESS_TOKEN']
        for k in keys:
            print(f"  {k}: {'SET' if k in cfg else 'MISSING'}")
        return

    if not args.platform:
        print('specify --platform'); return

    if args.platform == 'twitter':
        print(json.dumps(post_twitter(cfg, args.text, args.media)))
    elif args.platform == 'instagram':
        print(json.dumps(post_instagram(cfg, args.media or '', args.text)))
    elif args.platform == 'linkedin':
        print(json.dumps(post_linkedin(cfg, args.text)))

if __name__ == '__main__':
    main()
