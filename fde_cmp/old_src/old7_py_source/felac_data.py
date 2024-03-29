'''
 Copyright: Copyright (c) 2019
 Created: 2019-6-28
 Author: Zhang_Licheng
 Title: save all the predefined data
 All rights reserved
'''
## for reading once and using everywhere ##

import re
import os

operator_data = {}
gaussian_data = {}
shapfunc_data = {}
oprt_name_list = []
shap_name_list = []

pfelacpath = os.environ['pfelacpath']

call_count = 0

def get_operator_data():

    file_opr = open(pfelacpath + 'ges/pde.lib', mode='r')
    opr_find = 0
    for strings in file_opr.readlines():
        opr_pattern = re.match(r'sub [a-z]+\.[xyzros123d]+\(.*\)', strings, re.I)
        if opr_pattern != None:
            opr_find = 1
            opr_name, opr_vars = opr_pattern.group().split('(')[:2]
            opr_name, opr_axis = opr_name.replace('sub ','').split('.')[:2]

            var_list = opr_vars.split(')')[0].split(',')

            if  opr_name not in operator_data:
                operator_data[opr_name] = {}
            if  opr_name in operator_data \
            and opr_axis not in operator_data[opr_name]:
                operator_data[opr_name][opr_axis] = {}

            operator_data[opr_name][opr_axis]['vars'] = var_list.copy()
            operator_data[opr_name][opr_axis]['axis'] \
                = [ strs for strs in var_list if strs in list('xyzros')]
            operator_data[opr_name][opr_axis]['disp'] \
                = [ strs for strs in var_list if strs not in list('xyzros')]
            operator_data[opr_name][opr_axis]['expr'] = ''

            continue

        end_parttern = re.match('end', strings, re.I)
        if end_parttern != None:
            opr_find = 0
            continue

        if opr_find == 1:
            operator_data[opr_name][opr_axis]['expr'] += strings

    file_opr.close()

    oprt_name_list.clear()
    for strs in [opr_name+'.'+opr_axis \
                    for opr_name in operator_data.keys() \
                        for opr_axis in operator_data[opr_name].keys()] :
        oprt_name_list.append(strs)
# end get_operator_info()

def print_operator_data():
    for opr in operator_data:
        print('-'*56)
        for i,axi in enumerate(operator_data[opr]):
            if i != 0:
                opr_str = ' '*len(opr)
            else:
                opr_str = opr
            axi_str = axi + ' '*(3-len(axi))
            print(opr_str,axi_str,operator_data[opr][axi]['vars'])
            for strs in operator_data[opr][axi]['expr'].rstrip().split('\n'):
                print(' '*(len(opr_str)+len(axi_str)+2),strs)
# end print_operator_data()

def get_gaussian_data():
    read_gaus_file('gaus', 'line', r'n=\d+')
    read_gaus_file('gaust', 'triangle', r'P\d+')
    read_gaus_file('gausw', 'tetrahedron', r'P\d+')
# end get_gaussian_data()

def read_gaus_file(gaus_file, shap_type, pattern):

    file_gaus = open(pfelacpath + f'ges/{gaus_file}.pnt', mode='r')
    gaussian_data[shap_type] = {}

    gaus_find, gaus_ordr = 0, ''
    for strings in file_gaus.readlines():
        gaus_pattern = re.match(pattern, strings, re.I)
        if gaus_pattern != None:
            gaus_find = 1
            if   shap_type[0] == 'l':
                gaus_ordr = gaus_pattern.group().split('=')[1]
            elif shap_type[0] == 't':
                gaus_ordr = gaus_pattern.group()[1:]
            gaussian_data[shap_type][gaus_ordr] = ''
            continue

        if strings[0] == '\n':
            gaus_find = 0
            continue

        if gaus_find == 1:
            gaussian_data[shap_type][gaus_ordr] += strings

    file_gaus.close()
