'''
 Copyright: Copyright (c) 2019
 Created: 2019-4-15
 Author: Zhang_Licheng
 Title: generate the dict data to ges gesfile
 All rights reserved
'''
import re as regx
import os,math
from expr import idx_summation,cmplx_expr,split_bracket_expr,expr

def xde2ges(ges_info, xde_lists, list_addr, gesfile):

    pfelacpath = os.environ['pfelacpath']

    # use to deal with @L, @A, vol, singular, ...
    code_use_dict = {}
    for code_key in ['BFmate','AFmate','func','stif','mass','damp']:
        if code_key in xde_lists['code']:
            code_use_dict[code_key] = []
            release_code(xde_lists, code_key, pfelacpath, code_use_dict)

    # 1 write disp and var declare
    if 'disp' in xde_lists:
        write_disp_var(ges_info, xde_lists, gesfile)

    # 2 write refc, coor and coef declare
    if 'coor' in xde_lists:
        gesfile.write('\nrefc ')
        for strs in xde_lists['coor']: gesfile.write('r'+strs+',')
        gesfile.write('\ncoor ')
        for strs in xde_lists['coor']: gesfile.write(strs+',')

    if 'coef' in xde_lists:
        gesfile.write('\ncoef ')
        for strs in xde_lists['coef']: gesfile.write(strs+',')

    # 3 write func declare
    if 'func' in xde_lists:
        gesfile.write('\nfunc = ')
        for strs in xde_lists['func']: gesfile.write(strs+',')

    # 4 write dord and node declare
    if 'disp' in xde_lists:
        gesfile.write('\ndord ')
        for strs in xde_lists['disp']: gesfile.write('1'+',')
        gesfile.write('\nnode '+str(ges_info['shap_nodn'])+'\n')

    # 5 write code before mate declaration
    if 'BFmate' in code_use_dict:
        for strs in code_use_dict['BFmate']: gesfile.write(strs)

    # 6 write mate line
    if 'mate' in xde_lists:
        gesfile.write('mate')
        for var in xde_lists['mate']['default'].keys():
            gesfile.write(' '+var)
        for var in xde_lists['mate']['default'].keys():
            gesfile.write(' '+xde_lists['mate']['default'][var])
        gesfile.write('\n')

    # 7 write code after mate declaration
    if 'AFmate' in code_use_dict:
        for strs in code_use_dict['AFmate']: gesfile.write(strs)

    # 8 write 'singular' operator declaration
    if 'singular' in xde_lists:
        gesfile.write(xde_lists['singular'])

    # 9 write shap and tran paragraph
    if 'shap' in xde_lists:
        write_shap_tran(pfelacpath, ges_info, xde_lists, gesfile)

    # 9.3 write coef shap
    if 'coef_shap' in xde_lists:
        write_coefshap(pfelacpath, ges_info, xde_lists, gesfile)

    # 9 write gaus paragraph
    if 'gaus' in xde_lists:
        write_gaus(pfelacpath, ges_info, xde_lists, gesfile)

    # 10 write func paragraph
    if 'func' in code_use_dict or 'vol'  in xde_lists :
        write_func(code_use_dict, xde_lists, gesfile)

    # 11 write stif, mass, damp paragraph
    for weak in ['stif', 'mass', 'damp']:
        if weak in xde_lists:
            write_weak(weak, code_use_dict, xde_lists, gesfile)

    # 14 write load paragraph
    if 'load' in xde_lists:
        write_load(xde_lists, gesfile)

    gesfile.write('\nend')

    gesfile.close()

    return False
# end xde2ges()

def release_code(xde_lists, code_place, pfelacpath, code_use_dict):
    
    for code_strs in xde_lists['code'][code_place]:

        code_regx = regx.match(r'Insr|Tnsr|Cplx|Oprt|Func',code_strs,regx.I)

        if code_regx == None: 
            code_use_dict[code_place].append(code_strs+'\n')
            continue

        code_key = code_regx.group()

        # Insert C code
        if  code_key == 'Insr':
            code_use_dict[code_place].append(code_strs.replace('Insr_Code:','$cc')+'\n')

        # Tensor expres summation
        elif code_key == 'Tnsr':
            release_tensor_code(code_strs, code_place, xde_lists, code_use_dict)

        # complex expres expansion
        elif code_key == 'Cplx':
            release_complex_code(code_strs, code_place, xde_lists, code_use_dict)

        # the operator resault assignment
        elif code_key == 'Oprt':
            release_operator_code(code_strs, code_place, pfelacpath, xde_lists, code_use_dict)

        elif code_key == 'Func':
            release_funcasgn_code(code_strs, code_place, xde_lists, code_use_dict)
