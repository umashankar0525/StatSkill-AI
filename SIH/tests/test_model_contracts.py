"""Model outputs, official source boundaries, and all reachable quiz branches."""
import json,time,unittest
from unittest.mock import patch
import test_integration as app
import generation_runtime as runtime

class ModelContracts(unittest.TestCase):
    def test_opening_buffer_is_bounded_to_two_questions(self):
        sid='bounded-opening'
        profile=dict(role_id='TEST_BOUNDED',assessment_role_id='TEST_BOUNDED',designation='Officer',language='en')
        comps=[dict(id='T_BOUND',name='Bounded topic',required_level=3)]
        with app.db() as c:c.execute('INSERT INTO assessments(id,user_id,kind,profile,competencies,target,created) VALUES(?,?,?,?,?,?,?)',(sid,'test','initial',json.dumps(profile),json.dumps(comps),30,time.time()))
        question=lambda i:dict(question=f'Bounded opening question {i}?',options=['A','B','C','D'],correct_answer='A',explanation='Valid')
        with patch.object(app.quiz_buffer,'assigned_sources',return_value=[dict(text='Bounded topic source.',doc_id='fixture')]),patch.object(app.rag_engine,'generate_mcqs_with_llm',side_effect=lambda *args:[question(i) for i in range(args[-1])]):
            app.quiz_buffer.ensure(sid,{'id':'test'})
        with app.db() as c:self.assertEqual(c.execute('SELECT count(*) FROM question_drafts WHERE session_id=?',(sid,)).fetchone()[0],2)

    def test_four_ministries_and_exact_role_requirements(self):
        c=app.role_catalog.public_catalog()
        self.assertEqual([len(m['departments']) for m in c['ministries']],[6,4,4,3])
        self.assertEqual(len(c['areas']),17)
        self.assertEqual(len(app.role_catalog.ROLES),102)
        for area in c['areas']:
            ministry=next(m for m in c['ministries'] if m['name']==area['ministry'])
            self.assertIn(area['id'],[d['id'] for d in ministry['departments']])
            for role in area['roles']:
                r=app.role_catalog.ROLES[role['id']]
                self.assertTrue(all(1<=level<=6 for level in r['requirements'].values()))
        self.assertEqual(app.role_catalog.ROLES['PDF_A01_L3']['requirements']['C_PYTHON'],2)
        self.assertNotIn('C_PYTHON',app.role_catalog.ROLES['PDF_A01_L6']['requirements'])
        self.assertEqual(len(app.role_catalog.CATALOG['competencies']),33)
        self.assertEqual(app.role_catalog.ROLES['PDF_A02_L3']['requirements']['C_NAT_ACC'],3)
        self.assertEqual(app.role_catalog.ROLES['PDF_A09_L3']['requirements']['C_GIS'],3)

    def test_evaluation_rejects_invented_levels_and_evidence(self):
        rows=[dict(id='e1',payload=json.dumps(dict(question='What does sampling measure?',options=['A','B','C','D'],correct_answer='A',bloom_level=3)),answer=0,correct=1)]
        rows.append(dict(rows[0],id='e2'))
        good=dict(current_level=3,confidence='medium',reason='One correct answer supports this depth.',evidence_ids=['e1'])
        for value in [dict(good,current_level=6),dict(good,evidence_ids=['invented'])]:
            with patch.object(app.model_tasks,'json_task',return_value=(value,'llama3.1:8b')),patch.object(runtime.time,'sleep'):
                with self.assertRaises(runtime.GenerationError):app.assessment_evaluator.evaluate('rejected','C_SAMPLING',rows)
        with patch.object(app.model_tasks,'json_task',return_value=(good,'llama3.1:8b')) as model:
            self.assertEqual(app.assessment_evaluator.evaluate('accepted','C_SAMPLING',rows)['current_level'],3)
            app.assessment_evaluator.evaluate('accepted','C_SAMPLING',rows)
            self.assertEqual(model.call_count,1)
        with patch.object(app.model_tasks,'json_task',side_effect=AssertionError('Skipped answers must not call inference')):
            result=app.assessment_evaluator.evaluate('skipped','C_SAMPLING',[dict(rows[0],answer=None,correct=0)])
            self.assertEqual(result['current_level'],0)

    def test_l0_is_assigned_without_an_llm_call(self):
        rows=[dict(id='l0-'+str(i),payload=json.dumps(dict(question='Basic question?',options=['A','B','C','D'],correct_answer='A',bloom_level=1)),answer=1,correct=0) for i in range(4)]
        with patch.object(app.model_tasks,'json_task',side_effect=AssertionError('L0 must be decided from the answer key')):
            result=app.assessment_evaluator.evaluate('l0-session','C_SQL',rows)
        self.assertEqual(result['current_level'],0)
        self.assertIn('foundational',result['reason'])

    def test_recommendation_rejects_invented_courses_and_attaches_server_links(self):
        gaps=[dict(competency_id='C_CYBER',competency_name='Cybersecurity',gap=3,current_level=1,required_level=4)]
        p=dict(role_id='PDF_A06_L4',designation='Deputy Director',department='Data Informatics, AI & Analytics')
        user={'id':'recommendation-contract'}
        def recommendation(cid):return {'recommendations':[dict(course_id=cid,competency_id='C_CYBER',reason='Develops knowledge relevant to the assessed cybersecurity gap.')]}
        with patch.object(app.model_tasks,'json_task',return_value=(recommendation('invented-course'),'llama3.1:8b')):
            with self.assertRaises(ValueError):app.recommendation_service.recommend(user,p,gaps)
        course=next(c for c in app.recommendation_service.catalog() if 'C_CYBER' in c['competencies'])
        with patch.object(app.model_tasks,'json_task',return_value=(recommendation(course['id']),'llama3.1:8b')):
            result=app.recommendation_service.recommend(user,p,gaps)
        self.assertEqual(result['recommendations'][0]['course_id'],course['id'])
        self.assertIn('portal.igotkarmayogi.gov.in/app/toc/',app.recommendation_service.courses_for(user,p,gaps)[0]['url'])

    def test_task_model_routing(self):
        with patch.object(app.rag_engine,'chat',return_value='{}') as chat:
            for task,depth,expected in [('quiz',2,'llama3.2:3b'),('quiz',5,'llama3.2:3b'),('evaluation',3,'llama3.1:8b'),('recommendation',3,'llama3.1:8b')]:
                app.model_tasks.json_task(task,'system',{},depth=depth)
                self.assertEqual(chat.call_args.kwargs['model'],expected)
                if task=='quiz':
                    self.assertEqual(chat.call_args.kwargs['context_length'],4096)
                    self.assertEqual(chat.call_args.kwargs['gpu_layers'],-1)

if __name__=='__main__':unittest.main(verbosity=2)
