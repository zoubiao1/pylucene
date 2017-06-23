# coding=utf-8
# !/usr/bin/env python
import os
import logging
import sys
logger = logging.getLogger()
import lucene
lucene.initVM()
from java.io import File  # @UnresolvedImport
from org.apache.lucene.analysis.standard import StandardAnalyzer  # @UnresolvedImport
from org.apache.lucene.queryparser.classic import QueryParser  # @UnresolvedImport
from org.apache.lucene.store import SimpleFSDirectory  # @UnresolvedImport
from org.apache.lucene.util import Version  # @UnresolvedImport
from org.apache.lucene.index import FieldInfo, IndexWriter, IndexWriterConfig, DirectoryReader, Term, \
    IndexReader  # @UnusedImport
from org.apache.lucene.document import Document, Field, FieldType  # @UnresolvedImport
from org.apache.lucene.search import IndexSearcher, TermQuery, BooleanQuery  # @UnresolvedImport
from org.apache.pylucene.search.similarities import PythonDefaultSimilarity  # @UnresolvedImport
from org.apache.lucene.queries.mlt import MoreLikeThis  # @UnresolvedImport
from starpro.settings import LUCENE_MAIN_PATH
reload(sys)
sys.setdefaultencoding('utf-8')

INDEX_PATH = os.path.join(LUCENE_MAIN_PATH,'data')

class CustomSimilarity(PythonDefaultSimilarity):  # SIM
    # def computeNorm(self, state, norm):
    #    return state.getBoost()

    def lengthNorm(self, numTerms):
        return 1.0


class Searcher(object):  # 搜索类
    def __init__(self, indexDir,
                 computeLengthNorm=True):  # 初始化 indexDir-索引文件目录 computeLengthNorm-是否应用SIM（true-不用 false-应用）
        #         if not jpype.isJVMStarted():
        #         lucene.initVM()
        lucene.getVMEnv().attachCurrentThread()
        self.analyzer = StandardAnalyzer(Version.LUCENE_CURRENT)  # 标准分词 在针对英文时 以分隔符分词
        self.path = os.path.join(INDEX_PATH, indexDir)  # 存储路径
        self.store = SimpleFSDirectory(File(self.path))  # 存储***？
        # self.reader = DirectoryReader.open(self.store)
        self.reader = IndexReader.open(self.store)
        self.numDocs = self.reader.maxDoc()
        self.searcher = IndexSearcher(self.reader)  # IndexSearch类
        sim = CustomSimilarity()  # addby zmq
        if not computeLengthNorm:  # SIM
            sim = CustomSimilarity()
            self.searcher.setSimilarity(sim)
        self.mlt = MoreLikeThis(self.reader, sim)  # mlt？
        self.mlt.setAnalyzer(self.analyzer)
        self.mlt.setMinTermFreq(1)
        self.mlt.setMinDocFreq(1)
        # debug
        self.mlt.setMinWordLen(1)
        self.mlt.setMaxNumTokensParsed(100000000)
        BooleanQuery.setMaxClauseCount(1024 * 1024)  # 修改最长query clause BUG
        # debug

    def searchKeyWords(self, key_value, max_num):  # 查询text域中的指定字符匹配的文档
        key_value = str(key_value.encode('utf-8'))
        if type(key_value) != type('') or len(key_value) == 0:
            raise Exception('Please provide a string.')
        # term = ('text',key_value)
        # termquery = TermQuery(Term(*term))
        query = QueryParser(Version.LUCENE_CURRENT, "title", self.analyzer).parse(key_value)
        #         query = FuzzyQuery(Version.LUCENE_CURRENT, "title",self.analyzer).parse(key_value)###模糊查询

        self.query = query
        results = self.searcher.search(query, max_num)
        result_list = []
        # print len(results.scoreDocs),results.scoreDocs
        for each_result in results.scoreDocs:
            docid = each_result.doc
            result_list.append(self.searcher.doc(docid)['key'])
        return result_list

    def getDocID(self, dictID):  # 查询某个term命中的文档号 dictID为Key-Value(例如key-'title' value-seller_id)
        if len(dictID) != 1:
            raise Exception('Please provide a dict with one pair of field and value.')
        term = dictID.items()[0]
        termquery = TermQuery(Term(*term))
        self.query = termquery
        results = self.searcher.search(termquery, 10)
        try:
            if len(results.scoreDocs) < 1:
                return None
            docid = results.scoreDocs[0].doc
            print 'id:', docid
            return docid
        except Exception, e:
            logger.error('Doc not found: %s', str(dictID))
            raise Exception('Doc not found: %s', str(dictID))

    def getSimilarDocs(self, dictID={}, similarfields=['title'], nDocs=100000000):  # 查询'text'域相似文档
        docid = self.getDocID(dictID)
        if docid == None:
            return None
        self.mlt.setFieldNames(similarfields)
        query = self.mlt.like(docid)
        self.query = query
        similardocs = self.searcher.search(query, nDocs)
        self.hits = similardocs
        print 'len:', len(similardocs.scoreDocs)
        return [(self.searcher.doc(scoreDoc.doc).get(dictID.items()[0][0]), scoreDoc.score) for scoreDoc in
                similardocs.scoreDocs]