# end release_code()

def release_tensor_code(code_strs, code_place, xde_lists, code_use_dict):
    vect_expr = code_strs.replace('Tnsr_Asgn: ','')
    left_vara, righ_expr = vect_expr.split('=')[:2]
    left_vara, righ_expr = left_vara.strip(), righ_expr.strip().strip(';')
    expr_list = idx_summation(left_vara, righ_expr, xde_lists)
    for expres in expr_list:
        code_use_dict[code_place].append('$cc '+expres+';\n')
# end release_tensor_code()

def release_complex_code(code_strs, code_place, xde_lists, code_use_dict):
    cplx_expr = code_strs.replace('Cplx_Asgn: ','')
    left_vara, righ_expr = cplx_expr.split('=')[:2]
    left_vara, righ_expr = left_vara.strip(), righ_expr.strip().strip(';')

    # if complex expres is a tensor expres, make summation first
    if left_vara.find('_') != -1 \
    or righ_expr.find('_') != -1 :
        expr_list = idx_summation(left_vara, righ_expr, xde_lists)
        for expres in expr_list:
            cplx_list = expres.split('=')
            cplx_objt = cmplx_expr(cplx_list[1])
            for ri,cmplexpr in zip(['r','i'], cplx_objt.complex_list):
                code_use_dict[code_place] \
                    .append(f'$cc {cplx_list[0]}{ri}={cmplexpr};\n')
    else:
        cplx_objt = cmplx_expr(righ_expr)
        for ri,cmplexpr in zip(['r','i'], cplx_objt.complex_list):
            code_use_dict[code_place] \
                .append(f'$cc {left_vara}{ri}={cmplexpr};\n')
# end release_complex_code()

