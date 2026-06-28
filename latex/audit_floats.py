import re, os
aux = open('main.aux', encoding='utf8', errors='ignore').read()
flo = {}
for m in re.finditer(r'\\newlabel\{(fig:[^}]*|tab:[^}]*)\}\{\{([^}]*)\}\{([^}]*)\}', aux):
    lbl, num, pg = m.group(1), m.group(2), m.group(3)
    if lbl not in flo:
        flo[lbl] = (num, int(pg) if pg.isdigit() else pg)
sec = {}
for m in re.finditer(r'\\newlabel\{(sec:[^}]*)\}\{\{([^}]*)\}\{([^}]*)\}', aux):
    sec[m.group(1)] = (m.group(2), int(m.group(3)) if m.group(3).isdigit() else m.group(3))

firstref = {
 'tab:rw_comparison': 'sec:bg_problem', 'fig:architecture': 'sec:intro',
 'tab:encoding': 'sec:encoding', 'fig:lowering': 'sec:encoding', 'tab:lowering': 'sec:encoding',
 'tab:footprint': 'sec:mvm_arch', 'tab:inst_set': 'sec:safety', 'fig:fsm': 'sec:closed_loop',
 'fig:forest_rates': 'sec:setup', 'fig:compression': 'sec:res_e1', 'tab:energy': 'sec:res_energy',
 'fig:ablation': 'sec:res_e2', 'tab:fuzzing': 'sec:res_fuzzing', 'tab:system_ablation': 'sec:ablation_system',
 'tab:temperature': 'sec:res_temperature', 'fig:closed_loop': 'sec:res_e4', 'tab:realworld': 'sec:res_realworld',
 'tab:grammar_constrained': 'sec:res_grammar', 'fig:gen_token': 'sec:res_grammar',
 'tab:gen_results': 'sec:setup', 'tab:app_control_flow': 'sec:res_grammar', 'tab:app_model_compare': 'sec:pipeline',
 'tab:app_json_baseline': 'sec:encoding', 'tab:app_random_percat': 'sec:res_random',
 'tab:app_realworld_percat': 'sec:res_realworld', 'fig:scal_length': 'sec:scalability',
 'fig:scal_devices': 'sec:scalability', 'fig:scal_steps': 'sec:scalability', 'tab:full_isa': 'sec:formal_scope',
}
order = ['tab:rw_comparison','fig:architecture','tab:encoding','fig:lowering','tab:lowering',
 'tab:footprint','tab:inst_set','fig:fsm','fig:forest_rates','fig:compression','tab:energy',
 'fig:ablation','tab:fuzzing','tab:system_ablation','tab:temperature','fig:closed_loop','tab:realworld',
 'tab:grammar_constrained','fig:gen_token','tab:gen_results','tab:app_control_flow','tab:app_model_compare',
 'tab:app_json_baseline','tab:app_random_percat','tab:app_realworld_percat','fig:scal_length',
 'fig:scal_devices','fig:scal_steps','tab:full_isa']

print("found floats:", len(flo), " sections:", len(sec))
print(f"{'num':7} {'label':24} {'fPg':4} {'refSec':16} {'rPg':4} {'gap':4} verdict")
for l in order:
    if l not in flo:
        print("MISSING", l); continue
    num, fp = flo[l]; rs = firstref.get(l, '?'); rp = sec.get(rs, ('?', '?'))[1]
    kind = 'Fig' if l.startswith('fig') else 'Tab'
    gap = (fp - rp) if isinstance(fp, int) and isinstance(rp, int) else '?'
    v = ('*** BEFORE REF ***' if (gap != '?' and gap < 0) else 'same-pg' if gap == 0
         else '+1 ok' if gap == 1 else (f'+{gap} CHECK' if gap != '?' else '?'))
    print(f"{kind+str(num):7} {l:24} {str(fp):4} {rs.replace('sec:',''):16} {str(rp):4} {str(gap):4} {v}")
