from core import *
from contextlib import closing
base=P/'tests/edge.sqlite'
clean=P/'tests/edge_clean.sqlite'
with closing(ro(base)) as src,closing(sqlite3.connect(clean)) as dst,dst:
 src.backup(dst)
 dst.execute('DELETE FROM ft WHERE rowid IN (SELECT rowid FROM docs WHERE instr(content,char(0))>0)')
 dst.execute('DELETE FROM docs WHERE instr(content,char(0))>0')
al={**cor['aliases'],'short-eval':['가나']}
ts=['가나','가나다','나다라마','abcdef','%_!','"quoted"','한글음절','한글','a\u0301bc','😀가나','a\0needle','edge1.md','제목표본','태그표본','short-eval','before 😀','needle']
r=perform(clean,[dict(id=f'XC{i:02}',term=t,scope='all') for i,t in enumerate(ts)],al,cor['crosswalk'],'edge_clean')[0]
nul=P/'tests/edge_nul_fields.sqlite';shutil.copyfile(clean,nul)
with closing(sqlite3.connect(nul)) as db,db:
 path='99_EVAL/short\0hidden.md';title='evaldistincttitle'
 n=db.execute('INSERT INTO docs(path,carrier,kind,sz,mtime_ns,sha,status,title,tags,content,scan) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(path,'synthetic','.md',1,1,'','OK',title,'before\0tag','x',1)).lastrowid
 db.execute('INSERT INTO ft(rowid,path,tags,content) VALUES(?,?,?,?)',(n,path+' '+title,'before\0tag','x'))
r+=perform(nul,[dict(id='XN01',term='evaldistincttitle',scope='all')],al,cor['crosswalk'],'edge_nul_fields')[0]
opqs=[{**q,'id':q['id']+'_P2','page':2,'page_size':1} for q in cohort['operating_layer']]
r+=perform(D/'operating.sqlite',opqs,OA,OX,'operating_p2')[0]
save('private/functional_addendum.json',r)
print('ADDENDUM',len(r),[(x['layer'],x['engine'],x['id'],x['diff'],x['missed']) for x in r if not x['equal'] or x['missed']],flush=True)
