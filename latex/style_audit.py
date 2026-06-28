import re

# ---------- MAIN.TEX prose ----------
def strip_latex(txt):
    txt = re.sub(r'(?<!\\)%.*', '', txt)
    for env in ['lstlisting','tabular','table\\*?','figure\\*?',
                'equation','align\\*?','subfigure','highlights',
                'keywords','abstract']:
        txt = re.sub(r'\\begin\{'+env+r'\}.*?\\end\{'+env+r'\}', ' ',
                     txt, flags=re.DOTALL)
    txt = re.sub(r'\\\[.*?\\\]', ' ', txt, flags=re.DOTALL)
    txt = re.sub(r'\\irule\{.*?\}\s*\{.*?\}\s*\{.*?\}\s*\{.*?\}', ' ',
                 txt, flags=re.DOTALL)
    txt = re.sub(r'\\input\{[^}]*\}', ' ', txt)
    return txt

raw = open('main.tex', encoding='utf-8').read()
body = raw[raw.find(r'\section{Introduction}'):raw.find(r'\appendix')]
main_prose = strip_latex(body)

# de-LaTeX a copy for "natural text" patterns (drop \commands, keep their arg text)
def naturalize(t):
    t = re.sub(r'\\(emph|textbf|texttt|textit|textsc)\{([^}]*)\}', r'\2', t)
    t = re.sub(r'~\\citep\{[^}]*\}', '', t)
    t = re.sub(r'\\citep\{[^}]*\}', '', t)
    t = re.sub(r'\\ref\{[^}]*\}', 'X', t)
    t = re.sub(r'\\eqref\{[^}]*\}', 'X', t)
    t = re.sub(r'\\label\{[^}]*\}', '', t)
    t = re.sub(r'\\[a-zA-Z]+\b', ' ', t)   # drop remaining commands
    return t
main_nat = naturalize(main_prose)

# ---------- BASELINES (strip references) ----------
def load_base(fn):
    t = open('jsa_toolkit/'+fn, encoding='utf-8').read()
    lines = t.split('\n')
    for i,l in enumerate(lines):
        if l.strip().lower() in ('references','bibliography'):
            lines = lines[:i]; break
    return '\n'.join(lines)

texts = {
 'MAIN': main_nat,
 'jsa1': load_base('jsa.txt'),
 'jsa2': load_base('jsa2.txt'),
 'jsa3': load_base('jsa3.txt'),
}

def wc(t): return len(re.findall(r'[A-Za-z][A-Za-z\-]*', t))
WORDS = {k: wc(v) for k,v in texts.items()}
print("WORDS:", WORDS)
print()

def per1k(n,k): return round(1000.0*n/WORDS[k],2)

def report(name, patterns):
    # patterns: dict key->(text, regex, flags)
    print(f"### {name}")
    for k in texts:
        cnt = len(re.findall(patterns[k][0], patterns[k][1], patterns[k][2])) if isinstance(patterns,dict) else 0
    print()

def count(k, regex, flags=0):
    return len(re.findall(regex, texts[k], flags))

def row(label, regex, flags=0, transform=None):
    res={}
    for k in texts:
        t = texts[k] if transform is None else transform(texts[k])
        res[k]=len(re.findall(regex, t, flags))
    line=f"{label:42s} | "
    for k in ['MAIN','jsa1','jsa2','jsa3']:
        line+=f"{res[k]:3d} ({per1k(res[k],k):4.2f}) "
    print(line)
    return res

print("Pattern  (raw count, per-1k-words)        |  MAIN          jsa1          jsa2          jsa3")
print("-"*100)

# 1. Em-dash density. MAIN: '---' ; baselines: unicode — OR ' - ' spaced hyphen as dash
def emdash_main(t): return t   # main uses ---
row("Em-dash '---' (MAIN) / '—' (base)", r'XXXX')  # placeholder, do manual below

# manual em-dash
em={}
em['MAIN']=len(re.findall(r'---', texts['MAIN']))
for k in ['jsa1','jsa2','jsa3']:
    em[k]=len(re.findall(r'—', texts[k])) + len(re.findall(r'(?<=\w) - (?=\w)', texts[k]))
