"""Generate the 121-W fixture and measure the unmodified v1.5 query on synthetic inputs."""
import ast
import collections
import hashlib
import json
import math
import pathlib
import sqlite3
import statistics
import time
import types

OUT = pathlib.Path(__file__).resolve().parent
SRC = pathlib.Path('/Users/yongho/Library/Application Support/ROUTABL-AssetSearch')
FAMILIES = [
    ('quartz', '수정색인보정', '결정관측원리', 'ㄱㅈㄱㅊ'),
    ('cedar', '삼나무복원절차', '연륜표본보존', 'ㅇㄹㅍㅂ'),
    ('opal', '오팔검증규약', '빛분산관측법', 'ㅂㅂㅅ'),
    ('beacon', '등대경로확인', '안개항법원리', 'ㅇㄱㅎㅂ'),
    ('lumen', '광량측정노트', '렌즈투과가정', 'ㄹㅈㅌㄱ'),
    ('tundra', '동토온도기록', '빙층변화수식', 'ㅂㅊㅂㅎ'),
    ('zephyr', '미풍모델정리', '풍속오차공식', 'ㅍㅅㅇㅊ'),
    ('marble', '대리석분류표', '표면입도계수', 'ㅍㅁㅇㄷ'),
    ('cobalt', '코발트분석법', '파장교정실험', 'ㅍㅈㄱㅈ'),
    ('amber', '호박표본대장', '수지경화시간', 'ㅅㅈㄱㅎ'),
]
KINDS = ('exact_id', 'hangul_infix', 'body_only', 'configured_alias', 'jamo_intent')


def write_json(name, obj):
    with (OUT / name).open('x', encoding='utf-8') as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
        fh.write('\n')


