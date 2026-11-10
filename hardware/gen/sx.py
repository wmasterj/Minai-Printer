import re
TOK = re.compile(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+')
def parse(text):
    stack=[[]]
    for t in TOK.findall(text):
        if t=='(':
            l=[]; stack[-1].append(l); stack.append(l)
        elif t==')': stack.pop()
        else: stack[-1].append(t)
    return stack[0][0]
def dump(x, ind=0):
    if isinstance(x,str): return x
    simple = all(isinstance(i,str) for i in x)
    if simple or len(dump_flat(x))<100: return dump_flat(x)
    pad='\t'*(ind+1)
    head=[]; i=0
    while i<len(x) and isinstance(x[i],str): head.append(x[i]); i+=1
    s='('+' '.join(head)
    for it in x[i:]:
        s+='\n'+pad+dump(it,ind+1)
    return s+'\n'+'\t'*ind+')'
def dump_flat(x):
    if isinstance(x,str): return x
    return '('+' '.join(dump_flat(i) for i in x)+')'
def q(s): return '"'+str(s).replace('\\','\\\\').replace('"','\\"')+'"'
def uq(s): return s[1:-1].replace('\\"','"').replace('\\\\','\\') if s.startswith('"') else s