print(f"{'Em-dash (--- / — + spaced-hyphen)':42s} | "+ " ".join(f"{em[k]:3d} ({per1k(em[k],k):4.2f})" for k in ['MAIN','jsa1','jsa2','jsa3']))

# 2. inline enumeration markers (i)(ii)(1)(2)(a)(b)
row("Inline (i)/(ii)/(iii) roman markers", r'\((?:i|ii|iii|iv|v|vi)\)')
row("Inline (1)/(2)/(3) numeric markers", r'\((?:[1-9])\)')
row("Inline (a)/(b)/(c) alpha markers", r'\([a-d]\)')

# 3. First/Second/Third enumeration
row("Sentence 'First,'/'Second,'/'Third,'", r'\b(?:First|Second|Third|Fourth|Finally),', 0)

# 4. sentence-initial This/These + noun (anaphoric)
row("'. This/These X' anaphoric opener", r'(?:^|\.\s+)(?:This|These)\s+[a-z]+', re.M)

# 5. passive (rough): be-verb + past participle (-ed/known irregulars)
row("Passive 'is/are/was/were/be/been + Ved'",
    r'\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?\w+(?:ed|en)\b')

# 6. 'not merely ... ; it is' / 'not only ... but'
row("'not merely/only ... ' emphasis", r'\bnot\s+(?:merely|only|just|simply)\b')
row("'rather than' contrastive", r'\brather than\b')

# 7. term( gloss ) parenthetical restatement
row("Parenthetical gloss '(...)'  total parens", r'\([^)]{2,60}\)')

# 8. noun-compound chains X-Y-Z (>=2 internal hyphens, words)
row("Hyphen compound chains (>=2 hyphens)", r'\b[A-Za-z]+-[A-Za-z]+-[A-Za-z]+\b')

# 9. backward handoff transitions
row("'we now / next / turn to / following'", r'\b(?:we now|in turn|turn to|next(?:\s+section)?|as follows|following)\b', re.I)

# 10. rule-of-three: 'A, B, and C' triads
row("Triadic 'A, B, and C' lists", r'\w+,\s+\w[\w\- ]{0,30}?,\s+and\s+\w+')

# 11. e.g./i.e. density
row("'e.g.' / 'i.e.' parenthetical cues", r'\b(?:e\.g\.|i\.e\.)')

# 12. bare decimal (0.xxx)
row("Bare decimals 0.xxx", r'\b0\.\d{2,3}\b')

# 13. colon-led elaboration mid-sentence ' : lowercase'
row("Colon elaboration ': lowercase'", r'[a-z]:\s+[a-z]')

# 14. semicolon density
row("Semicolons ';'", r';')

print()
print("="*60)
print("DASH DETAIL (main prose, pre-naturalize)")
_body = raw[raw.find(r'\section{Introduction}'):raw.find(r'\appendix')]
_p = strip_latex(_body)
import re as _re
print("  '---' em-dash in prose:", len(_re.findall(r'---', _p)))
print("  '--' two-hyphen total:", len(_re.findall(r'(?<!-)--(?!-)', _p)))
print("  ASIDE en-dashes (alpha--alpha):")
for m in _re.finditer(r'[A-Za-z]{3,}\s*--\s*[A-Za-z]{3,}', _p):
    print("    ...", _p[max(0,m.start()-25):m.end()+25].replace(chr(10),' '), "...")

print()
print("="*70)
print("TARGETED RHETORICAL TEMPLATES (user-flagged)")
def show(label, regex, flags=0, ctx=0):
    print(f"\n--- {label} ---")
    res={}
    for k in ['MAIN','jsa1','jsa2','jsa3']:
        ms=list(re.finditer(regex, texts[k], flags))
        res[k]=len(ms)
    print("  counts/per1k: "+" ".join(f"{k}={res[k]}({per1k(res[k],k)})" for k in ['MAIN','jsa1','jsa2','jsa3']))
    if ctx:
        for m in list(re.finditer(regex, texts['MAIN'], flags))[:ctx]:
            print("   MAIN:",texts['MAIN'][max(0,m.start()-40):m.end()+40].replace(chr(10),' '))
    return res

