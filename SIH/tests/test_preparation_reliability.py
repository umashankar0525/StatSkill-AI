import json,time,unittest,urllib.error
from unittest.mock import patch
import test_integration as app
import generation_runtime as runtime
import soul_quiz_engine as generator

class PreparationTests(unittest.TestCase):
    def session(self,sid,target=4,topics=1):
        comps=[dict(id='T'+str(i),name='Topic '+str(i),required_level=1) for i in range(topics)]
        p=dict(role_id='TEST_'+sid,assessment_role_id='TEST_'+sid,designation='Officer',language='en')
        with app.db() as c:c.execute('INSERT INTO assessments(id,user_id,kind,profile,competencies,target,created) VALUES(?,?,?,?,?,?,?)',(sid,'test','initial',json.dumps(p),json.dumps(comps),target,time.time()))
        return {'id':'test'}
    def test_progress_counts_assessment_slots(self):
        self.session('count',32,8)
        with app.db() as c:
            c.execute('INSERT INTO assessment_buffers VALUES(?,?,?,?,?,?)',('count','rolling-v1','preparing',32,2,None))
            c.execute('INSERT INTO question_drafts VALUES(?,?,?,?)',('count',1,1,'{}'))
            c.execute('INSERT INTO question_drafts VALUES(?,?,?,?)',('count',2,1,'{}'))
        state=app.quiz_buffer.status('count')
        self.assertEqual(state['total'],32);self.assertEqual(state['ready'],2)
    def test_transient_retries_and_warm_cache(self):
        user=self.session('retry');attempts=[]
        def batch(*args):
            attempts.append(args)
            if len(attempts)<3:raise TimeoutError('Test timeout')
            return [dict(question=f'Unique question {len(attempts)} number {i}?',options=['A','B','C','D'],correct_answer='A',explanation='Valid') for i in range(args[-1])]
        with patch.object(app.quiz_buffer,'assigned_sources',return_value=[dict(text='Relevant study text for this topic.',score=0,doc_id='test')]),patch.object(app.rag_engine,'generate_mcqs_with_llm',side_effect=batch),patch.object(runtime.time,'sleep') as sleep:
            app.quiz_buffer.ensure('retry',user)
            self.assertEqual(sleep.call_count,2)
            self.assertEqual(app.quiz_buffer.status('retry')['ready'],2)
            count=len(attempts);app.quiz_buffer.ensure('retry',user);self.assertEqual(len(attempts),count)
        with app.db() as c:
            events=[json.loads(r[0]) for r in c.execute("SELECT payload FROM generation_events WHERE event='attempt_failed' AND session_id='retry'")]
        self.assertTrue(all(e['error_code']=='timeout' for e in events))
    def test_schema_and_prompt_budget(self):
        q=dict(question='Which method is supported by the supplied example?',options=['A','B','C','D'],correctAnswerIndex=0,explanation='The source defines it.',source_quote='Exact supporting source sentence.')
        with patch.object(app.model_tasks,'json_task',return_value=({'questions':[q]},'llama3.1:8b')) as model:
            generator.generate_batch('Exact supporting source sentence.\n'+'x'*10000,'Sampling','Apply','Officer',{'education':'PRIVATE'*1000},['history'*200]*100,1)
        args=model.call_args.args[2]
        self.assertEqual(len(args['source']),3600)
        self.assertEqual(len(args['avoid_question_stems']),8)
        self.assertTrue(all(len(x)<=140 for x in args['avoid_question_stems']))
        self.assertNotIn('education',args)
        self.assertIsInstance(model.call_args.kwargs['schema'],dict)

    def test_near_duplicate_paraphrases_are_rejected(self):
        q=dict(question='A company must stop production for environmental testing. Which option minimizes harm to stakeholders?',options=['Stop safely','Continue','Ignore testing','Hide results'],correctAnswerIndex=0,explanation='Testing limits harm.',source_quote='')
        previous=['A company must stop production for environmental testing. Which choice minimizes harm to affected stakeholders?']
        with self.assertRaisesRegex(runtime.GenerationError,'closely paraphrased'):
            generator.validate(q,'NONE',previous,'test',3)

    def test_duplicate_retry_remembers_rejected_stem_and_requests_alternatives(self):
        user=self.session('duplicate-reprompt',1);calls=[]
        repeated='What is the primary responsibility for maintaining metadata standards?'
        def batch(context,competency,bloom,role,profile,previous,count):
            calls.append((list(previous),count))
            if len(calls)==1:
                failure=runtime.GenerationError('duplicate','The model repeated a question.')
                failure.candidate=repeated
                raise failure
            self.assertIn(repeated,previous);self.assertEqual(count,3)
            return [dict(question=f'Unique metadata scenario {i} requires which control?',options=['A','B','C','D'],correct_answer='A',explanation='Valid') for i in range(count)]
        with patch.object(app.quiz_buffer,'assigned_sources',return_value=[]),patch.object(app.rag_engine,'generate_mcqs_with_llm',side_effect=batch),patch.object(runtime.time,'sleep') as sleep:
            app.quiz_buffer.ensure('duplicate-reprompt',user)
        self.assertEqual(len(calls),2);sleep.assert_not_called()
        self.assertEqual(app.quiz_buffer.status('duplicate-reprompt')['status'],'ready')

    def test_invalid_source_quote_falls_back_to_general_knowledge(self):
        user=self.session('quote-fallback',2)
        contexts=[]
        def batch(context,*args):
            contexts.append(context)
            if context!='NONE':
                raise runtime.GenerationError('quotation_missing','Supporting quotation does not match the study material.',False)
            return [dict(question=f'General fallback question {i}?',options=['A','B','C','D'],correct_answer='A',explanation='Established topic knowledge') for i in range(args[-1])]
        with patch.object(app.quiz_buffer,'assigned_sources',return_value=[dict(text='Relevant source text.',doc_id='fixture')]),patch.object(app.rag_engine,'generate_mcqs_with_llm',side_effect=batch),patch.object(runtime.time,'sleep'):
            app.quiz_buffer.ensure('quote-fallback',user)
        self.assertEqual(contexts.count('NONE'),1)
        self.assertEqual(len(contexts),2)
        with app.db() as c:values=[json.loads(r[0]) for r in c.execute('SELECT payload FROM question_drafts WHERE session_id=?',('quote-fallback',))]
        self.assertEqual(len(values),2)
        self.assertTrue(all(q['grounding']=='model knowledge' for q in values))
    def test_rejects_heading_and_unanswered_source_question(self):
        q=dict(question='What is the focus of the communication course?',options=['A','B','C','D'],correctAnswerIndex=0,explanation='Explanation',source_quote='The study course teaches effective communication.')
        with self.assertRaisesRegex(ValueError,'metadata'):generator.validate(q,q['source_quote'],[],'test',1)
        q.update(question='What happens when communication fails?',source_quote='What is the result of ineffective communication?')
        with self.assertRaisesRegex(runtime.GenerationError,'answer-supporting'):generator.validate(q,q['source_quote'],[],'test',1)
    def test_http_classification(self):
        with urllib.error.HTTPError('http://localhost',429,'limited',{'Retry-After':'3'},None) as err:
            failure=runtime.classify(err)
            self.assertTrue(failure.retryable);self.assertEqual(failure.retry_after,3)
        with urllib.error.HTTPError('http://localhost',404,'missing',{},None) as err:
            self.assertFalse(runtime.classify(err).retryable)

    def test_resume_retains_valid_saved_candidates(self):
        user=self.session('resume-partial');calls=[]
        def batch(*args):
            calls.append(args)
            if len(calls)==1:
                return [dict(question='One valid resumable question?',options=['A','B','C','D'],correct_answer='A',explanation='Source evidence')]
            if len(calls)==2:raise runtime.GenerationError('model_missing','Model unavailable',False)
            return [dict(question=f'Resumable question batch {len(calls)} item {i}?',options=['A','B','C','D'],correct_answer='A',explanation='Source evidence') for i in range(args[-1])]
        with patch.object(app.quiz_buffer,'assigned_sources',return_value=[dict(text='A relevant source.',doc_id='fixture')]),patch.object(app.rag_engine,'generate_mcqs_with_llm',side_effect=batch):
            with self.assertRaisesRegex(runtime.GenerationError,'Model unavailable'):app.quiz_buffer.ensure('resume-partial',user)
            with app.db() as c:
                saved=[r[0] for r in c.execute('SELECT payload FROM question_drafts WHERE session_id=?',('resume-partial',))]
            self.assertEqual(len(saved),1)
            app.quiz_buffer.ensure('resume-partial',user)
            self.assertEqual(app.quiz_buffer.status('resume-partial')['ready'],2)
            with app.db() as c:
                complete=[r[0] for r in c.execute('SELECT payload FROM question_drafts WHERE session_id=?',('resume-partial',))]
            self.assertEqual(len(complete),2);self.assertTrue(set(saved)<=set(complete))
            self.assertEqual(len(calls),3)

if __name__=='__main__':unittest.main(verbosity=2)