def hashed(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def fixture():
    docs, queries, aliases, crosswalk = [], [], {}, {}
    for i, (topic, title, phrase, jamo) in enumerate(FAMILIES, 1):
        doc_id = f'SIM-{i:03}'
        new = f'00_SYNTHETIC/{doc_id}.md'
        duplicate = f'00_SYNTHETIC/archive/{doc_id}-copy.md'
        old = f'00_SYNTHETIC/legacy/{doc_id}-old.md'
        text = phrase + ' synthetic topic ' + topic
        rows = [
            (new, title, text, 'OK', hashed(text), f'{doc_id}-current'),
            (duplicate, title, text, 'OK', hashed(text), f'{doc_id}-current'),
            (old, title + ' 구판', text + ' archived', 'PDF_TEXT_NOT_EXTRACTED', hashed(text+' archived'), f'{doc_id}-old'),
        ]
        for path, name, body, status, digest, group in rows:
            docs.append(dict(path=path, title=name, content=body, tags=topic, status=status, sha=digest, group=group))
        crosswalk[new] = dict(sha256=hashed(text), asset_id=doc_id,
                              github_verified=False, nas_verified=False, version='v2')
        alias = 'alias-' + topic
        aliases[alias] = [topic]
        for j, (kind, term) in enumerate(zip(KINDS, (doc_id, title[1:-1], phrase, alias, jamo))):
            queries.append(dict(id=f'Q{len(queries)+1:02}', kind=kind, term=term, scope='all',
                                split='dev' if (i+j)%5<3 else 'holdout',
                                grades={f'{doc_id}-current': 3, f'{doc_id}-old': 1},
                                top_path=new, expected_sha=hashed(text), expected_status='OK',
                                expected_version='v2', duplicate_paths=sorted([new,duplicate])))
    for i in range(1200):
        token = hashed(f'121-fixture-distractor-{i}')
        docs.append(dict(path=f'00_SYNTHETIC/decoys/D{i:04}.txt', title=f'표준 잡음 {i:04}',
                         content=('무관자료 ' + token + '\n') * 8, tags='decoy', status='OK',
                         sha=token, group=f'decoy-{i:04}'))
    return docs, queries, aliases, crosswalk


def read_pinned(name, expected):
    data = (SRC/name).read_bytes()
    if hashlib.sha256(data).hexdigest()!=expected:
        raise RuntimeError('source hash mismatch')
    return ast.parse(data)


def load_functions():
    index = read_pinned('routabl_assetsearch_v1_1.py','bdea926cabe2157bdec2f8d0c69173e1a50dfa35ec5cae40563f16711588cc83')
    search = read_pinned('routabl_search_v1_5_service.py','55b8747b145463c62366deba13904e3136893b8a611bb4ae94bbc2d7a642347d')
    ie = {}
    ix = [n for n in index.body if isinstance(n,ast.FunctionDef) and n.name in {'setup','add'}]
    exec(compile(ast.Module(body=ix,type_ignores=[]),'<index methods>','exec'),ie)
    names = {'kind','safe_like','basename','relevant','query'}
    qx = [n for n in search.body if isinstance(n,ast.FunctionDef) and n.name in names]
    for n in qx:
        n.returns=None
        for a in n.args.args:
            a.annotation=None
    qe = {'math':math,'Any':object,'MAIN_PROJECTS':(),'SCOPE':{'all'}}
    exec(compile(ast.Module(body=qx,type_ignores=[]),'<query methods>','exec'),qe)
    return ie, qe


def load_row(add, db, doc, mtime=1, epoch=1):
    add(db,doc['path'],'SYNTHETIC','FILE',len(doc['content'].encode()),mtime,
        doc['sha'],doc['status'],doc['title'],doc['tags'],doc['content'],epoch)


def measure(values):
    seq=sorted(values)
    return dict(n=len(seq),mean_ms=round(statistics.mean(seq),5),
                p50_ms=round(seq[math.ceil(len(seq)*.50)-1],5),
                p95_ms=round(seq[math.ceil(len(seq)*.95)-1],5),max_ms=round(seq[-1],5))


def avg(values):
    return round(statistics.mean(values),6)


def grade(result, q, groups):
    top = result['results'][:10]
    found = [groups[r['path']] for r in top]
    rel = [q['grades'].get(key, 0) for key in found]
    seen = set()
    gains=[]
    for key, value in zip(found, rel):
        gains.append(value if key not in seen else 0)
        seen.add(key)
    ideal=sorted(q['grades'].values(),reverse=True)[:10]
    def dcg(values):
        return sum((2**r-1)/math.log2(i+2) for i,r in enumerate(values))
    target = next((row for row in top if row['path']==q['top_path']),None)
    provenance = target.get('provenance') or {} if target else {}
    return dict(recall=sum(r>0 for r in gains)/len(q['grades']),
                precision=sum(r>0 for r in gains)/10,
                mrr=next((1/(i+1) for i,r in enumerate(gains) if r>0),0),
                ndcg=dcg(gains)/dcg(ideal),
                duplicate=bool(target and target['duplicate_count']==2 and
                               sorted(r['path'] for r in target['locations'])==q['duplicate_paths'] and
                               found.count(groups[q['top_path']])==1),
                latest=bool(top and top[0]['path']==q['top_path'] and top[0]['status']==q['expected_status'] and
                            provenance.get('sha256')==q['expected_sha'] and provenance.get('version')==q['expected_version']))


def main():
    docs, queries, aliases, crosswalk = fixture()
    groups={doc['path']:doc['group'] for doc in docs}
    ie, qe = load_functions()
    full, inc, noop = [],[],[]
    timer=lambda: time.perf_counter_ns()/1e6
    for iteration in range(10):
        db=sqlite3.connect(':memory:')
        start=timer()
        ie['setup'](db)
        for doc in docs:
            load_row(ie['add'],db,doc)
        db.commit()
        full.append(timer()-start)
        changed=dict(docs[-1])
        changed['content']+=' update'
        changed['sha']=hashed(changed['content'])
        start=timer()
        load_row(ie['add'],db,changed,mtime=2,epoch=2)
        db.commit()
        inc.append(timer()-start)
        start=timer()
        load_row(ie['add'],db,changed,mtime=2,epoch=3)
        db.commit()
        noop.append(timer()-start)
        assert db.execute('SELECT sha,scan FROM docs WHERE path=?',(changed['path'],)).fetchone()==(changed['sha'],3)
        assert db.execute('SELECT count(*) FROM ft WHERE ft MATCH ?',( 'update',)).fetchone()[0]==1
        if iteration!=9:
            db.close()
    pages = db.execute('PRAGMA page_count').fetchone()[0]
    size = pages*db.execute('PRAGMA page_size').fetchone()[0]
    qe.update(INDEX='synthetic', ALIASES=aliases, CROSSWALK=crosswalk,
              sqlite3=types.SimpleNamespace(connect=lambda *args,**kwargs: db, Row=sqlite3.Row))
    grades=collections.defaultdict(list)
    for q in queries:
        result=qe['query'](q['term'],scope=q['scope'],page_size=10)
        row=grade(result,q,groups)
        for group in ('all',q['split'],q['kind']):
            grades[group].append(row)
    report=dict(sqlite=sqlite3.sqlite_version, rows=len(docs), memory_db_bytes=size,
                full_sqlite_index=measure(full), changed_one_sqlite_index=measure(inc),
                unchanged_one_scan_marker=measure(noop),
                accuracy={key:dict(n=len(rows),**{m:avg([r[m] for r in rows]) for m in rows[0]}) for key,rows in grades.items()})
    write_json('SYNTHETIC_CORPUS_V01.json', dict(docs=docs, aliases=aliases, crosswalk=crosswalk))
    for name in ('dev','holdout'):
        write_json(f'SYNTHETIC_{name.upper()}_V01.json',[q for q in queries if q['split']==name])
    write_json('SYNTHETIC_RESULTS_V01.json',report)
    print(json.dumps(report,ensure_ascii=False,separators=(',',':')))
    db.close()


if __name__=='__main__':
    main()