class Indexer(object):  # 建立索引
    def __init__(self, indexDir, doClear=True, computeLengthNorm=False):
        #         if not jpype.isJVMStarted():
        #         lucene.initVM()
        lucene.getVMEnv().attachCurrentThread()
        self.analyzer = StandardAnalyzer(Version.LUCENE_CURRENT)
        # self.analyzer = LimitTokenCountAnalyzer(self.analyzer, 100678)#is here?
        self.config = IndexWriterConfig(Version.LUCENE_CURRENT, self.analyzer)
        self.config.setRAMBufferSizeMB(256.0)  # 设置自动提交的最大RAM为256MB
        self.config.setMaxBufferedDocs(10000)  # 设置自动提交的最大Docs个数为10000
        if not computeLengthNorm:
            sim = CustomSimilarity()
            self.config.setSimilarity(sim)
        self.path = os.path.join(INDEX_PATH, indexDir)
        # print self.path
        # path.mkdir(self.path)
        #         if doClear:
        #             self.clearExistingIndex()
        self.store = SimpleFSDirectory(File(self.path))
        self.writer = IndexWriter(self.store, self.config)

        self.t1 = FieldType()  # 域t1
        self.t1.setIndexed(True)
        self.t1.setStored(True)
        self.t1.setTokenized(False)
        self.t1.setIndexOptions(FieldInfo.IndexOptions.DOCS_AND_FREQS)

        self.t2 = FieldType()  # 域t2
        self.t2.setIndexed(True)
        self.t2.setStored(False)
        self.t2.setTokenized(True)
        self.t2.setIndexOptions(FieldInfo.IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)

    def clearExistingIndex(self):  # 删除索引？
        indexdir = self.path
        for thefile in os.listdir(indexdir):
            filepath = os.path.join(indexdir, thefile)
            try:
                if os.path.isfile(filepath):
                    os.unlink(filepath)
            except Exception, e:
                logger.error("Delete file %s failed: %s", filepath, str(e))

                # add by zhumingqing  建立索引
                #     def indexwriter(self,index_name):
                #         indexer = Indexer(index_name, computeLengthNorm = False)
                #         global searcher
                #         searcher = Searcher(index_name,True)
                #         product_dict={}
                #         keywords_products = InternalProducts.objects.all()
                #         for p in keywords_products:
                #             if type(p.title) != type(None) and len(p.title) != 0:
                #                 product_dict['sku']=p.sku
                #                 product_dict['title']=p.title
                #                 indexer.indexDict(product_dict)##建立索引
                #         indexer.commit()
                #         indexer.close()

    def indexDict(self, dictDoc):  # 建立索引
        doc = Document()
        for key, value in dictDoc.items():
            if key == 'title':
                doc.add(Field(key, value, self.t2))
            else:
                doc.add(Field(key, value, self.t1))
        try:
            self.writer.addDocument(doc)
            # self.numDocs = self.writer.maxDoc()
            # if self.numDocs>1000:
            #    self.commit()
            print 'index added for:', dictDoc['key'], 'total:', self.writer.maxDoc()
            logger.info('Index added for: %s', dictDoc['key'])
        except Exception, e:
            print e
            logger.error('Create index failed: %s', str(e))

    def indexDict_delete(self, dictDoc):  # 删除
        doc = []
        for key, value in dictDoc.items():
            doc.append(Term(key, value))
        try:
            self.writer.deleteDocuments(doc)
            # self.numDocs = self.writer.maxDoc()
            # if self.numDocs>1000:
            #    self.commit()
            print 'index delete for:', dictDoc['key'], 'total:', self.writer.maxDoc()
            logger.info('Index delete for: %s', dictDoc['key'])
        except Exception, e:
            print e
            logger.error('Delete index failed: %s', str(e))

    def commit(self):  # 提交索引
        self.writer.commit()

    def close(self):  # Indexwriter close
        self.writer.close()