def release_operator_code(code_strs, code_place, pfelacpath, xde_lists, code_use_dict):
    path_oprt = pfelacpath+'ges/pde.lib'
    file_oprt = open(path_oprt, mode='r')
    oprt_expr = code_strs.replace('Oprt_Asgn: ','')

    # singularity and volume operators
    for oprt_key in ['singular','vol']:
        if oprt_expr.find(oprt_key) != -1:
            
            oprt_strs, oprt_find = '', 0
            for line in file_oprt.readlines():
                oprt_start_file = regx.match('sub '+oprt_expr+r'\(',line, regx.I)
                oprt_end_file   = regx.match('end '+oprt_expr+'\n',line, regx.I)
                if oprt_start_file != None:
                    oprt_find = 1
                    continue
                if oprt_end_file   != None:
                    oprt_find = 0
                    break
                if oprt_find == 1:
                    oprt_strs += line
    
            xde_lists[oprt_key] = oprt_strs

    # other operators as grad, div, curl...
    if  oprt_expr.find('singular') == -1 \
    and oprt_expr.find('vol') == -1 :

        # split aa=grad.xy(x,y,u) to aa, grad.xy, [x,y,u]
        left_vara, righ_expr = oprt_expr.split('=')[:2]
        oprt_name, oprt_vars = righ_expr.split('(')[:2]
        oprt_vars = oprt_vars.rstrip(')').split(',')

        # expand vector variable list [x_i,a_i...] --> [x,y,z,a1,a2,...]
        temp_vars = []
        for vara in oprt_vars:
            if vara.count('_') == 0:
                temp_vars.append(vara)
            elif vara.count('_') == 1:
                vect_name = vara.split('_')[0]
                temp_vars += xde_lists['vect'][vect_name][1:]
            elif vara.count('_') == 2:
                matr_name = vara.split('_')[0]
                for matr_row in xde_lists['matrix'][matr_name][2:]:
                    temp_vars += matr_row
        oprt_vars = temp_vars.copy()

        # find operator in pde.lib
        oprt_strs, oprt_find = '', 0
        for line in file_oprt.readlines():
            oprt_start_file = regx.search('sub '+oprt_name+r'\(',line,regx.I)
            oprt_end_file   = regx.search('end '+oprt_name+'\n',line,regx.I)
            if oprt_start_file != None:
                oprt_find = 1
                # find variables of operator in pde.lib
                temp_vars = line.split('(')[1].rstrip().rstrip(')').split(',').copy()
                continue
            if oprt_end_file   != None:
                oprt_find = 0
                break
            if oprt_find == 1:
                oprt_strs += line

        # replace default variable by operator variable
        if len(oprt_vars) == len(temp_vars):
            for oprt_var, temp_var in zip(oprt_vars, temp_vars):
                oprt_strs = oprt_strs.replace(temp_var,oprt_var)

        # assign to a temporary list type of 'fvect' or 'fmatr' 
        # used for derivative of 'disp' variables in Func_Asgn step
        # Oprt_Asgn: [a] = opr(*,*) ----------- @L opr f a * *
        if  left_vara[0]  == '[' and left_vara[-1] == ']' :
            expr_list = oprt_strs.rstrip().split('\n')

            if left_vara.count('_') == 0: # may be fault tackle
                expres = left_vara.lstrip('[').rstrip(']') + '=' + ''.join(expr_list)
                code_use_dict[code_place].append(expres)

            elif left_vara.count('_') == 1:
                var = left_vara.lstrip('[').rstrip(']').split('_')[0]
                for ii in range(len(expr_list)):
                    xde_lists['fvect'][var][ii+1] = expr_list[ii]

            elif left_vara.count('_') == 2:
                var = left_vara.lstrip('[').rstrip(']').split('_')[0]
                row, clm = list(map(int,xde_lists['fmatr'][var][:2]))
                for ii in range(row):
                    for jj in range(clm):
                        xde_lists['fmatr'][var][ii+2][jj] = expr_list[ii*row+jj]

        # assign to derivative of distributed known variables such as last step 'disp' resault
        # Oprt_Asgn: a = opr(*,*) ----------- @L opr [svm] a * *
        elif left_vara[0]  != '[' and  left_vara[-1] != ']' :
            oprt_strs = oprt_strs.replace('[','{').replace(']','}')
            expr_list = oprt_strs.rstrip().split('\n')

            if left_vara.count('_') == 0:
                expres = left_vara.lstrip('[').rstrip(']') + '=' + ''.join(expr_list)
                code_use_dict[code_place].append('$cv '+expres)

            elif left_vara.count('_') == 1:
                expres = left_vara.lstrip('[').rstrip(']').split('_')[0]
                if len(xde_lists['vect'][expres]) == len(expr_list)+1:
                    for ii in range(len(expr_list)):
                        code_use_dict[code_place] \
                            .append('$cv '+ xde_lists['vect'][expres][ii+1] + '=' + expr_list[ii])

            elif left_vara.count('_') == 2:
                expres = left_vara.lstrip('[').rstrip(']').split('_')[0]
                matr_len = int(xde_lists['matrix'][expres][0]) \
                         * int(xde_lists['matrix'][expres][1])
                if matr_len == len(expr_list):
                    ii = 0
                    for lists in xde_lists['matrix'][expres][2:]:
                        for strs in lists:
                            code_use_dict[code_place].append('$cv '+strs+'='+expr_list[ii]+'\n')
                            ii += 1
    file_oprt.close()
# end release_operator_code()

