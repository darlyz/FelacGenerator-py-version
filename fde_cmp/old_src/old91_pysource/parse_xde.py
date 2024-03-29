'''
 Copyright: Copyright (c) 2019
 Created: 2019-3-30
 Author: Zhang_Licheng
 Title: parse the xde file and check it
 All rights reserved
'''
from colorama import init, Fore, Back, Style
init(autoreset=True)
Error_color = Fore.MAGENTA
Warnn_color = Fore.CYAN
Empha_color = Fore.GREEN

import re
from genxde import gen_obj, ifo_folder

pre_check = 0
sec_check = 0

def parse_xde(ges_info, xde_dict, xde_addr, xdefile):

    pre_parse(ges_info, xde_dict, xde_addr, xdefile)
    
    if gen_obj['check'] > 0:
        from check_xde import check_xde
        error = check_xde(ges_info, xde_dict, xde_addr)
        if error :
            return error
     
    sec_parse(ges_info, xde_dict, xde_addr)

    return False

def pre_parse(ges_info, xde_dict, xde_addr, xdefile):

    # all the xde keys
    key_pattern  = r'ARRAY|COEF|COOR|COMMON|DAMP' \
                 + r'|DEFI|DISP|DIST|END|USERC|' \
                 + r'FUNC|FVECT|FMATR|GAUS|LOAD|' \
                 + r'MATE|MASS|MATRIX|SHAP|STIF|VECT|' \
                 + r'\$C[CPV6]|\$I|@[LAWSR]'

    keywd_tag = {'bf_matrix'   : '', \
                 'matr_dclr'   : 0, \
                 'paragraph'   : 'BFmate',\
    }

    line_i = 0
    stitchline = ''
    xde_dict['code'] = {}
    xde_addr['code'] = {}

    # parsing while read xde to xde_dict
    for line in xdefile.readlines():
        line_i += 1

        # skip comment line and blank line
        if re.match(r'\s*(\$c[c6])?\s*((\\|//).*)?\s*\n',line,re.I) != None:
            continue

        # deal with valid sentence with comment
        # identify comment and stitch the next line begin with '\'
        line = stitchline + line
        if line.find('\\') != -1 :
            stitchline = line.split('\\')[0]
            continue
        else: stitchline = ''

        # identify comment begin with '//'
        if line.find('//') != -1:
            line = line.split('//')[0]

        # pop the space from head and tail
        line = line.strip()

        # retrieve the keywords
        matched_key = re.match(key_pattern, line, re.I)

        # find the keyword at the head
        if matched_key != None:

            key_lower = matched_key.group().lower()

            # match and pop to xde_dict
            if key_lower in ['disp','coef','coor','gaus']:
                push_key_declaration(key_lower, line_i, line, xde_dict, xde_addr)

            elif key_lower == 'mate':

                if keywd_tag['paragraph'] != 'BFmate':
                    print(f"{Error_color}Error NSN02, : if other " \
                        + "paragraph is writed before definition, " \
                        + "key word 'DEFI' should not be ommited before " \
                        + "'MATE' line and C insertion for 'MATE'.\n")

                push_key_declaration('mate', line_i, line, xde_dict, xde_addr)
                keywd_tag['paragraph'] = 'AFmate'

            elif key_lower == 'vect':
                push_tonser_declaration('vect', line_i, line, xde_dict, xde_addr)
                if line.find('|') != -1:
                    xde_dict['cmplx_tag'] = 1

            elif key_lower in ['fmatr','fvect']:
                push_tonser_declaration(key_lower, line_i, line, xde_dict, xde_addr)

            elif key_lower.find('$')!= -1 \
            or   key_lower.find('@')!= -1:
                line = line \
                       .replace('%1',ges_info['shap_form']) \
                       .replace('%2',ges_info['shap_nodn'])

                push_workflow_code(line_i, line, keywd_tag, xde_dict, xde_addr)

                if key_lower == '$cp':
                    xde_dict['cmplx_tag'] = 1

            elif key_lower in ['common','array']:

                line = line \
                    .replace('%1',ges_info['shap_form']) \
                    .replace('%2',ges_info['shap_nodn'])

                push_workflow_code(line_i, line, keywd_tag, xde_dict, xde_addr)

                if key_lower == 'array':
                    if 'array' not in xde_dict:
                        xde_dict['array'] = []
                    xde_dict['array'].append(line)

            elif key_lower in ['mass','damp','stif']:
                push_weak_declaration(key_lower, line_i, line, keywd_tag, xde_dict, xde_addr)

            elif key_lower == 'shap':

                if 'shap' not in xde_dict:
                    xde_addr['shap'] = []
                    xde_dict['shap'] = []

                xde_addr['shap'].append(line_i)
                xde_dict['shap'].append(line.split()[1:])

            elif key_lower == 'dist':

                if line.find('|') != -1:
                    xde_dict['cmplx_tag'] = 1

                if keywd_tag['paragraph'] in ['mass','damp','stif']:
                    xde_dict[keywd_tag['paragraph']].append('dist')
                    xde_dict[keywd_tag['paragraph']].append(line.split('=')[1].strip())
                    xde_addr[keywd_tag['paragraph']].append(line_i)

            elif key_lower == 'load':

                if line.find('|') != -1:
                    xde_dict['cmplx_tag'] = 1

                if not 'load' in xde_dict:
                    xde_dict['load'] = []
                    xde_addr['load'] = []

                if line.find('=') != -1:
                    xde_dict['load'].append(line.split('=')[1].strip())
                    xde_addr['load'].append(line_i)
                    keywd_tag['paragraph'] = 'load'

                else:
                    load_list = line.rstrip().split()[1:]
                    xde_dict['load'].append(str(len(load_list)))
                    xde_dict['load'] += load_list
                    xde_addr['load'].append(line_i)

            elif key_lower == 'func':

                wordlist = line.split()

                if len(wordlist) != 1:
                    if not 'func' in xde_dict:
                        xde_dict['func'] = []
                    keywd_tag['func'] = 1
                    xde_dict['func'] += wordlist[1:]

                else:
                    keywd_tag['paragraph'] = 'func'

            elif key_lower == 'matrix':

                push_tonser_declaration('matrix', line_i, line, xde_dict, xde_addr)
                matrix_name = line.split()[1]
                line_num    = xde_addr['matrix'][matrix_name]
                xde_addr['matrix'][matrix_name] = []
                xde_addr['matrix'][matrix_name].append(line_num)
                
                # tackle that code line write between matrix and other paragraph
                if  keywd_tag['matr_dclr'] == 0:
                    keywd_tag['matr_dclr'] = 1
                    keywd_tag['bf_matrix'] = keywd_tag['paragraph']

                keywd_tag['paragraph'] = 'matrix'

            elif key_lower == 'defi':
                keywd_tag['paragraph'] = 'BFmate'

            elif key_lower == 'end':
                pass

            elif key_lower == 'userc':
                pass

        # find the non-keyword-head line in 'func' 'stif' 'mass' and 'damp' paragraph
        else:

            # find cmplx_tag tag
            if line.find('|') != -1:
                xde_dict['cmplx_tag'] = 1

            paragraph_key = keywd_tag['paragraph']

            # find weak form and disp var deform in non-keyword-head line
            if  paragraph_key in ['mass','damp','stif','load'] \
            and paragraph_key in xde_dict:

                if line.rstrip().lower() == 'null':
                    xde_dict[paragraph_key].append(line.rstrip())
                    xde_addr[paragraph_key].append(line_i)

                else:
                    xde_dict[paragraph_key].append(line)
                    xde_addr[paragraph_key].append(line_i)

            elif  paragraph_key == 'func':
                xde_dict['code'][paragraph_key].append(line)
                xde_addr['code'][paragraph_key].append(line_i)

            elif paragraph_key == 'matrix' :
                xde_dict['matrix'][matrix_name].append(line)
                xde_addr['matrix'][matrix_name].append(line_i)

            else:
                print(f'{Warnn_color}Warn NSN03: redundant information ' \
                     + 'or wrong declare, line {line_i}: ' + line)

    if pre_check == 1:
        import json

        file = open(ifo_folder + 'pre_check.json', mode='w')
        file.write(json.dumps(xde_dict,indent=4))
        file.close()

        file = open(ifo_folder + 'pre_addr.json',  mode='w')
        file.write(json.dumps(xde_addr,indent=4))
        file.close()
