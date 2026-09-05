import io,json,time,unittest
from unittest.mock import patch
import test_integration as app
import generation_runtime as runtime

class EvaluationRecoveryTests(unittest.TestCase):
    def test_default_model_calls_share_the_configured_context(self):
        requests=[]
        def respond(request,**kwargs):
            requests.append(json.loads(request.data))
            return io.BytesIO(json.dumps({'done':True,'done_reason':'stop','message':{'content':'{}'}}).encode())
        with patch.object(app.rag_engine.urllib.request,'urlopen',side_effect=respond):
            for output in [True,{'type':'object'},False]:app.rag_engine.chat([{'role':'user','content':'Test'}],output)
        self.assertEqual(len({r['options']['num_ctx'] for r in requests}),1)

    def test_http_500_retries_and_uses_schema_then_cache(self):
        rows=[dict(id='retry-evidence-'+str(i),payload=json.dumps(dict(question='Which method matches the evidence?',options=['A','B','C','D'],correct_answer='A',bloom_level=2)),answer=0,correct=1) for i in range(2)]
        value=dict(current_level=2,confidence='medium',reason='Both responses support this level.',evidence_ids=[r['id'] for r in rows])
        with patch.object(app.model_tasks,'json_task',side_effect=[runtime.GenerationError('http_500','Model temporarily unavailable'),(value,'llama3.1:8b')]) as model,patch.object(runtime.time,'sleep'):
            result=app.assessment_evaluator.evaluate('recover-model','C_SQL',rows)
            self.assertEqual(result['current_level'],2)
            self.assertEqual(model.call_count,2)
            self.assertEqual(model.call_args.kwargs['schema']['properties']['current_level']['maximum'],2)
            self.assertEqual(app.assessment_evaluator.evaluate('recover-model','C_SQL',rows),result)
            self.assertEqual(model.call_count,2)

    def test_partial_results_survive_failure_and_retry(self):
        user={'id':'evaluation-recovery'};sid='evaluation-recovery'
        comps=[dict(id=k,name=k,required_level=3) for k in ['C_SQL','C_PYTHON']]
        with app.db() as c:
            c.execute('INSERT INTO assessments(id,user_id,kind,profile,competencies,target,created) VALUES(?,?,?,?,?,?,?)',(sid,user['id'],'initial','{}',json.dumps(comps),4,time.time()))
            for i in range(4):
                q=dict(question='Which option is supported?',options=['A','B','C','D'],correct_answer='A',bloom_level=2,competency_id=comps[i//2]['id'])
                c.execute('INSERT INTO assessment_items VALUES(?,?,?,?,?,?,?,?)',(sid+str(i),sid,i+1,json.dumps(q),0,1,time.time(),time.time()))
        calls=[]
        def model(task,system,data,**kwargs):
            calls.append(data['competency'])
            if data['competency']=='C_PYTHON' and len(calls)==2:raise runtime.GenerationError('http_404','Missing model',False)
            return dict(current_level=2,confidence='medium',reason='The recorded answers support this level.',evidence_ids=[data['evidence'][0]['id']]),'llama3.1:8b'
        with patch.object(app.model_tasks,'json_task',side_effect=model):
            with self.assertRaises(runtime.GenerationError):app.quiz_service.submit(user,{'session_id':sid})
            progress=app.quiz_service.view(sid,user)['evaluation']
            self.assertEqual(progress['completed'],1);self.assertEqual(progress['status'],'failed')
            result=app.quiz_service.submit(user,{'session_id':sid})['result']
        self.assertEqual(calls,['C_SQL','C_PYTHON','C_PYTHON'])
        self.assertEqual(len(result['changes']),2)
        self.assertTrue(all(r['required_level']==3 and r['new_level']==2 for r in result['changes']))
        self.assertEqual(app.quiz_service.view(sid,user)['evaluation']['status'],'complete')
        self.assertEqual(app.quiz_service.submit(user,{'session_id':sid})['result'],result)

    def test_all_102_roles_return_every_required_topic(self):
        def model(task,system,data,**kwargs):
            return dict(current_level=data['maximum_supported_level'],confidence='medium',reason='The saved evidence supports the estimated level.',evidence_ids=[data['evidence'][0]['id']]),'llama3.1:8b'
        with patch.object(app.model_tasks,'json_task',side_effect=model):
            for rid,role in app.role_catalog.ROLES.items():
                with self.subTest(role=rid):
                    user={'id':'matrix-'+rid}
                    profile=dict(role_id=rid,assessment_role_id=rid,activities=[],designation=role['title'],language='en')
                    session=app.quiz_service.start(user,{'kind':'initial'},profile)['session'];sid=session['id'];counts={}
                    for index in range(session['target']):
                        plan=app.quiz_service.question_plan(sid,user);comp=plan['comp'];counts[comp['id']]=counts.get(comp['id'],0)+1
                        q=dict(question=f'Test evidence {rid} {index}?',options=['A','B','C','D'],correct_answer='A',bloom_level=plan['bloom'],competency_id=comp['id'])
                        with app.db() as c:c.execute('INSERT INTO assessment_items VALUES(?,?,?,?,?,?,?,?)',(sid+str(index),sid,index+1,json.dumps(q),0,1,time.time(),time.time()))
                    self.assertEqual(set(counts),set(role['requirements']))
                    self.assertLessEqual(max(counts.values())-min(counts.values()),1)
                    result=app.quiz_service.submit(user,{'session_id':sid})['result']
                    self.assertEqual({r['competency_id']:r['required_level'] for r in result['changes']},role['requirements'])
                    self.assertTrue(all(r['competency_name']!=r['competency_id'] and 1<=r['new_level']<=6 for r in result['changes']))

if __name__=='__main__':unittest.main(verbosity=2)
