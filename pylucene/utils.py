#coding:utf-8
from common import Indexer, Searcher
try:
    from starpro.settings import sku_index_name
except:
    sku_index_name = 'sku.index'


def create_index(index_name,dictdoc):
    indexer = Indexer(index_name)
    indexer.indexDict(dictdoc)
    indexer.commit()
    indexer.close()


def delete_index(index_name,dictdoc):
    indexer = Indexer(index_name)
    indexer.indexDict_delete(dictdoc)
    indexer.commit()
    indexer.close()



def search_keyword(index_name,keyword):
    try:
        _search = Searcher(index_name,True)
    except Exception,e:
        print type(e),'---d'
        return  []
    return _search.searchKeyWords(key_value=keyword,max_num=50)


#  添加产品索引文件
# dictdoc {'key':sku,'title':sku chinese_title}
def add_product_index(dictdoc):
    create_index(sku_index_name,dictdoc)


#  删除产品索引文件 由于没有更新操作, 如果更新title 请先删除原有索引
# dictdoc {'key':sku}
def delete_product_index(dictdoc):
    delete_index(sku_index_name,dictdoc)



if __name__ == '__main__':
    # create_index({'key':'sbs', 'title':'中美'})
    # delete_index({'key':'1234','title':'文字游戏'})
    search_keyword('sku_index',u'中美')