def release_funcasgn_code(code_strs, code_place, xde_lists, code_use_dict):
    tnsr_expr = code_strs.replace('Func_Asgn: ','')
    left_vara, righ_expr = tnsr_expr.split('=')[:2]
    left_vara, righ_expr = left_vara.strip(), righ_expr.strip()

    # assign the temporary list type of 'fvect' or 'fmatr'
    # to the list type of 'vect' or 'matrix'
    if  left_vara[0]  != '[' and left_vara[-1] != ']' :

        # Func_Asgn: a = b[*,*] --------- @W a b * *
        if regx.search(r'[a-z]+[0-9a-z]*\[([0-9],)*[0-9]?\]',righ_expr,regx.I) != None \
        and righ_expr[-1] == ']':

            # read right variable index list
            righ_vara = righ_expr.split('[')[0]
            if righ_expr[-1] == ']' and righ_expr[-2] == '[':
                
                if   'fvect' in xde_lists and righ_vara in xde_lists['fvect']:
                    righ_idxs = list(range(int(xde_lists['fvect'][righ_vara][0])))
                
                elif 'fmatr' in xde_lists and righ_vara in xde_lists['fmatr']:
                    righ_idxs = list(range(int(xde_lists['fvect'][righ_vara][0]) \
                                          *int(xde_lists['fvect'][righ_vara][1])))
                
                righ_idxs = [x + 1 for x in righ_idxs]
            else:
                righ_idxs = righ_expr.split('[')[1].rstrip(']').split(',')

            if left_vara.count('_') == 0:
                expres = left_vara + '='

                if   'fvect' in xde_lists and righ_vara in xde_lists['fvect']:
                    for idx in righ_idxs:
                        expres += xde_lists['fvect'][righ_vara][int(idx)]
                
                elif 'fmatr' in xde_lists and righ_vara in xde_lists['fmatr']:
                    row, clm = list(map(int,xde_lists['fmatr'][righ_vara][:2]))
                    fmatr = xde_lists['fmatr'][righ_vara][2:]
                    for idx in righ_idxs:
                        expres += fmatr[math.ceil(int(idx)/clm)-1][int(idx)%clm-1]
                
                code_use_dict[code_place].append(expres+'\n\n')
            
            elif left_vara.count('_') == 1: 
                left_name = left_vara.split('_')[0]
                expr_list = []
                temp_list = xde_lists['vect'][left_name][1:].copy()

                if len(temp_list) == len(righ_idxs):

                    if   'fvect' in xde_lists and righ_vara in xde_lists['fvect']:
                        for vara, idx in zip(temp_list, righ_idxs):
                            expr_list.append(vara+'='+xde_lists['fvect'][righ_vara][int(idx)]+'\n\n')
                    
                    elif 'fmatr' in xde_lists and righ_vara in xde_lists['fmatr']:
                        row,clm = list(map(int,xde_lists['fmatr'][righ_vara][:2]))
                        fmatr   = xde_lists['fmatr'][righ_vara][2:len(xde_lists['fmatr'][righ_vara])]
                        for vara,idx in zip(temp_list,righ_idxs):
                            expr_list.append(vara+'='+fmatr[math.ceil(int(idx)/clm)-1][int(idx)%clm-1]+'\n\n')
                
                code_use_dict[code_place] += expr_list

            elif left_vara.count('_') == 2:
                left_name = left_vara.split('_')[0]
                expr_list = []
                matr_len = int(xde_lists['matrix'][left_name][0]) \
                         * int(xde_lists['matrix'][left_name][1])

                temp_list = xde_lists['matrix'][left_name][2:].copy()

                if matr_len == len(righ_idxs):
                    if 'fvect' in xde_lists and righ_vara in xde_lists['fvect']:
                        idx = 0
                        for lists in temp_list:
                            for vara in lists:
                                idx+=1
                                expr_list.append(vara+'='+xde_lists['fvect'][righ_vara][idx]+'\n\n')

                elif 'fmatr' in xde_lists and righ_vara in xde_lists['fmatr']:
                    fmatr = xde_lists['fmatr'][righ_vara][2:len(xde_lists['fmatr'][righ_vara])]
                    i = 0
                    for matr_row in temp_list:
                        for matr_vara in matr_row:
                            idx = righ_idxs[i]
                            expr_list.append(matr_vara+'='+fmatr[math.ceil(int(idx)/clm)-1][int(idx)%clm-1]+'\n\n')
                            i += 1

                code_use_dict[code_place] += expr_list

    # assign the temporary list type of 'fvect' or 'fmatr'
    # to the list type of 'fvect' or 'fmatr'
    elif left_vara[0]  == '[' and  left_vara[-1] == ']' :

        left_vara = left_vara.lstrip('[').rstrip(']')

        # Func_Asgn: [a] = b[*,*] --------- @S a b * *
        if regx.search(r'[a-z]+[0-9a-z]*\[([0-9],)*[0-9]?\]',righ_expr,regx.I) != None \
        and righ_expr[-1] == ']':

            # read right variable index list
            righ_vara = righ_expr.split('[')[0]
            if righ_expr[-1] == ']' and righ_expr[-2] == '[':

                if 'fvect' in xde_lists and righ_vara in xde_lists['fvect']:
                    righ_idxs = list(range(int(xde_lists['fvect'][righ_vara][0])))

                elif 'fmatr' in xde_lists and righ_vara in xde_lists['fmatr']:
                    righ_idxs = list(range(int(xde_lists['fvect'][righ_vara][0]) \
                                          *int(xde_lists['fvect'][righ_vara][1])))

                righ_idxs = [x + 1 for x in righ_idxs]
            else:
                righ_idxs = righ_expr.split('[')[1].rstrip(']').split(',')

            if left_vara.count('_') == 0:       
                expres = left_vara + '='

                if   'fvect' in xde_lists and righ_vara in xde_lists['fvect']:
                    for idx in righ_idxs:
                        expres += xde_lists['fvect'][righ_vara][int(idx)]

                elif 'fmatr' in xde_lists and righ_vara in xde_lists['fmatr']:
                    row, clm = list(map(int,xde_lists['fmatr'][righ_vara][:2]))
                    fmatr = xde_lists['fmatr'][righ_vara][2:]
                    for idx in righ_idxs:
                        expres += fmatr[math.ceil(int(idx)/clm)-1][int(idx)%clm-1]

                code_use_dict[code_place].append(expres+'\n\n')

            elif left_vara.count('_') == 1: 
                left_name = left_vara.split('_')[0]
                vect_len  = len(xde_lists['fvect'][left_name])

                if vect_len == len(righ_idxs) + 1:

                    if   'fvect' in xde_lists and righ_vara in xde_lists['fvect']:
                        for idx,ii in zip(righ_idxs,range(vect_len)):
                            xde_lists['fvect'][left_name][ii+1] = \
                            xde_lists['fvect'][righ_vara][int(idx)]

                    elif 'fmatr' in xde_lists and righ_vara in xde_lists['fmatr']:
                        row, clm = list(map(int,xde_lists['fmatr'][righ_vara][:2]))
                        for idx,ii in zip(righ_idxs,range(vect_len)):
                            xde_lists['fvect'][left_name][ii+1] = \
                            xde_lists['fmatr'][righ_vara][math.ceil(int(idx)/clm)+1][int(idx)%clm-1]
            
            elif left_vara.count('_') == 2:
                left_name = left_vara.split('_')[0]
                expr_list = []
                matr_len = int(xde_lists['fmatr'][left_name][0]) \
                         * int(xde_lists['fmatr'][left_name][1])

                if matr_len == len(righ_idxs):
                    if   'fvect' in xde_lists and righ_vara in xde_lists['fvect']:
                        for ii,idx in zip(range(matr_len),righ_idxs):
                            xde_lists['fmatr'][left_name][math.ceil(ii/clm)+1][ii%clm-1] = \
                                xde_lists['fvect'][righ_vara][int(idx)]

                    elif 'fmatr' in xde_lists and righ_vara in xde_lists['fmatr']:
                        for ii,idx in zip(range(matr_len),righ_idxs):
                            xde_lists['fmatr'][left_name][math.ceil(ii/clm)+1][ii%clm-1] = \
                                xde_lists['fmatr'][righ_vara][math.ceil(int(idx)/clm)+1][int(idx)%clm-1]
        else:
            righ_expr = righ_expr.replace('[','').replace(']','')

            expr_list = idx_summation(left_vara,righ_expr,xde_lists)

            if left_vara.count('_') == 1:
                left_vara = left_vara.split('_')[0]
                row = int(xde_lists['fvect'][left_vara][0])
                for ii in range(row):
                    xde_lists['fvect'][left_vara][ii+1] = \
                        expr_list[ii].split('=')[1].replace('++','+').replace('-+','-')

            elif left_vara.count('_') == 2:
                left_vara = left_vara.split('_')[0]
                row,clm = list(map(int,xde_lists['fmatr'][left_vara][:2]))
                for ii in range(row):
                    for jj in range(clm):
                        xde_lists['fmatr'][left_vara][ii+2][jj] = \
                            expr_list[ii*row+jj].split('=')[1].replace('++','+').replace('-+','-')
