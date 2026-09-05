"""Bounded, source-grounded question batches adapted from SOUL prompts."""
import difflib,re,secrets
import model_tasks
import generation_runtime as runtime

RULES='''Write substantive MCQs for the supplied role, topic and Bloom level.
Use only the supplied study text. Test concepts and decisions, never document headings or metadata.
Each question must test a DIFFERENT point or scenario, including across difficulty levels.
Questions listed in avoid_question_stems have already been used. Choose a different concept; paraphrasing one also counts as repetition.
Use exactly four distinct plausible options and one correctAnswerIndex (0–3).
Keep each question under 40 words, each option under 12 words and explanation under 25 words.
Copy one SHORT exact supporting sentence into source_quote (under 35 words).
The quotation must state the fact supporting the answer, not a heading, an unanswered question or a broken fragment.
Do not invent facts, references or unsupported scenarios. Do not use all/none of the above.
Follow the language requested; leave source_quote in its original language.
Return {"questions":[{"question":"...","options":["...","...","...","..."],
"correctAnswerIndex":0,"explanation":"...","source_quote":"..."}]}.
The requested focus and question forms should vary the task, not introduce facts absent from the source.'''
GENERAL_RULES='''Write substantive MCQs for the supplied role, topic and Bloom level.
Use established general knowledge of the topic. Test concepts and realistic decisions, never document metadata.
Each question must test a DIFFERENT point or scenario, including across difficulty levels.
Stay directly within the named competency. Do not substitute unrelated duties from the role profile.
Questions listed in avoid_question_stems have already been used. Choose a different concept; paraphrasing one also counts as repetition.
Use exactly four distinct plausible options and one correctAnswerIndex (0–3).
Keep each question under 40 words, each option under 12 words and explanation under 25 words.
Set source_quote to an empty string because no study passage is being cited.
Do not invent publications or references. Do not use all/none of the above.
Follow the requested language and return the requested JSON object only.'''
FORMS=['identify the defining concept','distinguish two related concepts','choose the correct procedure','identify an error and its consequence','interpret a practical example','compare two justified choices','select a sound plan','explain a cause and effect']
BOILERPLATE={'a','an','and','are','as','at','be','best','by','do','does','for','from','following','how','in','is','it','of','on','or','primary','should','the','this','to','what','when','which','with','would'}

def normalized(text):return ' '.join(re.findall(r'\w+',text.casefold()))

def is_duplicate(question,previous):
    """Catch exact repetitions and close paraphrases without rejecting shared quiz wording."""
    candidate=normalized(question)
    candidate_words=set(candidate.split())-BOILERPLATE
    for old in previous:
        existing=normalized(str(old))
        if candidate==existing:
            return str(old)
        if difflib.SequenceMatcher(None,candidate,existing,autojunk=False).ratio()>=.86:
            return str(old)
        existing_words=set(existing.split())-BOILERPLATE
        overlap=len(candidate_words & existing_words)
        if overlap>=4 and overlap/max(1,min(len(candidate_words),len(existing_words)))>=.75:
            return str(old)
    return None

def verified_quote(quote,context):
    """Return the exact source span for an exact or near-exact model quotation."""
    compact_quote=' '.join(quote.split())
    compact_context=' '.join(context.split())
    if compact_quote in compact_context:
        return compact_quote
    wanted=[m.group().casefold() for m in re.finditer(r'\w+',quote)]
    source=list(re.finditer(r'\w+',context))
    if len(wanted)<4 or not source:
        return None
    best=None
    for size in range(max(4,len(wanted)-2),min(len(source),len(wanted)+2)+1):
        for start in range(0,len(source)-size+1):
            actual=[m.group().casefold() for m in source[start:start+size]]
            score=difflib.SequenceMatcher(None,wanted,actual,autojunk=False).ratio()
            if best is None or score>best[0]:best=(score,start,size)
    if not best or best[0]<0.88:
        return None
    _,start,size=best
    return context[source[start].start():source[start+size-1].end()]

