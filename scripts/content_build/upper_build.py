"""Build three explicitly spiralling, original, unreviewed upper-stage libraries.

The 500 productive targets recur across adjacent stages. Examples gain narrative
context, while each story gains distinct, authored development and interpretation.
Counts describe study material, never certified CEFR mastery or frequency ranks.
"""
from __future__ import annotations
import json
from pathlib import Path
import re
import unicodedata
from collections import Counter
from upper_source import DATA, TOPICS
from upper_development import DEVELOPMENTS

ROOT = Path(__file__).resolve().parents[2]
LANGS = ('nl', 'en', 'fa')

def tri(values):
    assert len(values) == 3
    return dict(zip(LANGS, values))

def joined(sentences):
    return {lang: ' '.join(x[lang] for x in sentences) for lang in LANGS}

def blocks():
    result=[]
    for raw in DATA.strip().split('\n@'):
        lines=raw.strip().lstrip('@').splitlines()
        header=lines[0].split('|')
        assert len(header)==4, header
        rows=[]
        for line in lines[1:]:
            if not line.strip():continue
            bits=line.split('~')
            assert len(bits)==7,(header,line)
            term=bits[0].removeprefix('n') if bits[0].startswith('nde ') else bits[0]
            rows.append({'term':term,'meaning':tri(bits[1:4]),'sentence':tri(bits[4:7])})
        assert len(rows)==5,(header,len(rows))
        result.append({'topic':tri(TOPICS[header[0]]),'title':tri(header[1:]),'rows':rows})
    assert len(result)==100,len(result)
    return result

# Editorial corrections are applied to the original source records, not hidden in
# learner-facing text or counts. These replace unnecessarily narrow compounds.
FIXES={
'het vertrouwenwekkende':('de zorgvuldigheid','nauwkeurige en bedachtzame aanpak','carefulness','دقت و احتیاط',
'De zorgvuldigheid bleek doordat niemand zonder bewijs werd beschuldigd.','Carefulness was evident because nobody was accused without evidence.','دقت و احتیاط آشکار بود، چون کسی بدون دلیل متهم نشد.'),
'de volhoudbaarheid':('de duurzaamheid','mogelijkheid om iets langdurig te behouden','sustainability','پایداری',
'Na twee weken bespraken ze de duurzaamheid van de nieuwe werkafspraken.','After two weeks, they discussed the sustainability of the new working arrangements.','پس از دو هفته دربارهٔ پایداری توافق‌های کاری تازه صحبت کردند.'),
'het alternatiefprogramma':('de keuzemogelijkheid','beschikbare andere optie','choice','امکان انتخاب',
'Een extra keuzemogelijkheid liet iedereen op een passend niveau meedoen.','An additional choice allowed everyone to participate at a suitable level.','امکان انتخاب بیشتر به همه اجازه داد در سطح مناسب شرکت کنند.'),
'de beschikbaarheidsdruk':('de druk','aandrang om aan verwachtingen te voldoen','pressure','فشار',
'Door de druk om steeds bereikbaar te zijn, beantwoordde Ilse ook avondberichten.','Pressure to be constantly available made Ilse answer evening messages too.','فشار همیشه در دسترس بودن باعث می‌شد ایلسه پیام‌های عصر را هم پاسخ دهد.'),
'de herbruikbaarheidsgraad':('de uitwisseling','het onderling delen','exchange','تبادل',
'De verbeterde uitleg bevorderde de uitwisseling met andere kleine verenigingen.','The improved explanation encouraged exchange with other small associations.','توضیح بهتر تبادل با انجمن‌های کوچک دیگر را بیشتر کرد.'),
'de uitzonderingregel':('de uitzonderingsregel','regel voor bijzondere gevallen','exception rule','قاعدهٔ استثنا',
'Een uitzonderingsregel bleef gelden voor echt dringende vragen.','An exception rule remained for genuinely urgent questions.','برای پرسش‌های واقعاً فوری قاعدهٔ استثنا باقی ماند.'),
}

