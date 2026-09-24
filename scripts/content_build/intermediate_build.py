"""Build original, unreviewed recognition banks and graded anecdote collections.

Run: python scripts/content_build/intermediate_build.py
Adjacent stages deliberately revisit situations. Each stage has 500 recognition
items; these are not a frequency list, a mastery requirement or a CEFR certificate.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from intermediate_bank import GROUPS
from intermediate_stories import STORIES

ROOT = Path(__file__).resolve().parents[2]
LANGS=('nl','en','fa')
def tr(values): return dict(zip(LANGS, values, strict=True))
def sentence_words(text): return re.findall(r"[\wÀ-ÿ’'-]+", text.lower())
def stem_term(term):
    return re.sub(r'^(de|het|een|mijn)\s+', '', term.casefold())

# Keep shared words as a deliberate spiral while introducing different sets.
OMIT={'a2': {'participation','discussion'}, 'pre-b1': {'family','body'}, 'b1': {'food','drinks'}}
QUESTION=tr(('Welke uitleg past het best bij wat de personages doen?',
             'Which explanation best matches what the characters do?',
             'کدام توضیح با کار شخصیت‌ها بیشتر مطابقت دارد؟'))
EXTRA_TASK={
'a2': tr(('Vertel in één zin wat eerst misliep.','Say in one sentence what went wrong first.','در یک جمله بگو ابتدا چه مشکلی پیش آمد.')),
'pre-b1': tr(('Leg met want of omdat uit waarom de oplossing werkt.','Use a reason to explain why the solution works.','با بیان دلیل توضیح بده چرا راه‌حل مؤثر است.')),
'b1': tr(('Bespreek een andere mogelijke oplossing en vergelijk de gevolgen.','Discuss another possible solution and compare its consequences.','یک راه‌حل دیگر را مطرح کن و پیامدهایش را مقایسه کن.')),
}

# Examples that need word-specific syntax or a different physical context.
OVERRIDES={
 ('vehicles',0):[
 ('Ik neem de trein naar mijn werk.','I take the train to work.','من با قطار به محل کار می‌روم.'),
 ('Omdat mijn bus te laat is, neem ik vandaag de trein.','Because my bus is late, I take the train today.','چون اتوبوسم دیر کرده، امروز قطار می‌گیرم.'),
 ('Hoewel de trein meestal sneller is, controleer ik ook hoeveel tijd de overstap kost.','Although the train is usually faster, I also check how long changing takes.','با اینکه قطار معمولاً سریع‌تر است، زمان تعویض وسیله را هم بررسی می‌کنم.')],
 ('vehicles',2):[
 ('De tram stopt aan het plein.','The tram stops at the square.','تراموا در میدان می‌ایستد.'),
 ('Ik neem de tram, want dan hoef ik geen parkeerplaats te zoeken.','I take the tram because then I do not need to find parking.','تراموا می‌گیرم، چون دیگر لازم نیست جای پارک پیدا کنم.'),
 ('Als de tram tijdelijk niet rijdt, zoek ik vooraf uit welke vervangbus dezelfde richting uitgaat.','If the tram is temporarily not running, I find out beforehand which replacement bus goes in the same direction.','اگر تراموا موقتاً کار نکند، از قبل می‌پرسم کدام اتوبوس جایگزین به همان جهت می‌رود.')],
 ('helpverbs',9):[
 ('Kun je mij aan onze afspraak herinneren?','Can you remind me about our appointment?','می‌توانی قرارمان را به من یادآوری کنی؟'),
 ('Wil je mij morgen even aan onze afspraak herinneren?','Will you remind me tomorrow about our appointment?','می‌شود فردا قرارمان را به من یادآوری کنی؟'),
 ('Omdat mijn agenda deze week vol zit, vraag ik mijn collega om mij aan onze afspraak te herinneren.','Because my calendar is full this week, I ask my colleague to remind me about our appointment.','چون تقویمم این هفته پر است، از همکارم می‌خواهم قرارمان را به من یادآوری کند.')],
 ('learnverbs',5):[
 ('Ik wil deze tekst met het voorbeeld vergelijken.','I want to compare this text with the example.','می‌خواهم این متن را با مثال مقایسه کنم.'),
 ('Na de les probeer ik mijn tekst met het voorbeeld te vergelijken.','After class I try to compare my text with the example.','بعد از کلاس سعی می‌کنم متنم را با مثال مقایسه کنم.'),
 ('Ik vergelijk twee versies van dezelfde tekst om te begrijpen hoe de toon de betekenis beïnvloedt.','I compare two versions of the same text to understand how tone affects meaning.','دو نسخه یک متن را مقایسه می‌کنم تا بفهمم لحن چگونه بر معنی اثر می‌گذارد.')],
}
# Clarify context where an otherwise valid compound hides the target lemma.
FIXES={
('vehicles',0,'p1'):(
'Lina stapt uit de trein, mist de bus en ziet dat de tram niet meer rijdt. Een taxi is duurder dan ze wil betalen.',
'Lina gets off the train, misses the bus and sees that the tram has stopped running. A taxi costs more than she wants to pay.',
'لینا از قطار پیاده می‌شود، اتوبوس را از دست می‌دهد و می‌بیند تراموا دیگر کار نمی‌کند. تاکسی گران‌تر از مبلغی است که می‌خواهد بپردازد.'),
('weather',0,'p1'):(
'Eerder die week waren er regen, sneeuw en hagel. Voor het buitenfeest meldt de voorspelling nu storm en onweer.',
'Earlier that week there had been rain, snow and hail. The forecast now warns of a storm and thunder for the outdoor party.',
'اوایل آن هفته باران، برف و تگرگ آمده بود. حالا برای جشن بیرونی، طوفان و رعدوبرق پیش‌بینی می‌شود.'),
('shoppingdetails',1,'p1'):(
'Een gevulde lunchdoos heeft een mooie kleur en een stevig materiaal. Maar het gewicht en formaat zijn onhandig, en de houdbaarheid op het etiket geldt alleen voor het eten erin.',
'A filled lunch box has an attractive colour and sturdy material. But its weight and size are impractical, and the shelf life on the label applies only to the food inside.',
'ظرف غذای پُر رنگ زیبا و جنس محکمی دارد. اما وزن و اندازه‌اش نامناسب است و تاریخ ماندگاری روی برچسب فقط مربوط به غذای داخل آن است.'),
('learningnouns',1,'p1'):(
'In een telefoongesprek oefent Tom een beleefde vraag met een bijzin: «Kunt u zeggen wanneer het klaar is?» Daarna klinkt zijn vraag in de verleden tijd, «Had u dat niet gezegd?», door de klemtoon verwijtend.',
'In a telephone conversation Tom practises a polite request with a subordinate clause: “Can you say when it will be ready?” His next question in the past tense, “Had you not said that?”, sounds reproachful because of the stress.',
'تام در مکالمه تلفنی درخواست مؤدبانه‌ای با جمله وابسته تمرین می‌کند: «می‌توانید بگویید کی آماده است؟» بعد سؤال گذشته او، «مگر این را نگفته بودید؟»، به‌خاطر تکیه سرزنش‌آمیز به گوش می‌رسد.'),
('learningnouns',1,'p2'):(
'Hij luistert naar de opname en probeert een neutralere vraag: «Kunt u onze afspraak even herhalen?» Zijn partner begrijpt nu dat hij de afspraak wil controleren, niet iemand wil beschuldigen.',
'He listens to the recording and tries a more neutral question: “Could you repeat our agreement?” His partner now understands that he wants to check the agreement rather than blame anyone.',
'به ضبط گوش می‌دهد و سؤال خنثی‌تری امتحان می‌کند: «می‌توانید توافقمان را تکرار کنید؟» همراهش حالا می‌فهمد قصد بررسی توافق را دارد، نه سرزنش کسی.'),
('rooms',0,'p2'):(
'Geluid komt door de gang en ook de deur van de badkamer slaat hard dicht. De huisgenoten spreken één rustig uur af voor haar online examen.',
'Noise comes through the corridor and the bathroom door also bangs shut. The housemates agree on one quiet hour for her online exam.',
'صدا از راهرو می‌آید و در حمام هم محکم بسته می‌شود. هم‌خانه‌ها برای امتحان آنلاین او یک ساعت آرام توافق می‌کنند.'),
('learnverbs',1,'p1'):(
'Mina wil twee versies van een verzoek vergelijken en analyseren. Voorlezen door een vriend helpt haar om het verschil in toon te horen.',
'Mina wants to compare and analyse two versions of a request. Hearing a friend read them aloud helps her hear the difference in tone.',
'مینا می‌خواهد دو شکل یک درخواست را مقایسه و تحلیل کند. بلند خواندن دوستش کمک می‌کند تفاوت لحن را بشنود.'),
('restaurant',0,'p1'):(
'Op de menukaart ziet Hana het dagmenu en het vegetarische gerecht. De ingrediënten en allergenen van de saus staan er niet duidelijk bij.',
'On the menu Hana sees the daily menu and the vegetarian dish. The sauce’s ingredients and allergens are not clearly listed.',
'هانا در منو غذای روز و غذای گیاهی را می‌بیند. مواد و حساسیت‌زاهای سس روشن نوشته نشده‌اند.'),
('kitchen',1,'p1'):(
'Lou wast een bord, een kom en een glas af. Hij legt de snijplank weg, maar het vergiet voor de pasta is zoek.',
'Lou washes a plate, a bowl and a glass. He puts the chopping board away, but the colander for the pasta is missing.',
'لو بشقاب، کاسه و لیوان را می‌شوید. تخته برش را کنار می‌گذارد، اما آبکش پاستا گم شده است.'),
('food',1,'p1'):(
'Op de markt koopt Yasmin aardappelen, champignons, uien en bonen. Ze vergeet de aardbeien voor het dessert.',
'At the market Yasmin buys potatoes, mushrooms, onions and beans. She forgets the strawberries for dessert.',
'یاسمین از بازار سیب‌زمینی، قارچ، پیاز و لوبیا می‌خرد. توت‌فرنگی دسر را فراموش می‌کند.'),
}
for s in STORIES:
    for part in ('p1','p2'):
        if (s['group'],s['half'],part) in FIXES:
            s[part]=FIXES[(s['group'],s['half'],part)]

def make_example(group,item,index,stage_index):
    nl,meaning,en,fa=item
    if (group['key'],index) in OVERRIDES:
        return tr(OVERRIDES[(group['key'],index)][stage_index])
    pattern=group['patterns'][stage_index]
    if group['key']=='shoppingdetails' and stage_index==1:
        pattern=('Ik vergelijk {nl} van twee producten.','I compare {en} of two products.','من {fa} دو محصول را مقایسه می‌کنم.')
    if group['key']=='sports' and stage_index==2:
        fa=fa[:-1]+'یم' if fa.endswith('م') else fa
    result=tr(tuple(p.format(nl=nl,en=en,fa=fa) for p in pattern))
    result['nl']=result['nl'].replace('te samenvatten','samen te vatten').replace('te voorlezen','voor te lezen')
    if group['key']=='station' and nl=='de trap':
        result['en']=result['en'].replace('the stairs is','the stairs are')
    if group['key']=='helpverbs' and nl=='ondersteunen':
        result['fa']=result['fa'].replace('به من حمایت برسانی','از من حمایت کنی')
    if group['key']=='sportsgear' and nl=='de zwembril':
        result['en']=result['en'].replace('use it afterwards','use them afterwards')
    if group['key']=='sports' and nl=='schaatsen':
        result['fa']=result['fa'].replace('اسکیت','اسکیت روی یخ')
    if group['key']=='renting' and stage_index==2:
        result=tr((f'Ik vraag uitleg over {nl}, zodat ik de informatie goed begrijp.', f'I ask for an explanation of {en} so I understand the information correctly.', f'درباره {fa} توضیح می‌خواهم تا اطلاعات را درست بفهمم.'))
    if group['key']=='shoppingdetails' and nl=='de prijs' and stage_index==2:
        result=tr(('Ik vraag naar de prijs en controleer of eventuele extra kosten inbegrepen zijn.','I ask about the price and check whether any additional costs are included.','درباره قیمت می‌پرسم و بررسی می‌کنم آیا هزینه‌های اضافه احتمالی در آن حساب شده‌اند.'))
    if group['key']=='ingredients' and nl in ('knoflook','gember') and stage_index==1:
        result=tr((f'Ik snijd {nl} fijn voordat ik de soep klaarmaak.',f'I chop {en} finely before making the soup.',f'پیش از آماده کردن سوپ، {fa} را ریز خرد می‌کنم.'))
    return result

def selected_story_text(s,stage):
    # A2 reads the event. The bridge explicitly connects cause and result.
    # B1 reads the narrative first and answers a separate interpretation question;
    # the insight appears only as feedback so the answer is not printed in the text.
    p1=list(s['p1']);p2=list(s['p2'])
    if stage=='pre-b1':
        p2=[a+' '+b for a,b in zip(p2,s['insight'],strict=True)]
    return [tr(p1),tr(p2)]

def build():
  for level,stage in enumerate(('a2','pre-b1','b1')):
    groups=[g for g in GROUPS if g['key'] not in OMIT[stage]]
    items=[];group_ids={};term_ids={}
    for g in groups:
      group_ids[g['key']]=[]
      for j,item in enumerate(g['items']):
        nl,meaning,en,fa=item
        vid=f'{stage}-v{len(items)+1:03d}'
        assert stem_term(nl) not in term_ids,(stage,nl)
        term_ids[stem_term(nl)]=vid;group_ids[g['key']].append(vid)
        items.append(dict(id=vid,term=nl,topic=tr(g['topic']),meaning=tr((meaning,en,fa)),example=make_example(g,item,j,level)))
    chosen=[s for s in STORIES if s['group'] in group_ids]
    outputs=[]
    for i,s in enumerate(chosen):
      # Use different, plausible cause/result distractors drawn from other stories.
      # Nearby rows often share a theme; reject identical statements explicitly.
      other=[chosen[(i+offset)%len(chosen)] for offset in (7,19)]
      opts=[tr(s['insight']),tr(other[0]['insight']),tr(other[1]['insight'])]
      answer=i%3
      opts=opts[-answer:]+opts[:-answer] if answer else opts
      paragraphs=selected_story_text(s,stage)
      outputs.append(dict(id=f'{stage}-s{i+1:03d}',title=tr(s['title']),topic=tr(next(g['topic'] for g in groups if g['key']==s['group'])),paragraphs=paragraphs,vocabulary_ids=group_ids[s['group']][s['half']*5:s['half']*5+5],question=dict(prompt=QUESTION,options=opts,answer_index=answer,explanation=tr(s['insight']))))
    result=dict(schema_version=1,stage_id=stage,review_status='unreviewed',vocabulary=items,stories=outputs)
    # Machine checks cannot replace linguistic or educational review.
    assert len(items)==500 and len(outputs)==100
    assert len({x['id'] for x in items})==500
    assert len({x['term'].casefold() for x in items})==500
    assert set(x['id'] for x in items)==set(v for s in outputs for v in s['vocabulary_ids'])
    assert len({s['title']['nl'] for s in outputs})==100
    assert len({json.dumps(s['paragraphs'],ensure_ascii=False) for s in outputs})==100
    for item in items:
      for name in ('topic','meaning','example'):
        assert set(item[name])==set(LANGS)
        assert all(v.strip() for v in item[name].values())
        assert re.search('[\u0600-\u06ff]',item[name]['fa'])
    for s in outputs:
      assert len(s['paragraphs'])==2
      assert 0<=s['question']['answer_index']<3
      assert len({o['nl'] for o in s['question']['options']})==3
      for p in s['paragraphs']:
        assert all(p[lang].strip() for lang in LANGS)
    path=ROOT/'content'/'library'/f'{stage}.json'
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(f'{stage}: {len(items)} vocabulary, {len(outputs)} stories, {len(set(v for s in outputs for v in s["vocabulary_ids"]))} referenced words; answer distribution '+str([sum(s['question']['answer_index']==i for s in outputs) for i in range(3)]))
if __name__=='__main__': build()