# "not merely/just X; it is Y"  and  "is not X but Y"
show("'not merely/just ...; it is' template", r'not\s+(?:merely|just|simply)\b[^.]{0,80}', 0, 5)
# appositive contrast  ", not <word>"  (X, not Y rhetorical)
show("Appositive contrast ', not <X>'", r',\s+not\s+(?:a\s+|an\s+|the\s+|of\s+|by\s+|on\s+|every\s+)?[a-z]+', 0, 8)
# subsection opener "This subsection answers/presents/..."
show("'This subsection/section answers/presents' opener", r'This (?:subsection|section)\s+\w+', re.I, 6)
# "is a property of X rather than Y" / "a property of the runtime"
show("'a property of ... rather than/not'", r'a (?:property|consequence|matter|function) of', re.I, 4)
# colon mega-elaboration with em-dash style "X: <clause>"
# "by design" / "deliberately" intentionality markers
show("intentionality 'by design/deliberately/by construction'", r'\b(?:by design|deliberately|by construction|intentional)', re.I, 0)

print()
print("="*70)
print("GLOSS-REPETITION & intentionality context")
# repeated re-gloss of same acronym: "(lightweight virtual machine)" etc.
for term in [r'lightweight virtual machine', r'structured intermediate representation',
             r'intermediate representation', r'virtual machine']:
    c=len(re.findall(term, texts['MAIN'], re.I))
    print(f"  gloss '{term}': MAIN={c}")
print("  Intentionality instances in MAIN:")
for m in re.finditer(r'\b(?:by design|deliberately|by construction)\b', texts['MAIN'], re.I):
    print("   ...",texts['MAIN'][max(0,m.start()-45):m.end()+45].replace(chr(10),' '))

print()
print("="*70)
print("BEHAVIORAL (anti-human) TELLS")
def cnt(k,rx,fl=0): return len(re.findall(rx,texts[k],fl))
def line(label,rx,fl=0):
    print(f"{label:46s} | "+" ".join(f"{x}={cnt(x,rx,fl)}({per1k(cnt(x,rx,fl),x)})" for x in ['MAIN','jsa1','jsa2','jsa3']))

# headline-number saturation (same stat restated)
for num in ['9.8','13.8','0.982','48.7','1.000','UABR','8{,}000|8,000|8000']:
    line(f"repeats of '{num}'", num)
# recap / summary restatement phrases
line("'In summary / in turn / to summarize'", r'\b(?:In summary|in turn|To summarize|in conclusion)\b', re.I)
# Q1..Q4 style restatement
line("'Q1/Q2/Q3/Q4' or '(Efficiency)/(Security)' tags", r'Q[1-4]\b')
# explicit roadmap threading "developed/revisited/examine next/as we will see"
line("roadmap threading (developed/revisited/we will see/next)", r'\b(?:developed fully|revisited|we will see|examined next|as we|introduced (?:earlier|in Section)|return to)\b', re.I)
# 'as follows:' colon dumps into list
line("'as follows' / 'the following'", r'\b(?:as follows|the following)\b', re.I)
# running example restatements
line("'running example'", r'running example', re.I)
# parallel chiastic closers: ' on the X it ...; on the Y it ...'
line("'on the X ...; on the Y ...' parallel", r'on the \w+[^.;]{0,40}[;,] on the \w+', re.I)
# 'This X is Y' aphoristic single-sentence paragraph closers hard to grep; count ': it' reframes
line("dramatic reframe '; it is / : it'", r'(?:;\s+it is|:\s+it\s+)', 0)

print()
print("="*70)
print("CLOSER APHORISMS & SINGLE-CAUSE REDUCTIONS (the classic LLM move)")
# "trace to a single design decision" / "stem from" / "comes down to"
for rx in [r'(?:trace|traces|traced|stem|stems|reduce|reduces|comes down|boils down|attributable)\s+(?:to|from)\b',
           r'a single (?:design )?(?:decision|choice|mechanism|property)',
           r'The (?:key|central|practical) (?:property|takeaway|implication|insight) is',
           r'by design\b',
           r'is what (?:makes|gives|distinguishes|lets)']:
    print(f"\n[{rx[:45]}]")
    for m in re.finditer(rx, texts['MAIN'], re.I):
        print("   ...", texts['MAIN'][max(0,m.start()-55):m.end()+55].replace(chr(10),' '))