def build():
    scenes=blocks()
    dev={}
    for line in DEVELOPMENTS.strip().splitlines():
        if not line.strip(): continue
        pieces=line.split('~'); assert len(pieces)==7,pieces
        key=int(pieces[0]); assert key not in dev
        dev[key]=(tri(pieces[1:4]),tri(pieces[4:7]))
    assert set(dev)==set(range(1,101))
    for scene in scenes:
        for row in scene['rows']:
            if row['term'] in FIXES:
                fixed=FIXES[row['term']]
                row.update(term=fixed[0],meaning=tri(fixed[1:4]),sentence=tri(fixed[4:7]))
    terms=[unicodedata.normalize('NFKC',r['term']).casefold().strip() for s in scenes for r in s['rows']]
    assert len(terms)==len(set(terms))==500
    summaries=[]
    for stage in ('pre-b2','b2','pre-c1'):
        vocabulary=[]; stories=[]
        for idx,scene in enumerate(scenes,1):
            sentences=[row['sentence'] for row in scene['rows']]
            b2,c1=dev[idx]
            ids=[]
            for pos,row in enumerate(scene['rows']):
                vid=f'{stage}-v{(idx-1)*5+pos+1:03d}'; ids.append(vid)
                if stage=='pre-b2':example=row['sentence']
                elif stage=='b2':
                    example=joined([sentences[pos], sentences[pos+1] if pos < 4 else b2])
                else:
                    # An advanced card gives a concrete use followed by the scene's
                    # interpretive consequence, not an invented proficiency score.
                    example=joined([row['sentence'],c1])
                vocabulary.append({'id':vid,'term':row['term'],'topic':scene['topic'],
                    'meaning':row['meaning'],'example':example})
            if stage=='pre-b2':
                paragraphs=[joined(sentences[:2]),joined(sentences[2:])]
                answer=sentences[-1]
                prompt=tri(('Welke gebeurtenis sluit dit verhaal af?','Which event concludes this story?','کدام رویداد پایان این داستان را شکل می‌دهد؟'))
                # Earlier facts from this same scene are plausible chronological
                # alternatives, rather than unrelated answers from another topic.
                distractors=[sentences[0], sentences[2]]
            elif stage=='b2':
                paragraphs=[joined(sentences[:3]),joined(sentences[3:]+[b2])]
                answer=b2
                prompt=tri(('Welke verdere ontwikkeling wordt als laatste vermeld?','Which further development is mentioned last?','کدام تحول بعدی در پایان ذکر می‌شود؟'))
                distractors=[sentences[1], sentences[3]]
            else:
                paragraphs=[joined(sentences[:3]),joined(sentences[3:]+[b2,c1])]
                answer=c1
                prompt=tri(('Welke bredere duiding geeft de slotzin aan de gebeurtenissen?','What broader interpretation does the final sentence give to the events?','جملهٔ پایانی چه برداشت گسترده‌تری از رویدادها ارائه می‌کند؟'))
                distractors=[sentences[4], b2]
            answer_index=(idx-1)%3
            options=distractors[:];options.insert(answer_index,answer)
            explanation=tri((f'De afloop maakt dit duidelijk: {answer["nl"]}',f'The outcome makes this clear: {answer["en"]}',f'پایان داستان این نکته را روشن می‌کند: {answer["fa"]}'))
            stories.append({'id':f'{stage}-s{idx:03d}','title':scene['title'],
                'topic':scene['topic'],'paragraphs':paragraphs,'vocabulary_ids':ids,
                'question':{'prompt':prompt,'options':options,'answer_index':answer_index,'explanation':explanation}})
        pack={'schema_version':1,'stage_id':stage,'review_status':'unreviewed',
            'vocabulary':vocabulary,'stories':stories}
        path=ROOT/'content'/'library'/f'{stage}.json'
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(pack,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        validate(pack)
        summaries.append({'stage':stage,'terms':len(vocabulary),'stories':len(stories),
            'topics':len({x['topic']['nl'] for x in stories}),
            'answer_positions':dict(Counter(s['question']['answer_index'] for s in stories))})
    print(json.dumps(summaries,ensure_ascii=False,indent=2))

def validate(pack):
    ids={x['id'] for x in pack['vocabulary']}
    assert len(ids)==500
    assert len({v['example']['nl'] for v in pack['vocabulary']})==500
    assert len(pack['stories'])==100
    assert len({s['title']['nl'] for s in pack['stories']})==100
    assert len({s['paragraphs'][0]['nl'] for s in pack['stories']})==100
    used=set()
    for item in pack['vocabulary']:
        for field in ('meaning','example','topic'):
            assert set(item[field])==set(LANGS)
            assert all(item[field][l].strip() for l in LANGS)
            assert item[field]['en']!=item[field]['nl'],item
            assert re.search('[\u0600-\u06ff]',item[field]['fa']),item
    for story in pack['stories']:
        assert len(story['paragraphs'])==2
        used.update(story['vocabulary_ids'])
        assert set(story['vocabulary_ids'])<=ids
        q=story['question']; assert 0<=q['answer_index']<len(q['options'])
        assert len({o['nl'] for o in q['options']})==3
        for lang in LANGS:
            narrative = ' '.join(p[lang] for p in story['paragraphs'])
            assert q['options'][q['answer_index']][lang] in story['paragraphs'][-1][lang]
            assert all(option[lang] in narrative for option in q['options'])
        for part in story['paragraphs']+[story['title'],q['prompt'],q['explanation']]+q['options']:
            assert all(part[l].strip() for l in LANGS)
            assert part['nl']!=part['en']
            assert re.search('[\u0600-\u06ff]',part['fa'])
    assert used==ids

if __name__=='__main__':build()