def validate(q,context,previous,model,depth):
    if not isinstance(q,dict):raise ValueError('Expected a question object.')
    options=q.get('options');index=q.get('correctAnswerIndex')
    if index is None and isinstance(options,list) and q.get('correct_answer') in options:index=options.index(q['correct_answer'])
    if not isinstance(q.get('question'),str) or not 15<=len(q['question'])<=1000:raise ValueError('Generated question has invalid text.')
    if not isinstance(options,list) or len(options)!=4 or any(not isinstance(x,str) or not x.strip() or len(x)>700 for x in options) or len({x.strip().casefold() for x in options})!=4:raise ValueError('Generated question needs four distinct options.')
    if type(index) is not int or not 0<=index<4:raise ValueError('Generated question has no valid answer key.')
    if not isinstance(q.get('explanation'),str) or not q['explanation'].strip():raise ValueError('Generated question has no explanation.')
    quote=q.get('source_quote','')
    if not isinstance(quote,str):raise ValueError('Invalid source quotation.')
    if context!='NONE':
        quote=verified_quote(quote,context)
        if not quote:raise runtime.GenerationError('quotation_missing','Supporting quotation does not match the study material.',False)
        if len(re.findall(r'\w+',quote))<4 or quote.rstrip().endswith('?'):raise runtime.GenerationError('quotation_missing','Supporting quotation must state an answer-supporting fact.',False)
    if re.search(r'\b(which excerpt|cid:|font token)\b',q['question'],re.I):raise ValueError('Question tests document formatting rather than the competency.')
    if re.search(r'\b(focus|title|author|name)\b.{0,45}\b(course|module|document|textbook)\b',q['question'],re.I):raise ValueError('Question tests course metadata rather than the competency.')
    duplicate=is_duplicate(q['question'],previous)
    if duplicate:
        failure=runtime.GenerationError('duplicate','The model repeated or closely paraphrased an earlier question.')
        failure.candidate=q['question'];failure.matches=duplicate
        raise failure
    answer=options[index];options=list(options);secrets.SystemRandom().shuffle(options)
    return dict(question=q['question'],options=options,correct_answer=answer,explanation=q['explanation'],source_quote=quote,generation_model=model,generator='soul-batch-v4',proficiency_level=depth)

def generate_batch(context,competency,bloom,role,profile=None,previous=(),count=2):
    p=profile or {};count=max(1,min(3,int(count)))
    depth={'Remember':1,'Understand':2,'Apply':3,'Analyze':4,'Evaluate':5,'Create':6}.get(bloom,3)
    clean=re.sub(r'\(cid:\d+\)','',context)[:3600]
    offset=int(p.get('_offset',0))+int(p.get('_attempt',1))-1
    prior=[str(t) for t in previous]
    data={'role':role[:120],'duties':'' if clean=='NONE' else (p.get('role_duties') or p.get('responsibilities',''))[:240],
          'competency':competency,'difficulty':depth,'bloom':bloom,'language':'Hindi' if p.get('language')=='hi' else 'English',
          'source':clean,'count':count,'question_forms':[FORMS[(offset+i)%len(FORMS)] for i in range(count)],
          'avoid_question_stems':[t[:140] for t in prior[-8:]],
          'novelty_instruction':f'Use a new {competency} concept that is absent from every avoided question. Variation {offset}.',
          'variation':offset}
    properties={'question':{'type':'string'},'options':{'type':'array','items':{'type':'string'},'minItems':4,'maxItems':4},'correctAnswerIndex':{'type':'integer','minimum':0,'maximum':3},'explanation':{'type':'string'},'source_quote':{'type':'string'}}
    schema={'type':'object','properties':{'questions':{'type':'array','minItems':count,'maxItems':count,'items':{'type':'object','properties':properties,'required':list(properties)}}},'required':['questions']}
    temperature=min(.8,.34+.08*max(0,int(p.get('_attempt',1))-1))
    value,model=model_tasks.json_task('quiz',GENERAL_RULES if clean=='NONE' else RULES,data,depth=depth,tokens=360*count+120,schema=schema,temperature_override=temperature)
    items=value.get('questions',[value]);accepted=[];last_error=None
    if not isinstance(items,list):raise ValueError('Expected a list of questions.')
    for q in items[:count]:
        try:accepted.append(validate(q,clean,list(previous)+[x['question'] for x in accepted],model,depth))
        except (ValueError,runtime.GenerationError) as exc:
            last_error=exc;runtime.event('candidate_rejected',error_code=runtime.classify(exc).code,error=str(exc))
    if not accepted:raise last_error or ValueError('The model returned no questions.')
    return accepted

def generate_mcq(context,competency,bloom,role,profile=None,previous=(),model_override=None):
    return generate_batch(context,competency,bloom,role,profile,previous,1)[0]