# end pre_parse()

# push key declaration: DISP, COEF, COOR, GAUS, MATE
def push_key_declaration(keywd, line_num, line, xde_dict, xde_addr):

    if keywd in xde_dict:
        print(f'{Warnn_color}Warn NSN04: line {Empha_color}' \
             +f'{line_num}, {keywd} {Warnn_color}has been declared ' \
             +f'at line {Empha_color}{xde_addr[keywd]}\n')

    else:
        line = line.replace(',',' ').replace(';',' ')
        xde_addr[keywd] = line_num
        xde_dict[keywd] = line.split()[1:]

# push tensor declaration: VECT, FMATR, FVECT
def push_tonser_declaration(keywd, line_num, line, xde_dict, xde_addr):

    if keywd not in xde_dict: 
        xde_dict[keywd] = {}
        xde_addr[keywd] = {}

    line = re.sub(r'\s*=\s*',' ',line)
    wordlist = line.split()
    xde_addr[keywd][wordlist[1]] = line_num
    xde_dict[keywd][wordlist[1]] = wordlist[2:]

# push workflow code line : @*, $C*
def push_workflow_code(line_num, line, keywd_tag, xde_dict, xde_addr):
    code_find = 0
    paragraph_key = keywd_tag['paragraph']

    # tackle that code line write between matrix and other paragraph
    if paragraph_key == 'matrix':
        paragraph_key = keywd_tag['bf_matrix']

    if paragraph_key in ['BFmate','AFmate','func','stif','mass','damp']:

        code_find = 1

        if paragraph_key not in xde_dict['code']:
            xde_dict['code'][paragraph_key] = []
            xde_addr['code'][paragraph_key] = []

        xde_dict['code'][paragraph_key].append(line)
        xde_addr['code'][paragraph_key].append(line_num)

    if code_find == 0:
        print(f'{Error_color}Error NSN05: line {line_num}, ' \
            + 'wrong position inserted.\n')

