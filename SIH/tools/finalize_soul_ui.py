from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'static/js/liveViews.js';s=p.read_text(encoding='utf-8')
s=s.replace('<h2>Publish a course</h2>', '''<h2>Use material for role assessments</h2><form class="live-form" onsubmit="event.preventDefault();store.save('/api/materials/assign',values(this),'Material assigned to the role.')"><div class="form-grid">${select('Material','doc_id',docs,null,'id','title')}${select('Work-area role','role_id',f.roles.filter(r=>r.id.startsWith('PDF_')),null,'id','title')}</div><button class="live-btn" ${store.state.busy?'disabled':''}>Assign material</button></form><h2>Publish a course</h2>''')
p.write_text(s,encoding='utf-8')
p=root/'static/js/components/learnerDash.js';s=p.read_text(encoding='utf-8').replace('suggestedMax: 5','suggestedMax: 6');p.write_text(s,encoding='utf-8')
p=root/'static/js/components/quizPlayer.js';s=p.read_text(encoding='utf-8').replace('${c.new_level}</td>', "${c.new_level??tr('Not assessed')}</td>");p.write_text(s,encoding='utf-8')
p=root/'static/js/components/learningPath.js';s=p.read_text(encoding='utf-8').replace('Build skills through your enrolled courses and their assessments.','Continue your saved learning. iGOT course progress is managed on iGOT.');p.write_text(s,encoding='utf-8')