# end release_funcasgn_code()

def write_disp_var(ges_info, xde_lists, gesfile):
    # 1.1 write disp declare
    gesfile.write('disp ')
    for strs in xde_lists['disp']:
        gesfile.write(strs+',')
    gesfile.write('\n')

    # 1.2 parsing var
    var_dict = {}
    pan_vars = set()
    for shap in xde_lists['shap'].keys():
        if shap[-1] == 'c':
            pan_vars |= set(xde_lists['shap'][shap])
            continue
        nodn = int(regx.search(r'[1-9]+', shap, regx.I).group())
        
        for var in xde_lists['shap'][shap]:
            var_dict[var] = [var+str(ii+1) for ii in range(nodn)]

    # 1.3 write var declare
    gesfile.write('var')
    disp_vars = xde_lists['disp'].copy()
    i = 0
    for pan_var in pan_vars:
        disp_vars.remove(pan_var)
    for nodi in range(int(ges_info['shap_nodn'])):
        for strs in disp_vars:
            if nodi >= len(var_dict[strs]):
                continue
            gesfile.write(' '+var_dict[strs][nodi])
            i += 1
            if i == 10:
                gesfile.write('\nvar')
                i = 0
# end write_disp_var()

def write_shap_tran(pfelacpath, ges_info, xde_lists, gesfile):
    gesfile.write('\nshap\n')
    geslib_coor = ['x','y','z']
    base_shap_strs = ''
    base_shap_type = list(xde_lists['shap'].keys())[0]
    #base_shap_nodn = regx.search(r'[1-9]+',base_shap_type,regx.I).group()
    #base_shap_form = base_shap_type[0]

    # 9.1 write shap
    for shap in xde_lists['shap'].keys():

        shap_func = 'd' + ges_info['dim'] + shap + '.sub'
        path_shap = pfelacpath + 'ges/ges.lib'
        file_shap = open(path_shap, mode='r')
        shap_find, shap_strs = 0, ''

        # 9.1.1 find shap function in ges.lib
        for line in file_shap.readlines():
            shap_start_file = regx.search('sub '+shap_func,line,regx.I)
            shap_end_file   = regx.search('end '+shap_func,line,regx.I)
            if shap_start_file != None:
                shap_find = 1
                continue
            if shap_end_file   != None:
                shap_find = 0
                continue
            if shap_find == 1:
                shap_strs += line
        file_shap.close()

        # note: save the base shap function for mix element when write tran
        if shap == base_shap_type:
            base_shap_strs = shap_strs

        # 9.1.2 replace shap func's coor by xde's coor
        for coor_i, coor_str in enumerate(xde_lists['coor']):
            shap_strs = shap_strs.replace(geslib_coor[coor_i],'r'+coor_str)

        # 9.1.3 replace shap func's disp by xde's disp and write
        for shap_var in xde_lists['shap'][shap]:
            if shap[-1].lower() == 'c':
                temp_strs = shap_strs.replace('u',xde_lists['shap'][shap][shap_var])
            else:
                temp_strs = shap_strs.replace('u',shap_var)
            gesfile.write(shap_var+'=\n')
            gesfile.write(temp_strs)
            gesfile.write('\n')

    # 9.2 write tran
    gesfile.write('tran\n')
    shap_expr_list = base_shap_strs.split('\n')
    shap_expr_list.remove('')
    tran_expr_list = []

    # 9.2.1 add '()'
    for shap_expr in shap_expr_list:
        shap_var,shap_exp = shap_expr.split('=')[:2]
        shap_num = regx.search(r'[0-9]+', shap_var, regx.I).group()
        shap_var = shap_var.replace(shap_num, '('+shap_num+')')
        tran_expr_list.append(shap_var + '=' + shap_exp)

    # 9.2.2 replace shap func's coor by xde's coor
    for coor_i, coor_str in enumerate(xde_lists['coor']) :
        for ii in range(len(tran_expr_list)):
            tran_expr_list[ii] = \
                tran_expr_list[ii].replace(geslib_coor[coor_i],'r'+coor_str)

    # 9.2.3 replace shap func's disp by by xde's coor and write
    for coor_str in xde_lists['coor']:
        gesfile.write(coor_str + '=\n')
        for tran_expr in tran_expr_list:
            gesfile.write(tran_expr.replace('u', coor_str) + '\n')
        gesfile.write('\n')