def main(keyword):
    # indexer = Indexer('test.index', computeLengthNorm=False)
    # print 'config similarity:', indexer.config.getSimilarity()
    # indexer.indexDict({'title': 'A29JIFH4ZXPNL8', 'text': 'B00AOBEWM2 B00BQXUSJ6 B0087ZBRPM'})
    #
    # #     _test_totti1 = 'B00BQXUSJ8 B00BQXUSJ7 B00BQXUSJ6'
    # #     _test_i = 1
    # #     while _test_i < 17:
    # #         _test_totti1 = _test_totti1 + " " +  _test_totti1
    # #         print(" append num " + str(_test_i) + " len :" + str(len(_test_totti1)))
    # #         test_i = _test_i + 1
    # indexer.indexDict_delete({'title': '中文 学子', 'sku': '范德萨的范德萨发'})
    # indexer.indexDict({'title': 'sku dasf45241dsaf', 'sku': 'tetetetetest25'})
    # indexer.indexDict({'title': 'B007WADRBK B0056KJIO8 B008X0N0H4', 'sku': 'xys'})
    # indexer.indexDict({'title': '中文 学子', 'sku': '范德萨的范德萨发'})
    # indexer.indexDict({'title': 'A1THAZDOwwwwKK1', 'text': 'B00BQXUSJ8 B00BQXUSJ7 B00BQXUSJ6'})
    # indexer.indexDict({'title': 'A1THAZDOKKKKK2', 'text': 'B00BQXUSJ4 B00BQXUSJ7 B00BQXUSJ6'})
    # indexer.indexDict({'title': 'A1THAZDOKcghKK3', 'text': 'B00BQXUSJ8 B00BQXUSJ7 B00BQXUSJ6'})
    # indexer.indexDict({'title': 'A1THAZDOKKKKK4', 'text': 'B00BQXUSJ8 B00BQXUSJ9 B00BQXUSJ6'})
    # indexer.indexDict({'title': 'A1THAZDOKKKKK5', 'text': 'B00BQXUSJ8 B00BQXUSJ7 B00BQXUSJ6'})
    # indexer.indexDict({'title': 'test3', 'text': 'sdf7gdf b c'})
    # indexer.indexDict({'title': 'test4', 'text': 'b h d'})
    # indexer.indexDict({'title': 'test5', 'text': 'sdf7gdf b c e f h q w e r t y u i o p a s d f g h j k l z x v  n m'})
    # indexer.indexDict({'title': 'test6', 'text': 'sdf7gdf b e f'})
    # indexer.indexDict({'title': 'test7', 'text': 'sdf7gdf g h'})
    # indexer.indexDict({'title': 'test8', 'text': 'c x y'})
    # indexer.commit()
    searcher = Searcher('asin_index', True)
    print keyword
    print searcher.searchKeyWords(keyword, 10000)
    print searcher.searchKeyWords('数学', 10000)