# push weak expression declaration: STIF, MASS, DAMP
def push_weak_declaration(keywd, line_num, line, keywd_tag, xde_dict, xde_addr):

    if keywd in xde_dict:
        print(f'{Error_color}Error NSN06: line {Empha_color}' \
            + f'{line_num}, {keywd} {Error_color}has been declared ' \
            + f'at line {Empha_color}{xde_addr[keywd][0]}.\n')

    else:
        xde_addr[keywd] = []
        xde_dict[keywd] = []
        wordlist = line.split()

        if len(wordlist) > 1:
            xde_addr[keywd].append(line_num)
            xde_dict[keywd] = wordlist[1:]

        else:
            keywd_tag['paragraph'] = keywd

def sec_parse(ges_info, xde_dict, xde_addr):

    # parse disp and func for complex
    if 'cmplx_tag' in xde_dict and xde_dict['cmplx_tag'] == 1:

        for keywd in ['disp', 'func']:
            
            if keywd in xde_dict:

                xde_dict[f'cmplx_{keywd}'] = xde_dict[keywd].copy()
                xde_dict[keywd].clear()

                for strs in xde_dict[f'cmplx_{keywd}']:
                    xde_dict[keywd].append(strs+'r')
                    xde_dict[keywd].append(strs+'i')

    # parse array declaration
    if 'array' in xde_dict:
        array_declare_list = xde_dict['array'].copy()
        xde_dict['array'].clear()
        xde_dict['array'] = {}
        for array_strs in array_declare_list:
            array_list = re.findall(r'\^?\w+(?:\[\d+\]){1,2}', array_strs)
            for array in array_list:
                var = array.split('[')[0].lstrip('^')
                index_list = list(map(lambda x: x.lstrip('[').rstrip(']') , re.findall(r'\[\d+\]', array)))
                xde_dict['array'][var] = index_list

    if 'shap' in xde_dict:
        parse_shap_declaration(ges_info, xde_dict)

    if 'mate' in xde_dict:
        parse_mate_declaration(xde_dict)


    if 'gaus' in xde_dict:

        if xde_dict['gaus'][0] == '%3':
            xde_dict['gaus'] = ges_info['gaus_type']

        else:
            xde_dict['gaus'] = xde_dict['gaus'][0]


    if 'mass' in xde_dict:

        if  xde_dict['mass'][0] == '%1':
            xde_dict['mass'][0] = 'lump'

        if  len(xde_dict['mass']) == 1:
            xde_dict['mass'].append('1.0')


    if 'damp' in xde_dict:

        if  xde_dict['damp'][0] == '%1':
            xde_dict['damp'][0] = 'lump'

        if  len(xde_dict['damp']) == 1:
            xde_dict['mass'].append('1.0')


    # initial to empty string list
    if 'fvect' in xde_dict:

        for lists in xde_dict['fvect'].values():

            if len(lists) == 0:
                lists.append('1')

            if len(lists) == 1:
                lists += ['' for ii in range(int(lists[0]))]

    # initial to empty string list
    if 'fmatr' in xde_dict:

        for lists in xde_dict['fmatr'].values():

            if len(lists) == 0:
                lists += ['1','1']

            if len(lists) == 2:
                lists += [['' for ii in range(int(lists[1]))] \
                              for ii in range(int(lists[0]))]

    # insert vector lenth at head
    if 'vect' in xde_dict:
        for lists in xde_dict['vect'].values():
            if not lists[0].isnumeric():
                lists.insert(0,str(len(lists)))

    # insert row and colum scale if not declared
    if 'matrix' in xde_dict:

        for lists in xde_dict['matrix'].values():

            if  not lists[0].isnumeric() \
            and not lists[1].isnumeric() :
                row = len(lists)
                clm = len(lists[0].split())
                lists.insert(0,str(clm))
                lists.insert(0,str(row))

            else: 
                row = int(lists[0])

            for ii in range(row):
                lists[ii+2] = lists[ii+2].split()

    # parse 'line' form 'load' declaration
    if 'load' in xde_dict:
        if xde_dict['load'][0].isnumeric():
            xde_dict['load'] \
                = ['+[' + xde_dict['disp'][i] + ']*' + xde_dict['load'][i+1] \
                    for i in range(int(xde_dict['load'][0]))]


    # parsing workflow code
    parse_workflow_code(xde_dict)

    if sec_check == 1:
        import json
        file = open(ifo_folder+'sec_check.json',mode='w')
        file.write(json.dumps(xde_dict,indent=4))
        file.close()