# end write_shap_tran()

def write_coefshap(pfelacpath, ges_info, xde_lists, gesfile):
    gesfile.write('coef\n')
    geslib_coor = ['x','y','z']
    for shap in xde_lists['coef_shap'].keys():

        shap_func = 'd' + ges_info['dim'] + shap + '.sub'
        path_shap = pfelacpath + 'ges/ges.lib'
        file_shap = open(path_shap, mode='r')
        shap_find, shap_strs = 0, ''

        # 9.3.1 find shap function in ges.lib
        for line in file_shap.readlines():
            shap_start_file = regx.search('sub '+shap_func,line,regx.I)
            shap_end_file   = regx.search('end '+shap_func,line,regx.I)
            if shap_start_file != None:
                shap_find = 1
                continue
            if shap_end_file     != None:
                shap_find = 0
                continue
            if shap_find == 1:
                shap_strs += line
        file_shap.close()

        # 9.2.1 add '()'
        shap_expr_list = shap_strs.split('\n')
        shap_expr_list.remove('')
        coef_expr_list = []

        for shap_expr in shap_expr_list:
            shap_var, shap_exp  = shap_expr.split('=')[:2]
            shap_num  = regx.search(r'[0-9]+', shap_var, regx.I).group()
            shap_var  = shap_var.replace(shap_num, '('+shap_num+')')
            coef_expr_list.append(shap_var + '=' + shap_exp)

        shap_strs = '\n'.join(coef_expr_list)+'\n'

        # 9.3.2 replace shap func's coor by xde's coor
        for coor_i,coor_str in enumerate(xde_lists['coor']):
            shap_strs = shap_strs.replace(geslib_coor[coor_i],'r'+coor_str)

        # 9.3.3 replace shap func's disp by xde's disp and write
        for shap_var in xde_lists['coef_shap'][shap]:
            temp_string = shap_strs.replace('u', shap_var)
            gesfile.write(shap_var + '=\n')
            gesfile.write(temp_string)
            gesfile.write('\n')
