#!/usr/bin/python3
"""Exact Samsung characteristics decoded as JSON data; no page JavaScript executed.
Engineering lower screening estimates, NOT manufacturer lot guarantees.
"""
from pathlib import Path
import json,gzip,re,hashlib
ROOT=Path(__file__).resolve().parents[3];D=ROOT/'.cache/verify/electrical';D.mkdir(parents=True,exist_ok=True)
source={
 'CL10A475KO8NNNC':('docs/engineering/sources/raw/samsung-c47-routing.body.gz',4.7,.10,16),
 'CL21A106KAYNNNE':('docs/revision-r2/electrical-completion/evidence/samsung-c106.body.gz',10,.10,25),
 'CL21A226MPQNNNE':('docs/engineering/sources/raw/samsung-c22-routing.body.gz',22,.20,10),
 'CL21A476MQYNNNE':('docs/engineering/sources/raw/samsung-c476-fix.body.gz',47,.20,6.3)}
def curve(part):
 file,_,_,_=source[part];t=gzip.decompress((ROOT/file).read_bytes()).decode();found=[]
 assert 'typical data for design reference only' in t
 for m in re.finditer(r'\{\s*"graphType"\s*:\s*"DCBias"',t):
  d,_=json.JSONDecoder().raw_decode(t[m.start():])
  for ps in d.get('selectPartsList',[]):
   assert ps['partsName']==part[:-1],(ps['partsName'],part)
   found=sorted((float(v['x']),float(v['y'])) for v in ps['chartList'][0]['data'])
 assert found;return found
curves={part:curve(part) for part in source}
def interp(pts,v):
 for (a,b),(c,d) in zip(pts,pts[1:]):
  if a<=v<=c:return b+(d-b)*(v-a)/(c-a)
 raise ValueError(v)
rows=[]
for refs,part,bias,limit,kind,fitted in [
 ('main C1','CL10A475KO8NNNC',5.25,1.,'BQ IN recommendation 1..10uF',True),
 ('main C2 superseded','CL21A106KAYNNNE',4.23,4.7,'BQ BAT recommendation 4.7..47uF',False),
 ('main C13 superseded','CL21A106KAYNNNE',4.5,4.7,'BQ OUT recommendation 4.7..47uF; AP2112 input 1uF',False),
 ('main C2','CL21A476MQYNNNE',4.23,4.7,'BQ BAT recommendation 4.7..47uF',True),
 ('main C13','CL21A476MQYNNNE',4.5,4.7,'BQ OUT recommendation 4.7..47uF; AP2112 input 1uF',True),
 ('main C3','CL21A226MPQNNNE',3.3,1.,'AP2112 stable with 1uF ceramic; no invented ESP bulk minimum',True),
 ('main C3 rail ceiling screen','CL21A226MPQNNNE',3.6,1.,'AP2112 stable with 1uF ceramic',True),
 ('carrier C5','CL10A475KO8NNNC',3.3,1.,'AP2112 input 1uF ceramic',True),
 ('carrier C5 input ceiling','CL10A475KO8NNNC',3.6,1.,'AP2112 input 1uF ceramic',True),
 ('carrier C6','CL10A475KO8NNNC',1.8,1.,'AP2112 stable with 1uF ceramic',True),
 ('carrier C6 conservative ceiling','CL10A475KO8NNNC',1.95,1.,'ICM VDDIO upper limit screen, not LDO regulation target',True)]:
 file,c,tol,rating=source[part];dc=interp(curves[part],bias);typ=c*(1+dc/100);tc=typ*(1-tol)*.85;screen=tc*.9
 rows.append(dict(refs=refs,mpn=part,operating_bias_V=bias,nominal_uF=c,rated_V=rating,initial_tolerance_pct=tol*100,typical_bias_change_pct=round(dc,6),typical_biased_uF=round(typ,6),with_tolerance_and_X5R_uF=round(tc,6),with_10pct_age_allocation_uF=round(screen,6),screen_comparison_uF=limit,requirement=kind,fitted=fitted,pass_screen=screen>=limit))
report={'status':'PASS_ENGINEERING_SCREEN_AFTER_C2_C13_SUBSTITUTION','guaranteed_effective_minimum':False,'rows':rows,
 'method':'Exact base-MPN DCBias curves; final C/E suffix is packaging, verified manufacturer package-code table. Linear interpolation; multiply initial tolerance, 0.85 X5R (-55..85C), then optional 0.90 engineering ageing allocation. No generic voltage-rating derating rule.',
 'requirement_interpretation':'TI SLUS810N Table7-1 recommends nominal IN 1..10uF and BAT/OUT 4.7..47uF; no independent guaranteed DC-biased minimum is specified. Compare derated estimates with the lower recommendation as a conservative sizing check, NOT a fabricated TI stability law. Old 10uF fails even before ageing allocation (4.422/4.189uF). Replace only C2/C13; chosen 47uF is within the recommended nominal upper endpoint. AP2112 primary datasheet page1 stable with 1uF, page2 note4 X5R/X7R recommendation. Do not impose legacy buck/buck-boost targets on this LDO.',
 'limits':['Typical DC-bias graphs are engineering reference, not guaranteed lot/temperature/bias lower envelopes. Product of separate tolerance/TCC/bias effects is a screen, not a combined-stress guarantee.','10% ageing is an explicitly bounded engineering allocation, not a manufacturer guaranteed rate or an unlimited service-life claim.','No additional ESR lower limit is invented: AP2112 explicitly supports ceramic. Startup, load steps, rail noise, charging stability and actual thermal behaviour remain physical commissioning gates.','C1 screen assumes normal USB 5.25V maximum. Existing accepted design provides no high-voltage or surge qualification.','47uF upper nominal recommendation is not an absolute maximum; tolerance can exceed nominal. Source and package dimensions verified; power-up current and output dynamics remain physical tests.'],
 'sources':{part:{'archive':v[0],'sha256':hashlib.sha256((ROOT/v[0]).read_bytes()).hexdigest(),'url':'https://product.samsungsem.com/mlcc/'+part[:-1]+'.do'} for part,v in source.items()}}
assert all(r['pass_screen'] for r in rows if r['fitted'])
(D/'capacitance.json').write_text(json.dumps(report,indent=2)+'\n')
for r in rows:print(r['refs'],r['with_tolerance_and_X5R_uF'],r['with_10pct_age_allocation_uF'],'PASS' if r['pass_screen'] else 'REPLACED')
