import json,time,unittest
from unittest.mock import patch
import numpy as np
import test_integration as app
import topic_evidence
import test_preparation_reliability as preparation_tests

class MaterialEvidenceTests(unittest.TestCase):
    def test_retrieval_filters_role_and_topic_before_ranking(self):
        class Encoder:
            def encode(self,query,**kwargs):return np.array([1.]+[0.]*383)
        c=app.rag_engine.vector_connection()
        try:
            for did,topic,role in [('right','C_SQL','role'),('wrong-topic','C_AI_ML','role'),('wrong-role','C_SQL','other')]:
                c.execute("INSERT INTO documents(id,title,status) VALUES(?,?,'ready')",(did,did))
                row=c.execute('INSERT INTO doc_chunks(doc_id,chunk_text,page_num) VALUES(?,?,1)',(did,did+' study content'))
                c.execute('INSERT INTO doc_chunks_vec(rowid,chunk_embedding) VALUES(?,?)',(row.lastrowid,json.dumps([1.]+[0.]*383)))
                c.execute('INSERT INTO document_topics VALUES(?,?)',(did,topic))
                c.execute('INSERT INTO document_assignments VALUES(?,?)',(did,role))
            c.commit()
        finally:c.close()
        with patch.object(app.rag_engine,'get_embedder',return_value=Encoder()):
            result=app.quiz_buffer.assigned_sources({'id':'C_SQL','name':'SQL'},{'role_id':'role'},None)
            self.assertEqual([x['doc_id'] for x in result],['right'])
            self.assertEqual(app.quiz_buffer.assigned_sources({'id':'C_GIS','name':'GIS'},{'role_id':'role'},None),[])

    def test_missing_topic_uses_general_knowledge_fallback(self):
        user=preparation_tests.PreparationTests().session('missing-material',2,1)
        calls=[]
        def generate(context,*args):
            calls.append(context)
            count=args[-1]
            return [dict(question=f'General topic question {i}?',options=['A','B','C','D'],correct_answer='A',explanation='General topic knowledge') for i in range(count)]
        with patch.object(app.quiz_buffer,'assigned_sources',return_value=[]),patch.object(app.rag_engine,'generate_mcqs_with_llm',side_effect=generate):
            app.quiz_buffer.ensure('missing-material',user)
        self.assertEqual(calls,['NONE'])
        self.assertEqual(app.quiz_buffer.status('missing-material')['status'],'ready')
        with app.db() as c:payloads=[json.loads(r[0]) for r in c.execute('SELECT payload FROM question_drafts WHERE session_id=?',('missing-material',))]
        self.assertTrue(all(q['grounding']=='model knowledge' and not q['sources'] for q in payloads))

    def test_bloom_evidence_and_skips(self):
        def row(depth,correct,answer=0):return dict(payload=json.dumps({'bloom_level':depth}),answer=answer,correct=correct)
        remember=topic_evidence.performance([row(1,1),row(1,1)])
        analyze=topic_evidence.performance([row(4,1),row(4,1)])
        self.assertEqual(remember['maximum_supported_level'],1)
        self.assertEqual(analyze['maximum_supported_level'],4)
        self.assertEqual(topic_evidence.performance([row(4,1)])['maximum_supported_level'],0)
        mixed=topic_evidence.performance([row(1,1),row(4,0,None)])
        self.assertEqual(mixed['weighted_score'],20)
        self.assertEqual(mixed['maximum_supported_level'],0)
        self.assertEqual(topic_evidence.performance([row(1,0),row(1,0),row(1,0),row(1,0)])['maximum_supported_level'],0)
        self.assertEqual(topic_evidence.performance([row(1,1),row(1,1),row(1,0),row(1,0)])['maximum_supported_level'],1)
        self.assertEqual(topic_evidence.performance([row(1,1),row(1,1),row(1,1),row(1,0)])['maximum_supported_level'],1)
        self.assertEqual(topic_evidence.performance([row(4,0,None)])['maximum_supported_level'],0)
        industrial=[row(4,0),row(4,0),row(3,1),row(3,1),row(4,1),row(4,0)]
        self.assertEqual(topic_evidence.performance(industrial)['maximum_supported_level'],1)

    def test_saved_question_views_and_topic_summary(self):
        preparation_tests.PreparationTests().session('evidence-view')
        payload=json.dumps(dict(question='A source question?',competency_id='T0',competency='Topic 0',bloom_level=2,bloom_name='Understand',options=['A','B','C','D'],correct_answer='A',sources=[{'page':3}]))
        with app.db() as c:
            c.execute('INSERT INTO assessment_items(id,session_id,position,payload,answer,correct,issued,answered) VALUES(?,?,?,?,?,?,?,?)',('evidence-q','evidence-view',1,payload,0,1,time.time(),time.time()))
            row=c.execute('SELECT * FROM questions WHERE id=?',('evidence-q',)).fetchone()
            self.assertEqual(row['bloom_name'],'Understand');self.assertEqual(row['topic_id'],'T0')
            self.assertEqual(c.execute('SELECT correct FROM user_responses WHERE question_id=?',('evidence-q',)).fetchone()[0],1)
            rows=c.execute('SELECT * FROM assessment_items WHERE session_id=?',('evidence-view',)).fetchall()
            topic_evidence.save(c,'test','evidence-view','T0',rows,{'current_level':1,'confidence':'low'})
        result=topic_evidence.for_user('test');self.assertEqual(result[0]['evidence_count'],1)

if __name__=='__main__':unittest.main(verbosity=2)