# end write_coefshap()

def write_gaus(pfelacpath, ges_info, xde_lists, gesfile):
    # 9.1 Gaussian integral
    if xde_lists['gaus'][0] == 'g':

        gaus_degree = regx.search(r'[0-9]+',xde_lists['gaus'],regx.I).group()

        # 9.1.1 line square or cube shap
        if ges_info['shap_form'].lower() in ['l','q','c']:

            path_gaus = pfelacpath+'ges/gaus.pnt'
            file_gaus = open(path_gaus, mode='r')
            gaus_find, gaus_axis, gaus_weit = 0, [], []

            # 9.1.1.1 read gaus axis and weight in gaus.pnt
            for line in file_gaus.readlines():
                gaus_start_file = regx.search('n='+gaus_degree,line,regx.I)
                if gaus_start_file != None:
                    gaus_find = 1
                    continue
                if gaus_find == 1 and line=='\n':
                    gaus_find = 0
                    continue
                if gaus_find == 1:
                    gaus_strs = line.split()
                    if  gaus_strs[0][0] not in ['-' ,'+'] :
                        gaus_strs[0] = ' '+gaus_strs[0]
                    gaus_axis.append(gaus_strs[0])
                    gaus_weit.append(gaus_strs[1])

            file_gaus.close()

            # 9.1.1.2 write line square or cube's gaussian integra
            gesfile.write('gaus = '+str(len(gaus_weit)**int(ges_info['dim']))+'\n')

            if  ges_info['shap_form'].lower()=='l':
                for axis_i in range(len(gaus_axis)):
                    gesfile.write(gaus_axis[axis_i]+' ' \
                                 +gaus_weit[axis_i]+'\n')

            elif ges_info['shap_form'].lower()=='q':
                for axis_i in range(len(gaus_axis)):
                    for axis_j in range(len(gaus_axis)):
                        weight = float(gaus_weit[axis_i]) \
                                *float(gaus_weit[axis_j])
                        gesfile.write (gaus_axis[axis_i]+' ' \
                                      +gaus_axis[axis_j]+' ' \
                                      +str(weight)+'\n')
                                        
            elif ges_info['shap_form'].lower()=='c':
                for axis_i in range(len(gaus_axis)):
                    for axis_j in range(len(gaus_axis)):
                        for axis_k in range(len(gaus_axis)):
                            weight = float(gaus_weit[axis_i]) \
                                    *float(gaus_weit[axis_j]) \
                                    *float(gaus_weit[axis_k])
                            gesfile.write (gaus_axis[axis_i]+' ' \
                                          +gaus_axis[axis_j]+' ' \
                                          +gaus_axis[axis_k]+' ' \
                                          +str(weight)+'\n')

        # 9.1.2 triangle shap
        elif ges_info['shap_form'].lower()=='t':

            path_gaus = pfelacpath+'ges/gaust.pnt'
            file_gaus = open(path_gaus, mode='r')
            gaus_find, gaus_strs = 0, ''

            # 9.1.2.1 tackle the gaussian degree
            if gaus_degree == '6':
                gaus_degree = '5'
            elif int(gaus_degree) > 12 and int(gaus_degree) < 17:
                gaus_degree = '12'
            elif int(gaus_degree) > 17:
                gaus_degree = '17'

            # 9.1.2.2 read gaus axis and weight in gaust.pnt and write
            for line in file_gaus.readlines():
                gaus_start_file = regx.match('P'+gaus_degree,line,regx.I)
                if gaus_start_file != None:
                    gaus_find = 1
                    continue
                if gaus_find == 1 and regx.match(r'\s*\n',line,regx.I) != None:
                    gaus_find = 0
                    continue
                if gaus_find == 1:
                    gaus_strs += line

            file_gaus.close()
            gesfile.write(gaus_strs)

        # 9.1.3 tetrahedron shap
        elif ges_info['shap_form'].lower()=='w':

            path_gaus = pfelacpath+'ges/gausw.pnt'
            file_gaus = open(path_gaus, mode='r')
            gaus_find, gaus_strs = 0, ''

            # 9.1.3.1 tackle the gaussian degree
            if gaus_degree == '4':
                gaus_degree = '3'
            elif gaus_degree == '6':
                gaus_degree = '5'
            elif int(gaus_degree) > 7:
                gaus_degree = '7'

            # 9.1.2.2 read gaus axis and weight in gausw.pnt and write
            for line in file_gaus.readlines():
                gaus_start_file = regx.search('P'+gaus_degree,line,regx.I)
                if gaus_start_file != None:
                    gaus_find = 1
                    continue
                if gaus_find == 1 and regx.match(r'\s*\n',line,regx.I) != None:
                    gaus_find = 0
                    continue
                if gaus_find == 1:
                    gaus_strs += line

            file_gaus.close()
            gesfile.write(gaus_strs)

        else: pass

    # 9.2 node integral
    else:
        path_gaus = pfelacpath+'ges/ges.lib'
        file_gaus = open(path_gaus, mode='r')
        gaus_find, gaus_strs = 0, ''

        # 9.2.1 read gaus axis and weight in ges.lib and write
        for line in file_gaus.readlines():
            gaus_name = ' d'+ ges_info['dim'] + xde_lists['gaus']+'.gau'
            gaus_start_file = regx.search('sub' + gaus_name, line,regx.I)
            gaus_end_file   = regx.search('end' + gaus_name, line,regx.I)
            if gaus_start_file != None:
                gaus_find = 1
                continue
            if gaus_end_file != None:
                gaus_find = 0
                continue
            if gaus_find == 1:
                gaus_strs += line

        file_gaus.close()
        gesfile.write(gaus_strs)
