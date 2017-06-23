#coding:utf-8

pylucene 工具类
使用版本是4.9 ,安装方法参考环境搭建文档
PyLucene是Java版Lucene的Python版封装。
这个工具的目标是让Python使用Lucene的文本索引和搜索能力。
它与Java版Lucene的最新版本是兼容的。PyLucene把一个带有JAVA VM的Lucene嵌入到Python进程中。
你可以在http://lucene.apache.org/pylucene/网站上找到更多的PyLucene详情。


主要分成两个大的类

1.Indexer 建立索引使用
__init__(self, indexDir, doClear=True, computeLengthNorm=False) 索引目录,doClear 没有使用, computeLengthNorm-是否应用SIM ,使用默认值即可
clearExistingIndex(self) ## 谨慎使用, 清楚该索引目录的所有索引
indexDict(self, dictDoc) ### dictDoc = {'title':'xx','key':'xxx'}  建立索引 title用来查询比较  key 作为id
比如 {'title':'四阶魔方','key':'dddddd'}  搜索时和四阶魔方 比较.但是最后返回 ddddd(如果匹配上的话)
indexDict_delete(self, dictDoc) 删除键值对 ,没有更新操作,如有更新,请先删除再创建
commit(self) 提交新建的索引
close(self)  关闭连接


2.Searcher 主要是搜索使用 ,如果初始化时使用的 目录不存在或不是索引目录可能会抛异常
__init__ 初始化,加载索引目录等 一般传  一个 索引目录 'index_path' 即可
searchKeyWords(self, key_value, max_num) 核心功能,搜索相似数据. key_value,关键词  max_num 返回的最大记录数
getDocID(self, dictID):  # 查询某个term命中的文档号 dictID为Key-Value(例如key-'title' value-seller_id) 使用较少
getSimilarDocs(self, dictID={}, similarfields=['title'], nDocs=100000000):  # 查询'text'域相似文档 还没有具体了解(目前没有使用)


实例 在test_lucene

应用场景
产品模糊查询

使用流程 增加修改产品标题的时候删除或建立索引,使用标题和spu作为键值对, 搜索时根据关键词查找spu列表

使用时维护好自己的index_name
公共目录在 lucenedata/data/




