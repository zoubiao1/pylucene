#coding:utf-8

index_name = 'asin_index'
from common import Indexer, Searcher


def test_create_index(dictdoc):
    print 'start'
    indexer = Indexer(index_name)
    indexer.indexDict(dictdoc)
    indexer.commit()
    indexer.close()
    print 'end create index'


def delete_index(dictdoc):
    print 'start delete index'
    indexer = Indexer(index_name)
    indexer.indexDict_delete(dictdoc)
    indexer.commit()
    indexer.close()
    print 'end create indexz'


def search_keyword(keyword):
    try:
        _search = Searcher(index_name,True)
    except Exception,e:
        print type(e),'---d'
        return  ''
    print _search.searchKeyWords(key_value=keyword,max_num=10)


if __name__ == '__main__':
    # test_create_index({'key':'sbs', 'title':'中美'})
    # delete_index({'key':'1234','title':'文字游戏'})
    search_keyword(u'中美')