# end sec_parse()

def parse_shap_declaration(ges_info, xde_dict):
    shap_dict = {}

    # 3.1.1 common shap (maybe user declare twice or more, so the last active)
    for shap_list in xde_dict['shap']:

        if len(shap_list) == 2:

            if  shap_list[0] == '%1': 
                shap_list[0] = ges_info['shap_form']

            if  shap_list[1] == '%2': 
                shap_list[1] = ges_info['shap_nodn']

            base_shap_type = shap_list[0] + shap_list[1]
            shap_dict[base_shap_type] = xde_dict['disp'].copy()

            if 'coef' in xde_dict:
                xde_dict['coef_shap'] = {}
                xde_dict['coef_shap'][base_shap_type] = xde_dict['coef'].copy()

    # 3.1.2 penalty or mix shap
    for shap_list in xde_dict['shap']:

        if len(shap_list) >= 3:

            if  shap_list[0] == '%1':
                shap_list[0] = ges_info['shap_form']

            if  shap_list[1] == '%4' \
            or  shap_list[1].isnumeric():

                var_list  = shap_list[2:]
                disp_find_n = len(set(var_list)&set(xde_dict['disp']))
                
                coef_find_n = 0
                if 'coef' in xde_dict:
                    coef_find_n = len(set(var_list)&set(xde_dict['coef']))

                if (disp_find_n > 0 or coef_find_n > 0) \
                and shap_list[1] == '%4':

                    if   base_shap_type == 't6' : 
                        shap_list[1] = '3'

                    elif base_shap_type == 'q9' : 
                        shap_list[1] = '4'

                    elif base_shap_type == 'w10': 
                        shap_list[1] = '4'

                    elif base_shap_type == 'c27': 
                        shap_list[1] = '8'

                    subs_shap_type = shap_list[0] + shap_list[1]

                if disp_find_n > 0:
                    if subs_shap_type not in shap_dict:
                        shap_dict[subs_shap_type] = []

                if coef_find_n > 0:
                    if subs_shap_type not in xde_dict['coef_shap']:
                        xde_dict['coef_shap'][subs_shap_type] = []

                for var_name in var_list:

                    if var_name.isnumeric():
                        continue

                    if 'coef' not in xde_dict:
                        if var_name not in xde_dict['disp'] :
                            continue

                    else:
                        if  var_name not in xde_dict['disp'] \
                        and var_name not in xde_dict['coef'] :
                            continue

                    if var_name in shap_dict[base_shap_type]:
                        shap_dict[base_shap_type].remove(var_name)
                        shap_dict[subs_shap_type].append(var_name)

                    if 'coef_shap' in xde_dict:

                        if var_name in xde_dict['coef_shap'][base_shap_type]:
                            xde_dict['coef_shap'][base_shap_type].remove(var_name)
                            xde_dict['coef_shap'][subs_shap_type].append(var_name)

            elif shap_list[1] == '%2c' \
            or  (shap_list[1][-1].lower() == 'c' \
                and shap_list[1][:-1].isnumeric) :

                var_list = shap_list[2:]

                pena_vars = {}
                for var_name in var_list:

                    if var_name.isnumeric(): 
                        continue

                    if var_name.find('_'):
                        var_name, pan_name = var_name.split('_')[:2]

                    pena_vars[var_name] = pan_name

                shap_list[1]   = shap_list[1].replace('%2',ges_info['shap_nodn'])
                subs_shap_type = shap_list[0] + shap_list[1]

                if subs_shap_type not in shap_dict:
                    shap_dict[subs_shap_type] = pena_vars

                for pena_var in pena_vars.keys() :
                    shap_dict[base_shap_type].remove(pena_var)

    xde_dict['shap'] = shap_dict
