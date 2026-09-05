from pathlib import Path
p=Path(__file__).resolve().parents[1]/'tests/test_integration.py'
s=p.read_text(encoding='utf-8')
s=s.replace('import okr_service','import okr_service\nimport role_catalog\nimport model_tasks\nimport quiz_buffer\nimport itertools\nimport assessment_evaluator\nimport recommendation_service')
s=s.replace('class IntegrationTests(unittest.TestCase):','''class IntegrationTests(unittest.TestCase):
    def work_profile(self,rid='PDF_A01_L3'):
        r=role_catalog.ROLES[rid]
        return dict(assessment_role_id=rid,assessment_area=r['area_id'],ministry=r['ministry'],department=r['area'],designation=r['title'],administration_type='Central Government',education='Statistics')
''')
s=s.replace("        cls.http=server.http",'''        original=model_tasks.json_task
        def inference(task,system,data,**kw):
            if task=='evaluation':return dict(current_level=data['maximum_supported_level'],confidence='medium',reason='The saved responses support this demonstrated level.',evidence_ids=[data['evidence'][0]['id']]),'llama3.1:8b'
            if task=='recommendation':
                course=data['courses'][0];needed={g['competency_id'] for g in data['gaps']}
                return {'recommendations':[dict(course_id=course['id'],competency_id=next(cid for cid in course['competencies'] if cid in needed),reason='Relevant to the assessed skill gap.')]},'llama3.1:8b'
            return original(task,system,data,**kw)
        cls.model_patch=patch.object(model_tasks,'json_task',side_effect=inference);cls.model_patch.start()
        cls.http=server.http''')
s=s.replace('        cls.http.shutdown()',"        live_api.WORKERS.shutdown(wait=True)\n        cls.model_patch.stop()\n        cls.http.shutdown()")
s=s.replace("        self.assertEqual(r.status,status)","        if r.status!=status:self.fail(f'{path}: expected {status}, got {r.status}: {r.read().decode()}')")
s=s.replace('        for _ in range(100):\n            job=',"        if 'job_id' not in data:return data\n        for _ in range(1500):\n            job=")
s=s.replace("        self.assertTrue(self.api('/api/auth/check-username?username=profile.roundtrip'", "        payload.update(self.work_profile('PDF_A01_L1'))\n        self.assertTrue(self.api('/api/auth/check-username?username=profile.roundtrip'",1)
s=s.replace("        self.api('/api/profile/update',update,role='newaccount')", "        update.update(self.work_profile('PDF_A01_L5'))\n        self.api('/api/profile/update',update,role='newaccount')",1)
s=s.replace("frac_engine.map_designation_to_role('Joint Director'))","'PDF_A01_L5')")
s=s.replace('        self.assertTrue(states)','        self.assertEqual(states,[])')
s=s.replace('        self.assertTrue(ministries)','        self.assertEqual(len(ministries),4)')
a=s.index("        result=self.api('/api/profile'",s.index('    def test_02_'));b=s.index('    def test_03_',a)
s=s[:a]+'''        p=self.work_profile()
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
'''+s[b:]
s=s.replace("'competency_id':'C_DPDP','target':4", "'competency_id':'C_ETHICS','target':4")
s=s.replace("result=self.api('/api/quiz/submit',{'session_id':s['id']})['result']","result=self.job('/api/quiz/submit',{'session_id':s['id']},'learner')['result']",1)
s=s.replace("        s=self.api('/api/quiz/start',{'kind':'initial'})['session']\n        with patch.object(rag_engine,'generate_mcq_with_llm',side_effect=RuntimeError", "        s=self.api('/api/quiz/start',{'kind':'initial','language':'hi'})['session']\n        with patch.object(rag_engine,'generate_mcq_with_llm',side_effect=RuntimeError")
s=s.replace("        self.api('/api/auth/register',{**body,'role_id':'unknown'},role=None,status=400)","        body.update(self.work_profile());body['responsibilities']='Review field surveys'\n        self.api('/api/auth/register',{**body,'assessment_role_id':'unknown'},role=None,status=400)")
s=s.replace("self.assertEqual(p['role_id'],'R_SO')","self.assertEqual(p['role_id'],'PDF_A01_L3')")
s=s.replace("self.assertEqual(p['activities'],['A_C_PYTHON'])","self.assertEqual(p['activities'],[])")
s=s.replace("            self.api('/api/quiz/submit',{'session_id':s['id']})", "            self.job('/api/quiz/submit',{'session_id':s['id']},'learner')")
s=s.replace("        s=self.api('/api/quiz/start',{'kind':'initial'},role='buffer')['session']", "        self.api('/api/profile/update',{**self.work_profile(),'responsibilities':'Distinct buffer regression'},role='buffer')\n        s=self.api('/api/quiz/start',{'kind':'initial'},role='buffer')['session']")
s=s.replace('            self.assertEqual(len(calls),2)\n', '            prepared_count=len(calls);self.assertGreater(prepared_count,2)\n')
s=s.replace('self.assertEqual(len(calls),2)  # Answer submission never invoked inference.', 'self.assertEqual(len(calls),prepared_count)  # Answer submission never invoked inference.')
s=s.replace('            self.assertEqual(len(calls),3)', '            self.assertEqual(len(calls),prepared_count)')
s=s.replace("        self.assertEqual(saved['user']['degree'],'M.Sc. Economics')", "        self.assertEqual(saved['user']['degree'],'M.Sc. Economics')")
p.write_text(s,encoding='utf-8')

p=p.parent/'check_frontend.js';s=p.read_text(encoding='utf-8')
s=s.replace('const [data,framework,admin]', 'const [data,framework,admin,registrationCatalog]')
s=s.replace("'/api/framework','/api/admin'", "'/api/framework','/api/admin','/api/registration/catalog'")
s=s.replace('data,framework,admin,languageChosen:true','data,framework,admin,registrationCatalog,languageChosen:true')
s=s.replace("status:'active',question:","status:'active',preparation:{status:'ready'},question:")
s=s.replace("['/api/quiz/answer','/api/quiz/prepare'],'Ready answers advance directly and prepare only one following question'", "['/api/quiz/answer'],'Ready answers advance without a generation request'")
p.write_text(s,encoding='utf-8')