print()
print("="*70)
print("COMPLEMENTARY DIM 1: SENTENCE-LENGTH RHYTHM (burstiness)")
import statistics as st
def sentences(t):
    t=re.sub(r'\s+',' ',t)
    # protect common abbreviations
    for a in ['e.g.','i.e.','Fig.','Eq.','vs.','Sec.','Prop.','approx.','cf.','et al.','Inc.','Ref.','no.','No.']:
        t=t.replace(a,a.replace('.','<D>'))
    parts=re.split(r'(?<=[.!?])\s+(?=[A-Z(])',t)
    out=[]
    for p in parts:
        p=p.replace('<D>','.')
        w=re.findall(r'[A-Za-z][A-Za-z\-]*',p)
        if len(w)>=3: out.append(len(w))
    return out
for k in ['MAIN','jsa1','jsa2','jsa3']:
    s=sentences(texts[k])
    short=sum(1 for x in s if x<=8); lng=sum(1 for x in s if x>=40)
    print(f"  {k}: n={len(s)} mean={st.mean(s):.1f} sd={st.pstdev(s):.1f} CV={st.pstdev(s)/st.mean(s):.2f} | short(<=8w)={short}({100*short/len(s):.0f}%) long(>=40w)={lng}({100*lng/len(s):.0f}%)")

print()
print("COMPLEMENTARY DIM 2: sentence-initial signpost adverbs")
def cnt(k,rx,fl=0): return len(re.findall(rx,texts[k],fl))
def line(label,rx,fl=re.M):
    print(f"{label:46s} | "+" ".join(f"{x}={cnt(x,rx,fl)}({per1k(cnt(x,rx,fl),x)})" for x in ['MAIN','jsa1','jsa2','jsa3']))
line("'Notably/Importantly/Crucially/Indeed' init", r'(?:^|\.\s+)(?:Notably|Importantly|Crucially|Indeed|Specifically|Conversely|Critically|Remarkably)\b')
line("'Moreover/Furthermore/Additionally' init", r'(?:^|\.\s+)(?:Moreover|Furthermore|Additionally|Likewise)\b')
line("'However/Thus/Therefore/Hence' init", r'(?:^|\.\s+)(?:However|Thus|Therefore|Hence|Consequently)\b')
line("'It is worth/important to note' meta", r'[Ii]t is (?:worth|important|interesting) (?:noting|to note|to point)')

print()
print("COMPLEMENTARY DIM 3: run-in bold lead-in headers \textbf{X.}")
mt=open('main.tex',encoding='utf-8').read()
mb=mt[mt.find(r'\section{Introduction}'):mt.find(r'\appendix')]
rib=re.findall(r'\textbf\{[A-Z][^}]{2,40}?\.?\}\s*(?=[A-Z])', mb)
rib2=re.findall(r'\(?:noindent\)?textbf\{[^}]{3,45}\}\s*(?:\.|:)?\s*[A-Z]', mb)
print(f"  MAIN run-in bold headers (\textbf{{...}} starting a sentence): ~{len(rib2)}")
print("  examples:", [re.search(r'textbf\{([^}]*)\}',x).group(1) for x in rib2[:12]])

print()
print("COMPLEMENTARY DIM 4: 'each/every' universal-parallel density")
line("'each/every' universal quantifier", r'\b(?:each|every)\b', 0)

print()
print("COMPLEMENTARY DIM 5: explicit causal signposting density")
line("'because/since/so that/thereby/thus' causal", r'\b(?:because|since|so that|thereby|thus|hence|therefore)\b', re.I)

print()
print("COMPLEMENTARY DIM 6: sentence-opener diversity (repetition)")
for k in ['MAIN','jsa1','jsa2','jsa3']:
    ss=re.findall(r'(?:^|\.\s+)([A-Z][a-z]+)', texts[k])
    from collections import Counter
    c=Counter(ss); top=c.most_common(5)
    uniq=len(c)/max(1,len(ss))
    print(f"  {k}: opener-type/token={uniq:.2f}  top5={top}")