# end parse_shap_declaration()

def parse_mate_declaration(xde_dict):

    mate_dict = {}
    mate_dict['default'] = {}
    mate_var = []
    mate_val = []

    for strs in xde_dict['mate']:

        if re.match(r'[a-z]\w*', strs, re.I) == None :
            mate_val.append(strs)

        else:
            mate_var.append(strs)

    for var_i, var in enumerate(mate_var):

        if var_i < len(mate_val):
            mate_dict['default'][var] = mate_val[var_i]

        else:
            mate_dict['default'][var] = '0.0'

    xde_dict['mate'] = mate_dict
# end parse_mate_declaration()

def parse_workflow_code(xde_dict):

    regx_key = r'\$C[CPV6]|@[LAWSR]|ARRAY'

    for code_place in xde_dict['code'].keys():
        for code_i, code_line in enumerate(xde_dict['code'][code_place]):
            code_regx = re.match(regx_key,code_line,re.I)

            if code_regx == None:
                # say something
                continue

            code_key = code_regx.group()

            if   code_key.lower() == '$cc' \
            or   code_key.lower() == '$c6':
                xde_dict['code'][code_place][code_i] \
                    = 'Insr_Code: ' + code_line.replace(code_key,'').lstrip()

            elif code_key.lower() == '$cv':
                xde_dict['code'][code_place][code_i] \
                    = 'Tnsr_Asgn: ' + code_line.replace(code_key,'').lstrip()

            elif code_key.lower() == '$cp':
                xde_dict['code'][code_place][code_i] \
                    = 'Cplx_Asgn: ' + code_line.replace(code_key,'').lstrip()

            # 3.6.2 parsing operator
            elif code_key.lower() == '@l':

                opr_list = code_line.replace(code_key,'').lstrip().split()
                opr_expr = opr_list[0]
                opr_name = opr_expr.split('.')[0]
                asgn_type = opr_list[1].lower()

                var_prefxs = ['',  '',   '',     '[']
                var_posfxs = ['',  '_i', '_i_j', ']']
                asgn_types = ['c', 'v',  'm',    'f']

                if asgn_type == 'n':

                    if   opr_name.lower() == 'singular':
                        xde_dict['code'][code_place][code_i] \
                            = 'Oprt_Asgn: '+opr_expr

                    elif opr_name.lower() == 'vol':
                        xde_dict['code'][code_place][code_i] \
                            = 'Oprt_Asgn: '+opr_expr

                elif asgn_type in asgn_types:

                    type_indx = asgn_types.index(asgn_type)
                    prefx_str = var_prefxs[type_indx]
                    posfx_str = var_posfxs[type_indx]

                    if asgn_type == 'f':

                        if   'fvect' in xde_dict \
                        and opr_list[2] in xde_dict['fvect']:
                            posfx_str = '_i'   + posfx_str

                        elif 'fmatr' in xde_dict \
                        and opr_list[2] in xde_dict['fmatr']:
                            posfx_str = '_i_j' + posfx_str

                    temp_str  = 'Oprt_Asgn: ' \
                              + prefx_str + opr_list[2] + posfx_str \
                              + '=' + opr_expr + '(' \
                              + ','.join(opr_list[3:]) + ')'

                    xde_dict['code'][code_place][code_i] = temp_str

            # 3.6.3 parsing assignment
            elif code_key.lower() == '@a':
                expr = code_line.replace(code_key,'').lstrip().split('=')
                xde_dict['code'][code_place][code_i] \
                    = 'Func_Asgn: [' + expr[0].rstrip() \
                    + ']=' + expr[1].lstrip()

            elif code_key.lower() == '@r':
                expr = code_line.replace(code_key,'').lstrip().split('=')
                xde_dict['code'][code_place][code_i] \
                    = 'Func_Asgn: [' + expr[0].rstrip() \
                    + ']=' + expr[1].lstrip().replace('[','').replace(']','')

            elif code_key.lower() in ['@w','@s']:
                opr_list = code_line.replace(code_key,'').lstrip().split()
                temp_str = 'Func_Asgn: '

                for strs, prefx, posfx \
                in zip(['vect', 'matrix', 'fvect', 'fmatr' ], \
                       ['',     '',       '[',     '['     ],
                       ['_i=',  '_i_j=',  '_i]=',  '_i_j]=']) :

                    if strs in xde_dict \
                    and opr_list[0] in xde_dict[strs]:
                        prefx_str, posfx_str = prefx, posfx

                temp_str += prefx_str + opr_list[0] + posfx_str

                temp_str += opr_list[1] + '[' + ','.join(opr_list[2:]) + ']'

                xde_dict['code'][code_place][code_i] = temp_str

            elif code_key.lower() == 'array':

                var_list = code_line.replace(code_key,'').strip().split(',')
                temp_str = 'Insr_Code: double '

                for var_strs in var_list:
                    var_name = var_strs.strip().split('[')[0]
                    idx_list = re.findall(r'\[\d+\]',var_strs,re.I)

                    if len(idx_list) == 1:
                        vect_len = idx_list[0].lstrip('[').rstrip(']')

                        if 'vect' not in xde_dict : 
                            xde_dict['vect'] = {}

                        xde_dict['vect'][var_name]  = [vect_len] \
                            + [var_name + '[' + str(ii+1) + ']' \
                                for ii in range(int(vect_len))]

                        var_strs = var_name + '[' + str(int(vect_len)+1) +']'

                    elif len(idx_list) == 2:

                        matr_row = idx_list[0].lstrip('[').rstrip(']')
                        matr_clm = idx_list[1].lstrip('[').rstrip(']')

                        if 'matrix' not in xde_dict :
                            xde_dict['matrix'] = {}

                        xde_dict['matrix'][var_name] = [matr_row, matr_clm] \
                            + [[var_name+'['+str(ii+1)+']['+str(jj+1)+']' \
                                for jj in range(int(matr_clm))] \
                                    for ii in range(int(matr_row))]

                    temp_str += var_strs + ','
                    
                xde_dict['code'][code_place][code_i] = temp_str.rstrip(',') +';'
# end parse_workflow_code()