# end write_gaus()

def write_func(code_use_dict, xde_lists, gesfile):
    gesfile.write('\nfunc\n')
    if 'vol'  in xde_lists :
        gesfile.write(xde_lists['vol'])

    if 'func' in code_use_dict:
        for strs in code_use_dict['func']:

            if strs[0] == '$':
                gesfile.write(strs)

            else:
                if strs.find('(') != -1:
                    strs = strs.rstrip('\n')
                    
                    driv_list = set(regx.findall(r'\[[a-z][a-z0-9]*/[xyzros]\]', strs, regx.I))
                    rplc_list = ['driv'+str(i) for i in range(len(driv_list))]
                    for rplc, driv in zip(rplc_list, driv_list):
                        strs = strs.replace(driv, rplc)
                    
                    expr_objt = expr(strs.split('=')[1])
                    expr_strs = expr_objt.bracket_expand(expr_objt.expr_head)
                    
                    for rplc, driv in zip(rplc_list, driv_list):
                        expr_strs = expr_strs.replace(rplc, driv)
                    strs = strs.split('=')[0] + '=' + expr_strs+'\n\n'
                    
                    gesfile.write(strs)
                else: gesfile.write(strs)
# end write_func()

def write_weak(weak, code_use_dict, xde_lists, gesfile):
    if xde_lists[weak][0].lower() != 'null' or weak in code_use_dict:
        gesfile.write('\n{}\n'.format(weak))
    else: return

    if weak in code_use_dict:
        for strs in code_use_dict[weak]:
            gesfile.write(strs)

    if xde_lists[weak][0] == 'dist':
        left_vara = xde_lists[weak][0]
        righ_expr = ''
        for ii in range(1,len(xde_lists[weak])):
            righ_expr += xde_lists[weak][ii]
        expr_list = idx_summation(left_vara,righ_expr,xde_lists)
        expr_list = split_bracket_expr(expr_list[0])
        for strs in expr_list:
            if strs == 'dist=':
                gesfile.write(strs)
            else:
                gesfile.write(strs+'\n')

    elif xde_lists[weak][0] == 'lump':
        if len(xde_lists[weak]) == 1:
            xde_lists[weak].append('1.0')

        lump_expr = {}
        if len(xde_lists[weak]) == 2: pass

        gesfile.write('lump =\n')
        for shaps in xde_lists['shap']:
            nodn = regx.search(r'\d+',shaps,regx.I).group()
            for vara in xde_lists['shap'][shaps]:
                for ii in range(int(nodn)):
                    gesfile.write('+[{}]{}{}\n' \
                        .format(xde_lists[weak][1], vara, ii+1))
# end write_weak()

def write_load(xde_lists, gesfile):
    gesfile.write('\n')
    left_vara = 'load'
    righ_expr = ''.join(xde_lists['load'])
    expr_list = idx_summation(left_vara,righ_expr,xde_lists)
    expr_list = split_bracket_expr(expr_list[0])
    for strs in expr_list:
        if strs == 'load=':
            gesfile.write(strs)
        else:
            gesfile.write(strs+'\n')
# end write_load() 