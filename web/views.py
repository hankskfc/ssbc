#coding: utf8
import re
import datetime
import sys
import urllib
import requests
from django.http import Http404
from django.shortcuts import render, redirect

API_URL = 'http://127.0.0.1:8001/api/'
API_HOST = 'www.shousibaocai.com'
re_punctuations = re.compile(
    u"。|，|,|！|…|!|《|》|<|>|\"|'|:|：|？|\?|、|\||“|”|‘|’|；|—|（|）|·|\(|\)|　|\.|【|】|『|』|@|&|%|\^|\*|\+|\||<|>|~|`|\[|\]")
req_session = requests.Session()

# Create your views here.
def index(request):
    reclist = ['速度与激情7','王牌特工','战狼','左耳','咱们结婚吧']
    d = {'reclist': reclist}
    return render(request, 'index.html', d)

def hash(request, h):
    qs = {
        'hashes': h,
    }
    url = API_URL + 'json_info?' + urllib.urlencode(qs)
    r = req_session.get(url, headers={'Host':API_HOST})
    try:
        j = r.json()
    except:
        raise Http404(sys.exc_info()[1])
    d = {'info': j[h]} 
    d['keywords'] = list(set(re_punctuations.sub(u' ', d['info']['name']).split()))
    if 'files' in d['info']:
        d['info']['files'] = [y for y in d['info']['files'] if not y['path'].startswith(u'_')]
        d['info']['files'].sort(key=lambda x:x['length'], reverse=True)
    d['magnet_url'] = 'magnet:?' + urllib.urlencode({'xt':'urn:btih:%s'% (d['info']['info_hash']), 'dn':d['info']['name'].encode('utf8')})
    d['download_url'] = 'http://www.so.com/s?' + urllib.urlencode({'ie':'utf-8', 'src': 'ssbc', 'q': d['info']['name'].encode('utf8')})
    return render(request, 'info.html', d)


def search(request, keyword, p):
    d = {'keyword': keyword}
    d['words'] = list(set(re_punctuations.sub(u' ', d['keyword']).split()))
    try:
        d['p'] = int(p)
    except:
        d['p'] = 1
    d['ps'] = 10
    d['offset'] = d['ps']*(d['p']-1)
    # Fetch list
    qs = {
        'keyword': keyword.encode('utf8'),
        'count': d['ps'],
        'start': d['offset'],
    }
    url = API_URL + 'json_search?' + urllib.urlencode(qs)
    r = req_session.get(url, headers={'Host':API_HOST})
    d.update(r.json())
    # Fill info
    ids = '-'.join([str(x['id']) for x in d['result']['items']])
    if ids:
        qs = {
            'hashes': ids,
        }
        url = API_URL + 'json_info?' + urllib.urlencode(qs)
        r = req_session.get(url, headers={'Host':API_HOST})
        j = r.json()

        for x in d['result']['items']:
            x.update(j[str(x['id'])])
            x['magnet_url'] = 'magnet:?' + urllib.urlencode({'xt':'urn:btih:%s'% (x['info_hash']), 'dn':x['name'].encode('utf8')})
            if 'files' in x:
                x['files'] = [y for y in x['files'] if not y['path'].startswith(u'_')][:5]
                x['files'].sort(key=lambda x:x['length'], reverse=True)
            else:
                x['files'] = [{'path': x['name'], 'length': x['length']}]
    # pagination
    w = 10
    total = int(d['result']['meta']['total'])
    d['page_max'] = total / d['ps'] if total % d['ps'] == 0 else total/d['ps'] + 1
    d['prev_pages'] = range( max(d['p']-w+min(int(w/2), d['page_max']-d['p']),1), d['p'])
    d['next_pages'] = range( d['p']+1, int(min(d['page_max']+1, max(d['p']-w/2,1) + w )) )
    return render(request, 'list.html', d)

def hash_old(request, h):
    return redirect('/hash/' + h, permanent=True)

def search_old(request, kw, p):
    return redirect('list', kw, p)

