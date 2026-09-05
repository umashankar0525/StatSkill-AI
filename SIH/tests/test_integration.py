"""End-to-end HTTP regressions against an isolated DB; deterministic model boundary."""
import base64
import json
import os
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch
from contextlib import contextmanager

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
TEMP=tempfile.TemporaryDirectory()
os.environ['STATSKILL_DB']=str(Path(TEMP.name)/'test.db')
os.environ['STATSKILL_USERS']=str(Path(TEMP.name)/'users.json')
os.environ['STATSKILL_UPLOADS']=str(Path(TEMP.name)/'uploads')
import server
import live_api
import quiz_service
import frac_engine
import rag_engine
import okr_service
import role_catalog
import model_tasks
import quiz_buffer
import itertools
import assessment_evaluator
import recommendation_service
from storage import db,encode

class IntegrationTests(unittest.TestCase):
    def work_profile(self,rid='PDF_A01_L3'):
        r=role_catalog.ROLES[rid]
        return dict(assessment_role_id=rid,assessment_area=r['area_id'],ministry=r['ministry'],department=r['area'],designation=r['title'],administration_type='Central Government',education='Statistics')

    @contextmanager
    def mock_generator(self,fn):
        def batch(context,competency,bloom,role,profile=None,previous=(),count=2):
            return [fn(context,competency,bloom,role,profile,previous) for _ in range(count)]
        with patch.object(rag_engine,'generate_mcq_with_llm',side_effect=fn),patch.object(rag_engine,'generate_mcqs_with_llm',side_effect=batch):yield
    @classmethod
    def setUpClass(cls):
        original=model_tasks.json_task
        def inference(task,system,data,**kw):
            if task=='evaluation':return dict(current_level=data['maximum_supported_level'],confidence='medium',reason='The saved responses support this demonstrated level.',evidence_ids=[data['evidence'][0]['id']]),'llama3.1:8b'
            if task=='recommendation':
                course=data['courses'][0];needed={g['competency_id'] for g in data['gaps']}
                return {'recommendations':[dict(course_id=course['id'],competency_id=next(cid for cid in course['competencies'] if cid in needed),reason='Relevant to the assessed skill gap.')]},'llama3.1:8b'
            return original(task,system,data,**kw)
        cls.source_patch=patch.object(quiz_buffer,'assigned_sources',return_value=[dict(doc_id='fixture',text='Fixture study source for model-isolated tests.',score=0,page=1)]);cls.source_patch.start()
        cls.model_patch=patch.object(model_tasks,'json_task',side_effect=inference);cls.model_patch.start()
        cls.http=server.http.server.ThreadingHTTPServer(('127.0.0.1',0),server.StatSkillHandler)
        server.StatSkillHandler.log_message=lambda *args: None
        cls.thread=threading.Thread(target=cls.http.serve_forever,daemon=True)
        cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.http.server_port}'
        cls.tokens={}
        with db() as c:
            for role in ('learner','trainer','admin'):
                hashed,salt=server.hash_password('TestPassword123')
                row=c.execute('INSERT INTO users(name,email,password_hash,salt,role,designation,department) VALUES(?,?,?,?,?,?,?)',
                              (role,role+'@test.invalid',hashed,salt,role,'Statistical Officer','Test statistics'))
                cls.tokens[role]=(role+'-test-token',row.lastrowid)
        for role,(token,_) in cls.tokens.items():
            live_api.bind_session(token,{'email':role+'@test.invalid'})
    @classmethod
    def tearDownClass(cls):
        live_api.WORKERS.shutdown(wait=True)
        cls.model_patch.stop()
        cls.source_patch.stop()
        cls.http.shutdown()
        cls.http.server_close()
    def api(self,path,body=None,role='learner',status=200):
        headers={'Content-Type':'application/json'}
        if role:
            headers['Authorization']='Bearer '+self.tokens[role][0]
        req=urllib.request.Request(self.base+path,data=None if body is None else json.dumps(body).encode(),headers=headers)
        try:
            r=urllib.request.urlopen(req,timeout=10)
        except urllib.error.HTTPError as e:
            r=e
        if r.status!=status:self.fail(f'{path}: expected {status}, got {r.status}: {r.read().decode()}')
        return json.load(r)
    def job(self,path,body,role='trainer'):
        data=self.api(path,body,role)
        if 'session' in data:
            return data['session']
        if 'job_id' not in data:return {k:v for k,v in data.items() if k!='success'}
        for _ in range(1500):
            job=self.api('/api/jobs/'+data['job_id'],role=role)['job']
            if job['status']=='failed':
                self.fail(job['error'])
            if job['status']=='complete':
                return job['result']
            time.sleep(.02)
        self.fail('Job did not complete')
    def test_01_access_and_empty_evidence(self):
        self.api('/api/overview',role=None,status=401)
        self.api('/api/documents/upload',{},status=403)
        self.api('/api/admin/role',{},status=403)
        self.assertIsNone(self.api('/api/overview')['overall_score'])
        self.assertEqual(self.api('/api/overview')['history'],[])
        self.api('/api/assessments/submit',{'score':100,'responses':[]},status=400)
        self.assertFalse(frac_engine.get_user_competency_profile(str(self.tokens['learner'][1])))
    def test_username_registration_and_full_profile(self):
        from PIL import Image
        import io
        image=io.BytesIO();Image.new('RGB',(8,8),'blue').save(image,format='PNG')
        payload=dict(username='profile.roundtrip',password='AccountTest123',confirm_password='AccountTest123',
          full_name='Account Test',government_id='TEST-42',age=30,experience=0,
          administration_type='Central Government',ministry='MoSPI',department='Survey Division',
          designation='Junior Statistical Officer (JSO)',education='M.Sc. Statistics',projects='Household survey',
          profile_picture='data:image/png;base64,'+base64.b64encode(image.getvalue()).decode(),role='superadmin')
        payload.update(self.work_profile('PDF_A01_L1'))
        self.assertTrue(self.api('/api/auth/check-username?username=profile.roundtrip',role=None)['available'])
        registered=self.api('/api/auth/register-username',payload,role=None)
        self.assertEqual(registered['user']['role'],'learner')
        self.tokens['newaccount']=(registered['token'],registered['user']['id'])
        self.assertFalse(self.api('/api/auth/check-username?username=PROFILE.ROUNDTRIP',role=None)['available'])
        self.api('/api/auth/register-username',{**payload,'username':'PROFILE.ROUNDTRIP'},role=None,status=400)
        self.api('/api/auth/login',{'username':'profile.roundtrip','password':'wrong'},role=None,status=401)
        signed_in=self.api('/api/auth/login',{'username':'PROFILE.ROUNDTRIP','password':'AccountTest123'},role=None)
        self.assertEqual(signed_in['user']['id'],registered['user']['id'])
        current=self.api('/api/overview',role='newaccount')['user']
        self.assertEqual(current['experience'],0)
        self.assertEqual(current['government_id'],'TEST-42')
        self.assertTrue(current['profile_picture'].startswith('data:image/jpeg;base64,'))
        update=dict(name='Account Test',ministry='MoSPI',department='Survey Division',designation='Joint Director',
          degree='M.Sc. Economics',experienceYears='0',currentAssignment='Survey planning',location='New Delhi',
          specialization='Sampling',previousRoles='JSO',statisticalDomains='Sampling, Survey Design',
          projectsHandled='Population survey',technicalQualifications='Python, R',trainingProgrammes='NSSTA',role='admin',id=self.tokens['admin'][1])
        update.update(self.work_profile('PDF_A01_L5'))
        update.pop('education')
        self.api('/api/profile/update',update,role='newaccount')
        saved=self.api('/api/overview',role='newaccount')
        self.assertEqual(saved['user']['role'],'learner')
        self.assertEqual(saved['user']['location'],'New Delhi')
        self.assertEqual(saved['user']['projectsHandled'],'Population survey')
        self.assertEqual(saved['user']['degree'],'M.Sc. Economics')
        self.assertEqual(saved['user']['trainingProgrammes'],'NSSTA')
        self.assertEqual(saved['profile']['role_id'],'PDF_A01_L5')
        self.assertEqual(saved['user']['profile_picture'],current['profile_picture'])
        self.api('/api/profile/update',update,role=None,status=401)
        self.api('/api/auth/register-username',{**payload,'username':'invalid.photo','profile_picture':'data:image/svg+xml;base64,PHN2Zz4='},role=None,status=400)
        self.assertTrue(self.api('/api/auth/check-username?username=invalid.photo',role=None)['available'])

    def test_organization_seeds_and_user_directory_permissions(self):
        states = self.api('/api/states', role=None)
        ministries = self.api('/api/ministries/central', role=None)
        self.assertIsInstance(states, list)
        self.assertEqual(states,[])
        self.assertIsInstance(ministries, list)
        self.assertEqual(len(ministries),4)
        self.api('/api/users', role=None, status=401)
        self.api('/api/users', role='learner', status=403)
        self.assertIn('users', self.api('/api/users', role='admin'))
    def test_02_profile_role_activity_mapping(self):
        p=self.work_profile()
        result=self.api('/api/profile',dict(p,activities=['A_C_GIS'],experience_years=3))
        self.assertEqual(result['profile']['activities'],[])
        gaps={g['competency_id']:g['required_level'] for g in self.api('/api/overview')['gaps']}
        self.assertEqual(gaps['C_PYTHON'],2)
        self.assertEqual(gaps['C_SURVEY'],3)
        self.assertNotIn('C_GIS',gaps)
        self.api('/api/profile/update',dict(p,ministry='Ministry of Finance'),status=400)
        self.api('/api/profile/update',dict(p,assessment_area='A07'),status=400)
        self.api('/api/profile/update',dict(p,department='Not a work area'),status=400)
        self.assertEqual(self.api('/api/overview')['profile']['role_id'],p['assessment_role_id'])
    def test_03_full_adaptation_scoring_okr_and_idempotency(self):
        self.api('/api/okrs',{'title':'Improve survey skill','due_date':'2099-12-31','key_results':[{'title':'Reach level four','metric':'competency','competency_id':'C_ETHICS','target':4}]})
        s=self.api('/api/quiz/start',{'kind':'initial'})['session']
        self.assertTrue(30<=s['target']<=50)
        self.assertEqual(s['id'],self.api('/api/quiz/start',{'kind':'initial'})['session']['id'])
        self.api('/api/quiz/'+s['id'],role='trainer',status=400)
        counter=[0]
        def generate(*args,**kwargs):
            counter[0]+=1
            self.assertEqual(args[4]['education'],'Statistics')
            return {'question':f'Test question number {counter[0]} about {args[1]}?', 'options':['A','B','C','D'],'correct_answer':'B','explanation':'Test evidence'}
        blooms=[]
        with self.mock_generator(generate):
            for i in range(s['target']):
                s=self.job('/api/quiz/next',{'session_id':s['id']},'learner')
                q=s['question'];blooms.append(q['bloom_level'])
                self.assertNotIn('correct_answer',q)
                self.assertNotIn('explanation',q)
                body={'session_id':s['id'],'question_id':q['id'],'answer':1 if i%3!=1 else 0}
                s=self.api('/api/quiz/answer',body)['session']
                self.api('/api/quiz/answer',body)
        self.assertEqual(blooms[:4],[3,3,4,2])
        result=self.job('/api/quiz/submit',{'session_id':s['id']},'learner')['result']
        self.assertEqual(result['total'],s['target'])
        self.assertGreater(result['score_percent'],0)
        self.assertLess(result['score_percent'],100)
        self.assertEqual(len(result['changes']),len(self.api('/api/overview')['gaps']))
        history=len(self.api('/api/overview')['history'])
        self.assertEqual(result,self.api('/api/quiz/submit',{'session_id':s['id']})['result'])
        self.assertEqual(history,len(self.api('/api/overview')['history']))
        self.assertGreater(self.api('/api/okrs')['objectives'][0]['progress'],0)
        live_api.storage.init()
        self.assertEqual(history,len(self.api('/api/overview')['history']))
    def test_04_failed_generation_never_invents_a_question(self):
        s=self.api('/api/quiz/start',{'kind':'initial','language':'hi'})['session']
        with patch.object(rag_engine,'generate_mcqs_with_llm',side_effect=RuntimeError('Ollama unavailable')),patch('generation_runtime.time.sleep'):
            data=self.api('/api/quiz/next',{'session_id':s['id']})
            for _ in range(100):
                j=self.api('/api/jobs/'+data['job_id'])['job']
                if j['status']=='failed':break
                time.sleep(.01)
        self.assertEqual(j['status'],'failed')
        self.assertIsNone(self.api('/api/quiz/'+s['id'])['session']['question'])
    def test_05_okr_checkins_permissions(self):
        oid=self.api('/api/okrs',{'title':'Improve field delivery','due_date':'2099-12-31','key_results':[{'title':'Review ten field reports','metric':'manual','baseline':2,'target':10}]})['objective_id']
        o=next(o for o in self.api('/api/okrs')['objectives'] if o['id']==oid)
        kid=o['key_results'][0]['id']
        self.api('/api/okrs/checkin',{'key_result_id':kid,'value':6,'note':'Reviewed six signed reports'})
        o=next(o for o in self.api('/api/okrs')['objectives'] if o['id']==oid)
        self.assertEqual(o['progress'],50)
        self.assertEqual(len(o['key_results'][0]['checkins']),1)
        self.api('/api/okrs/checkin',{'key_result_id':kid,'value':10,'note':'Forged'},role='trainer',status=400)
        self.api('/api/okrs/status',{'objective_id':oid,'status':'archived'})
    def test_06_registration_persistence_and_auth(self):
        # Exercise registration without dispatching any external email or SMS.
        email='new-officer@test.invalid'
        server.VERIFIED_EMAILS.add(email)
        body={'email':email,'name':'New Officer','password':'TestPassword123','designation':'Statistical Officer','department':'Survey','ministry':'MoSPI','role_id':'R_SO','activities':['A_C_PYTHON'],'responsibilities':'Review field surveys','experience_years':'4','language':'hi'}
        body.update(self.work_profile());body['responsibilities']='Review field surveys'
        self.api('/api/auth/register',{**body,'assessment_role_id':'unknown'},role=None,status=400)
        result=self.api('/api/auth/register',body,role=None)
        self.assertIsInstance(result['user']['id'],int)
        self.assertEqual(result['role'],'learner')
        self.assertEqual(result['user']['email'],email)
        self.api('/api/auth/login',{'email':email,'password':'wrong'},role=None,status=401)
        login=self.api('/api/auth/login',{'email':email,'password':'TestPassword123'},role=None)
        self.assertEqual(result['user']['id'],login['user']['id'])
        with db() as c:
            p=json.loads(c.execute('SELECT data FROM learner_profiles WHERE user_id=?',(str(result['user']['id']),)).fetchone()['data'])
        self.assertEqual(p['role_id'],'PDF_A01_L3')
        self.assertEqual(p['activities'],[])
        self.assertEqual(p['responsibilities'],'Review field surveys')
        self.assertEqual(p['language'],'hi')

    def test_07_document_course_review_and_completion(self):
        import numpy as np
        class Encoder:
            def encode(self,texts,**kwargs):
                vector=[0.1]*384
                return np.array([vector for _ in texts] if isinstance(texts,list) else vector)
        content='Stratified sampling draws a sample from each non-overlapping stratum. This improves precision when units within each stratum are similar.'
        with patch.object(rag_engine,'get_embedder',return_value=Encoder()),patch.object(quiz_buffer,'assigned_sources',side_effect=lambda comp,p,doc_id:rag_engine.retrieve_context(comp['name'],doc_id=doc_id)):
            doc=self.job('/api/documents/upload',{'title':'Sampling material','filename':'../../sample.txt','content':base64.b64encode(content.encode()).decode()})['doc_id']
            self.assertEqual(self.api('/api/documents/'+doc)['chunks'][0]['page_num'],1)
            # A second document must never leak into a course-specific search.
            self.job('/api/documents/upload',{'title':'Other material','filename':'other.txt','content':base64.b64encode(b'Completely unrelated accounting handbook.').decode()})
            self.assertTrue(all(x['doc_id']==doc for x in rag_engine.retrieve_context('accounting',doc_id=doc)))
            course=self.api('/api/courses',{'title':'Survey sampling','description':'Learn stratification','doc_id':doc,'competency_id':'C_SAMPLING'},role='trainer')['course_id']
            self.api('/api/quiz/start',{'kind':'course','course_id':course},status=400)
            self.api('/api/courses/enrol',{'course_id':course})
            self.api('/api/courses/enrol',{'course_id':course})
            self.assertEqual(len(self.api('/api/learning-path')['courses']),1)
            s=self.api('/api/quiz/start',{'kind':'course','course_id':course})['session']
            counter=[0]
            def generate(*args,**kwargs):
                self.assertIn('Stratified sampling',args[0])
                counter[0]+=1
                return {'question':f'Course sampling question {counter[0]}?', 'options':['A','B','C','D'],'correct_answer':'A','explanation':'Grounded answer','source_quote':'Stratified sampling draws a sample from each non-overlapping stratum.'}
            with self.mock_generator(generate):
                draft=self.job('/api/ai/generate-questions',{'doc_id':doc,'competency_id':'C_SAMPLING'})
                self.api('/api/questions/review',{'question_id':draft['question_id'],'status':'approved'},role='trainer')
                for _ in range(s['target']):
                    s=self.job('/api/quiz/next',{'session_id':s['id']},'learner')
                    self.assertEqual(s['question']['sources'][0]['doc_id'],doc)
                    s=self.api('/api/quiz/answer',{'session_id':s['id'],'question_id':s['question']['id'],'answer':0})['session']
            self.job('/api/quiz/submit',{'session_id':s['id']},'learner')
            self.assertEqual(self.api('/api/learning-path')['courses'][0]['enrolment_status'],'completed')
            self.assertEqual(self.api('/api/overview',role='trainer')['question_bank'][0]['status'],'approved')

    def test_08_timeout_and_invalid_model_output(self):
        s=self.api('/api/quiz/start',{'kind':'initial'})['session']
        q={'question':'Timeout test question?', 'options':['A','B','C','D'],'correct_answer':'A','explanation':'Test','competency_id':'C_SURVEY','bloom_level':3}
        with self.mock_generator(lambda *a,**kw:dict(q,question='Timeout test '+str(time.time_ns())+'?')):
            s=self.job('/api/quiz/next',{'session_id':s['id']},'learner')
        with db() as c:
            c.execute('UPDATE assessment_items SET issued=? WHERE id=?',(time.time()-181,s['question']['id']))
        self.api('/api/quiz/answer',{'session_id':s['id'],'question_id':s['question']['id'],'answer':0})
        with db() as c:
            row=c.execute('SELECT answer,correct FROM assessment_items WHERE id=?',(s['question']['id'],)).fetchone()
        self.assertIsNone(row['answer']);self.assertEqual(row['correct'],0)
        with patch.object(rag_engine,'chat',return_value='{"question":"bad question"}'):
            with self.assertRaises(ValueError):
                rag_engine.generate_mcq_with_llm('NONE','Sampling','Apply','Officer')

    def test_09_preparation_uses_previous_previous_answer_and_does_not_issue_early(self):
        with db() as c:
            uid=c.execute("INSERT INTO users(name,email,role,designation,department) VALUES('Buffer test','buffer@test.invalid','learner','Statistical Officer','Survey')").lastrowid
        self.tokens['buffer']=('buffer-test-token',uid)
        live_api.bind_session('buffer-test-token',{'email':'buffer@test.invalid'})
        self.api('/api/profile/update',{**self.work_profile(),'responsibilities':'Distinct buffer regression'},role='buffer')
        s=self.api('/api/quiz/start',{'kind':'initial','language':'hi'},role='buffer')['session']
        calls=[]
        def generate(*args,**kwargs):
            calls.append(args[2])
            return {'question':f'Buffered survey question number {len(calls)}?', 'options':['A','B','C','D'],'correct_answer':'A','explanation':'Valid saved explanation'}
        with self.mock_generator(generate):
            s=self.job('/api/quiz/next',{'session_id':s['id']},'buffer')
            first=s['question']
            self.assertEqual(self.job('/api/quiz/prepare',{'session_id':s['id']},'buffer'),{})
            self.job('/api/quiz/prepare',{'session_id':s['id']},'buffer')
            prepared_count=len(calls);self.assertEqual(prepared_count,2)
            unchanged=self.api('/api/quiz/'+s['id'],role='buffer')['session']
            self.assertEqual(unchanged['question']['id'],first['id'])
            self.assertEqual(unchanged['question']['deadline'],first['deadline'])
            with db() as c:
                self.assertEqual(c.execute('SELECT count(*) FROM assessment_items WHERE session_id=?',(s['id'],)).fetchone()[0],1)
            started=time.perf_counter()
            s=self.api('/api/quiz/answer',{'session_id':s['id'],'question_id':first['id'],'answer':1},role='buffer')['session']
            self.assertLess(time.perf_counter()-started,1,'Prepared question handoff must stay below one second locally.')
            self.assertEqual(s['question']['position'],2)
            self.assertEqual(s['question']['bloom_level'],3)
            self.assertEqual(len(calls),prepared_count)  # Q2 was in the opening pair.
            self.job('/api/quiz/prepare',{'session_id':s['id']},'buffer')
            self.assertEqual(len(calls),prepared_count+3)  # Three Q3 alternatives are generated while Q2 is displayed.
            s=self.api('/api/quiz/answer',{'session_id':s['id'],'question_id':s['question']['id'],'answer':0},role='buffer')['session']
            self.assertEqual(s['question']['position'],3)
            self.assertEqual(s['question']['bloom_level'],2)  # Q1 was wrong; Q2 was right.
            self.assertEqual(len(calls),prepared_count+3)
            self.assertNotIn('correct_answer',s['question'])
            self.assertGreater(s['question']['deadline'],time.time()+178)
        self.api('/api/quiz/prepare',{'session_id':s['id']},role='trainer',status=400)

if __name__=='__main__':
    unittest.main(verbosity=2)