# end read_gaus_file()

def print_gaussian_data():
    for shap in gaussian_data:
        print('-'*56)
        for i, order in enumerate(gaussian_data[shap]):
            if i != 0:
                shap_str = ' '*len(shap)
            else:
                shap_str = shap
            order_str = 'order ' + order + ' '*(2-len(order))
            print(shap_str, order_str)
            for strs in gaussian_data[shap][order].rstrip().split('\n'):
                print(' '*(len(shap_str)+len(order_str)+2),strs)
# end print_gaussian_data()

def get_shapfunc_data():
    file_shap = open(pfelacpath + 'ges/ges.lib', mode='r')
    shap_find = 0
    for strings in file_shap.readlines():

        shap_start = re.match(r'sub [0-9a-z]+\.', strings, re.I)
        if shap_start != None:
            shap_find = 1
            shap_name, shap_vars = strings.rstrip().split('(')
            shap_name, shap_attr = shap_name.replace('sub ','').split('.')
            vars_list = shap_vars.rstrip(')').split(',')

            if  shap_attr not in shapfunc_data:
                shapfunc_data[shap_attr] = {}
            if  shap_attr in shapfunc_data \
            and shap_name not in shapfunc_data[shap_attr]:
                shapfunc_data[shap_attr][shap_name] = {}

            shapfunc_data[shap_attr][shap_name]['vars'] = vars_list.copy()
            shapfunc_data[shap_attr][shap_name]['axis'] \
                = [ strs for strs in vars_list if strs in list('xyzros')]
            shapfunc_data[shap_attr][shap_name]['disp'] \
                = [ strs for strs in vars_list if strs not in list('xyzros')]
            shapfunc_data[shap_attr][shap_name]['expr'] = ''

            continue

        shap_end = re.match(r'end [0-9a-z]+\.', strings, re.I)
        if shap_end != None:
            shap_find = 0
            continue

        if shap_find == 1:
            shapfunc_data[shap_attr][shap_name]['expr'] += strings
    
    file_shap.close()

    shap_name_list.clear()
    for strs in [ shap_name for shap_name in shapfunc_data['sub'].keys()]:
        shap_name_list.append(strs)
# end get_shapfunc_data()

def print_shapfunc_data():
    for attr in shapfunc_data:
        print('-'*56)
        for i, name in enumerate(shapfunc_data[attr]):
            if i != 0:
                attr_str = ' '*len(attr)
            else:
                attr_str = attr
            name_str = name + ' '*(6-len(name))
            print(attr_str,name_str,shapfunc_data[attr][name]['vars'])
            for strs in shapfunc_data[attr][name]['expr'].rstrip().split('\n'):
                print(' '*(len(attr_str)+len(name_str)+2),strs)
# end print_shapfunc_data()

def get_felac_data():
    get_operator_data()
    get_gaussian_data()
    get_shapfunc_data()

    global call_count
    call_count += 1

def prepare_to_genxde(gesname, coortype, ges_info):
    ges_shap_type = re.search(r'[ltqwc][1-9][0-9]*',gesname,re.I).group()
    ges_gaus_type = re.search(r'g[1-9][0-9]*',gesname,re.I)
    if ges_gaus_type != None:
        ges_gaus_type = ges_gaus_type.group()
    else: ges_gaus_type = ges_shap_type

    ges_shap_nodn = re.search(r'[1-9][0-9]*',ges_shap_type,re.I).group()
    ges_shap_form = ges_shap_type[0]

    dim = re.search(r'[1-9]+', coortype, re.I).group()
    axi = coortype.split('d')[1]
    ges_info['name'] = gesname
    ges_info['shap_nodn'] = ges_shap_nodn
    ges_info['shap_form'] = ges_shap_form
    ges_info['gaus_type'] = ges_gaus_type
    ges_info['dim'] = dim
    ges_info['axi'] = axi
# end prepare_to_genxde()