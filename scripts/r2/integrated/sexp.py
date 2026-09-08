"""Small lossless-token S-expression utility for KiCad migrations (no library fallback)."""
import re, json, uuid
TOKEN=re.compile(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+')
def parse(s):
 stack=[]; root=None
 for t in TOKEN.findall(s):
  if t=='(':
   a=[]
   if stack:stack[-1].append(a)
   else:root=a
   stack.append(a)
  elif t==')':stack.pop()
  else:stack[-1].append(t)
 assert not stack
 return root
def dump(a,level=0):
 if not isinstance(a,list):return str(a)
 if all(not isinstance(x,list) for x in a):return '('+' '.join(map(str,a))+')'
 out='('; first=True
 for x in a:
  if not first:out+='\n'+'  '*(level+1) if isinstance(x,list) else ' '
  out+=dump(x,level+1);first=False
 return out+')'
def many(a,key):return [x for x in a if isinstance(x,list) and x and x[0]==key]
def one(a,key):
 xs=many(a,key); assert len(xs)==1,(key,len(xs));return xs[0]
def val(v):return json.loads(v) if v.startswith('"') else v
def prop(a,key):return next(val(x[2]) for x in many(a,'property') if val(x[1])==key)
def q(s):return json.dumps(str(s),ensure_ascii=False)
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'smove:integrated:'+str(s)))
def node(s):return parse(s)
def walk(a):
 yield a
 for x in a:
  if isinstance(x,list):yield from walk(x)
