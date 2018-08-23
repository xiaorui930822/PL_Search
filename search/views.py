from django.shortcuts import render
from django.views.generic.base import View
import json
from django.http import HttpResponse
from elasticsearch import Elasticsearch
from datetime import datetime
import redis
from pure_pagination import Paginator
from search.models import ArticalType, LagouType


client = Elasticsearch(hosts=['localhost:9200'])
redis_cli = redis.StrictRedis()


# Create your views here.
class IndexView(View):
    # 首页热门搜索
    def get(self, request):
        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=5)
        topnum = len(topn_search)
        if not topnum:
            topnum = 0
        for i in range(topnum):
            topn_search[i] = topn_search[i].decode('utf-8')
        return render(request, 'index.html', {
            "topn_search": topn_search,
            "topnum":topnum,
        })


class SearchSuggest(View):
    def get(self, request):
        key_words = request.GET.get('s', '')
        search_index = request.GET.get('s_type', 'artical')
        re_datas = []
        if key_words:
            if search_index == 'artical':
                s_search = ArticalType.search()
            elif search_index == 'job':
                s_search = LagouType.search()
           # s_search = ArticalType.search()
            ss = s_search.suggest('my_suggest', key_words, completion={
                "field": "suggest", "fuzzy": {
                    "fuzziness": 2
                },
                "size": 10
            })
            suggestions = ss.execute_suggest()
            for match in suggestions.my_suggest[0].options:
                source = match._source
                re_datas.append(source['title'])
        return HttpResponse(json.dumps(re_datas), content_type="application/json")


class SearchView(View):
    def get(self, request):
        key_words = request.GET.get('q', '')
        if not key_words:
            key_words = 'python'  # 设置默认搜索语句
        redis_cli.zincrby("search_keywords_set", key_words)
        topn_search = redis_cli.zrevrangebyscore("search_keywords_set", "+inf", "-inf", start=0, num=5)
        for i in range(len(topn_search)):
            topn_search[i] = topn_search[i].decode('utf-8')
        # 页码
        page = request.GET.get('page', '1')
        try:
            page = int(page)
        except:
            page = 1
        artical_count = redis_cli.get("artical_count")
        if artical_count:
            artical_count = artical_count.decode('utf-8')
        lagou_count = redis_cli.get("lagou_count")
        if lagou_count:
            lagou_count = lagou_count.decode('utf-8')
        start_time = datetime.now()
        search_aim = request.GET.get('s_type', 'artical')
        if search_aim == 'artical':
            search_index = 'artical_linux'
            response = client.search(
                index=search_index,
                body={
                    "query": {
                        "multi_match": {
                            "query": key_words,
                            "fields": ['tags^2', 'title^3', 'content']
                        }
                    },
                    'from': 0,
                    "size": 9999,
                    "highlight": {
                        "pre_tags": ["<span class='keyWord'>"],
                        "post_tags": ["</span'>"],
                        "fields": {
                            "title": {},
                            "content": {},
                            "tags": {},
                        }
                    }

                }
            )
        if search_aim == 'job':
            search_index = 'lagou2_linux'
            response = client.search(
                index=search_index,
                body={
                    "query": {
                        "multi_match": {
                            "query": key_words,
                            "fields": ['tags^2', 'title^3', 'job_desc']
                        }
                    },
                    'from': 0,
                    "size": 9999,
                    "highlight": {
                        "pre_tags": ["<span class='keyWord'>"],
                        "post_tags": ["</span'>"],
                        "fields": {
                            "title": {},
                            "job_desc": {},
                            "tags": {},
                        }
                    }

                }
            )
        end_time = datetime.now()
        cose_seconds = (end_time - start_time).total_seconds()
        total_nums = response["hits"]["total"]
        if (page % 10) > 0:
            page_nums = int(total_nums / 10) + 1
        else:
            page_nums = int(total_nums / 10)
        hit_list = []
        for hit in response["hits"]["hits"]:
            hit_dict = {}
            # 文章标题
            if "title" in hit["highlight"]:
                hit_dict["title"] = "".join(hit["highlight"]["title"])
            else:
                hit_dict["title"] = hit["_source"]["title"]
                # 对于文章列表：
            if search_aim == 'artical':
                hit_dict["source"] = '伯乐在线'
                # 文章内容
                if "content" in hit["highlight"]:
                    hit_dict["content"] = "".join(hit["highlight"]["content"])[:500]
                else:
                    hit_dict["content"] = hit["_source"]["content"][:500]
            elif search_aim == 'job':
                hit_dict["source"] = '拉勾网'
                if "job_desc" in hit["highlight"]:
                    hit_dict["content"] = "".join(hit["highlight"]["job_desc"])[:500]
                else:
                    hit_dict["content"] = hit["_source"]["job_desc"][:500]

            hit_dict["create_date"] = hit["_source"]["create_date"]
            hit_dict["url"] = hit["_source"]["url"]
            hit_dict["score"] = hit["_score"]

            hit_list.append(hit_dict)
        p = Paginator(hit_list, 10, request=request)  # 页码为10的倍数
        hit_list_page = p.page(page)
        return render(request, 'result.html', {
            "all_hits": hit_list_page,
            "key_words": key_words,
            "page": page,
            "total_nums": total_nums,
            "page_nums": page_nums,
            "cose_seconds": cose_seconds,
            "artical_count": artical_count,
            "lagou_count": lagou_count,
            "topn_search": topn_search,
            "search_aim": search_aim,
        })


def page_not_found(request):
    # 全局404处理函数
    from django.shortcuts import render_to_response
    response = render_to_response('404.html', {})
    response.status_code = 404
    return response


def page_error(request):
    # 全局404处理函数
    from django.shortcuts import render_to_response
    response = render_to_response('500.html', {})
    response.status_code = 500
    return response