print()
print("="*70)
print("RECOUNT: run-in bold headers + 'The'-opener share + short-sentence samples")
mt=open('main.tex',encoding='utf-8').read()
mb=mt[mt.find('\section{Introduction}'):mt.find('\appendix')]
hdrs=re.findall(r'\textbf\{([^}]{2,45})\}', mb)
# keep ones that look like run-in headers (Title Case / end with . or :), drop inline emphasis of numbers
runin=[h for h in hdrs if re.match(r'^[A-Z]', h) and not re.search(r'\d', h)]
print(f"  total \textbf{{}} in body: {len(hdrs)}; run-in-style headers: {len(runin)}")
print("  per-1k:", round(1000*len(runin)/WORDS['MAIN'],2))
print("  headers:", runin)
# baselines have no bold; check ALL-CAPS or numbered run-in lead-ins as analog? skip — bold is latex-only
print()
# 'The' opener share
for k in ['MAIN','jsa1','jsa2','jsa3']:
    ss=re.findall(r'(?:^|\.\s+)([A-Z][a-z]+)', texts[k])
    the=sum(1 for x in ss if x=='The')
    print(f"  {k}: 'The'-opener share = {the}/{len(ss)} = {100*the/len(ss):.0f}%")
print()
print("  MAIN short sentences (<=8 words) sample:")
for s in re.split(r'(?<=[.])\s+(?=[A-Z])', re.sub(r'\s+',' ',texts['MAIN'])):
    w=re.findall(r'[A-Za-z][A-Za-z\-]*',s)
    if 3<=len(w)<=7: print("    -",s.strip()[:90])

print()
print("="*70)
print("DIM 7: AI-FAVORITE LEXICON (auto-detector vocab)")
favs=['leverage','delve','underscore','pivotal','realm','showcase','seamless',
      'holistic','nuanced','intricate','robust','crucial','vital','myriad',
      'plethora','tapestry','testament','navigate','foster','endeavor',
      'paramount','utilize','facilitate','encompass','elucidate','notably',
      'furthermore','moreover','comprehensive','cutting-edge','state-of-the-art']
for k in ['MAIN','jsa1','jsa2','jsa3']:
    hits={w:len(re.findall(r'\b'+w+r'\b',texts[k],re.I)) for w in favs}
    hits={w:c for w,c in hits.items() if c}
    tot=sum(hits.values())
    print(f"  {k}: total={tot} ({per1k(tot,k)}/1k)  {hits}")

print()
print("DIM 8: REPEATED 4-GRAM SCAFFOLDING (formulaic reuse) in MAIN prose")
from collections import Counter
def grams(t,n):
    w=re.findall(r'[a-z]+',t.lower())
    return [' '.join(w[i:i+n]) for i in range(len(w)-n+1)]
g4=Counter(grams(texts['MAIN'],4))
# drop pure content noun-strings; show repeated >=3
rep=[(p,c) for p,c in g4.most_common(40) if c>=3]
for p,c in rep: print(f"   {c}x  {p}")

print()
print("DIM 9: CONTRASTIVE BALANCING 'X, while/whereas Y'")
def cnt(k,rx,fl=0): return len(re.findall(rx,texts[k],fl))
def line(label,rx,fl=0):
    print(f"{label:42s} | "+" ".join(f"{x}={cnt(x,rx,fl)}({per1k(cnt(x,rx,fl),x)})" for x in ['MAIN','jsa1','jsa2','jsa3']))
line("', while/whereas' mid-sentence contrast", r',\s+(?:while|whereas)\b', re.I)
line("'not X but Y' / 'X but not Y'", r'\bbut not\b|\bnot\b[^.,;]{1,25}\bbut\b', re.I)

print()
print("DIM 10: META-DISCOURSE 'we/our' density (author presence)")
line("'we/our/us'", r'\b(?:we|our|us)\b', re.I)

print()
print("DIM 11: CONTENT-TERM SATURATION (favorite key phrases)")
for ph in ['bounded execution','capability gating','untrusted','step limit|step-limit','closed-loop','formal']:
    line(f"'{ph}'", ph, re.I)
