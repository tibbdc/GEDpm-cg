import os
import boto3
import uuid
import json

# enviroment
region = os.environ["AWS_DEFAULT_REGION"]
result_bucket = os.environ["s3Result"]

s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb',region_name=os.environ['AWS_DEFAULT_REGION'])
output_table = dynamodb.Table(os.environ['ddbOutput'])

#Obtain the reverse complementary sequence 
def revComp(seq):
    complementSeq=seq.translate(str.maketrans('ACGTacgtRYMKrymkVBHDvbhd', 'TGCAtgcaYRKMyrkmBVDHbvdh'))
    revcompSeq = complementSeq[::-1]
    return revcompSeq

#Get the template sequence for primer design based on the input file 
def input_to_primer_template(input_file_path, max_left_arm_seq_length, max_right_arm_seq_length, max_verify_1_up_ponit, max_verify_2_down_ponit):
    primer_template = {}
    with open(input_file_path,'r') as input_file:
        for line1 in input_file:
            seq_id = line1.split(',')[0]
            sequence = line1.split(',')[1]
            index_mutation_site = int(line1.split(',')[2])
            base_before_mutation = line1.split(',')[3]
            base_after_mutation = line1.split(',')[4][:-1]
            seq_length = len(sequence)
            if base_before_mutation == 'O':
                seq_length_needed = max_left_arm_seq_length + max_right_arm_seq_length + max_verify_1_up_ponit + max_verify_2_down_ponit
                if seq_length < seq_length_needed:
                    error ="The length of target sequence must be larger than sum of 'Upstream Homologous Arm Max Length', 'Downstream Homologous Arm Max Length','Max Length of Gap between Upstream Homologous Arm and Left Sequencing Primer' and 'Max Length of Gap between Downstream Homologous Arm and Right Sequencing Primer'"
                    print(error)
                    # break
                    return error
                else:
                    list_seq_and_mut_position = []
                    # seq_after_mutation = sequence[:index_mutation_site-1] + base_after_mutation + sequence[index_mutation_site:]
                    seq_after_mutation = sequence[:index_mutation_site-1] + base_after_mutation + sequence[index_mutation_site-1:]
                    list_seq_and_mut_position.extend([seq_after_mutation,index_mutation_site])
                    primer_template[seq_id] = list_seq_and_mut_position
            else:
                seq_length_needed = max_left_arm_seq_length + max_right_arm_seq_length + max_verify_1_up_ponit + max_verify_2_down_ponit + 1
                if seq_length < seq_length_needed:
                    error = "The length of target sequence must be larger than sum of 'Upstream Homologous Arm Max Length', 'Downstream Homologous Arm Max Length','Max Length of Gap between Upstream Homologous Arm and Left Sequencing Primer' and 'Max Length of Gap between Downstream Homologous Arm and Right Sequencing Primer'"
                    print(error)
                    # break
                    return error
                else:
                    base_type = sequence[index_mutation_site-1]
                    if base_type != base_before_mutation:
                        error="The 'Mutation site index' and 'Sequence before mutation' of the sequence with the ID " + seq_id + " in the input file do not match."
                        print(error)
                        # break
                        return error
                    else:
                        list_seq_and_mut_position = []
                        if base_after_mutation == 'O':
                            seq_after_mutation = sequence[:index_mutation_site-1] + sequence[index_mutation_site:]
                            list_seq_and_mut_position.extend([seq_after_mutation,index_mutation_site])
                            primer_template[seq_id] = list_seq_and_mut_position
                        else:
                            seq_after_mutation = sequence[:index_mutation_site-1] + base_after_mutation + sequence[index_mutation_site:]
                            list_seq_and_mut_position.extend([seq_after_mutation,index_mutation_site])
                            primer_template[seq_id] = list_seq_and_mut_position
    return primer_template

#Obtain linear plasmid sequence 
def plasmid_seq(input_file_path):
    with open(input_file_path,'r') as input_file:
        return input_file.read().upper()

#Primer design for upstream Homologous Arm
def leftPrimer1Design(seqId,seqTemplate,max_left_arm_seq_length,min_left_arm_seq_length,left_arm_primer_opt_tm,left_arm_primer_min_tm,left_arm_primer_max_tm,left_arm_primer_min_gc,left_arm_primer_max_gc):
    import primer3
    seqlength=len(seqTemplate)
    left_length=max_left_arm_seq_length-min_left_arm_seq_length
    seq_args = {
            'SEQUENCE_ID': seqId,
            'SEQUENCE_TEMPLATE': seqTemplate,
            'SEQUENCE_PRIMER_PAIR_OK_REGION_LIST': [[0,left_length+18,seqlength-38,37]],
            #'SEQUENCE_FORCE_RIGHT_START': seqlength-1,
    }
    global_args = {
            'PRIMER_OPT_SIZE': 18,
            'PRIMER_MIN_SIZE': 18,
            'PRIMER_MAX_SIZE': 25,
            'PRIMER_OPT_TM': left_arm_primer_opt_tm,
            'PRIMER_MIN_TM': left_arm_primer_min_tm,
            'PRIMER_MAX_TM': left_arm_primer_max_tm,
            'PRIMER_MIN_GC': left_arm_primer_min_gc,
            'PRIMER_MAX_GC': left_arm_primer_max_gc,
            'PRIMER_PICK_ANYWAY':1,
            'PRIMER_PRODUCT_SIZE_RANGE': [seqlength-left_length+18,seqlength],
            'PRIMER_NUM_RETURN':1
    }
    primer3_result = primer3.bindings.designPrimers(seq_args, global_args)
    return primer3_result

#Primer design for downstream Homologous Arm
def rightPrimer1Design(seqId,seqTemplate,max_right_arm_seq_length,min_right_arm_seq_length,right_arm_primer_opt_tm,right_arm_primer_min_tm,right_arm_primer_max_tm,right_arm_primer_min_gc,right_arm_primer_max_gc):
    import primer3
    seqlength=len(seqTemplate)
    right_length=max_right_arm_seq_length-min_right_arm_seq_length
    seq_args = {
            'SEQUENCE_ID': seqId,
            'SEQUENCE_TEMPLATE': seqTemplate,
            'SEQUENCE_PRIMER_PAIR_OK_REGION_LIST': [[-1,-1,seqlength-right_length-1,right_length]],
            'SEQUENCE_FORCE_LEFT_START': 0
    }
    global_args = {
            'PRIMER_OPT_SIZE': 18,
            'PRIMER_MIN_SIZE': 18,
            'PRIMER_MAX_SIZE': 25,
            'PRIMER_OPT_TM': right_arm_primer_opt_tm,
            'PRIMER_MIN_TM': right_arm_primer_min_tm,
            'PRIMER_MAX_TM': right_arm_primer_max_tm,
            'PRIMER_MIN_GC': right_arm_primer_min_gc,
            'PRIMER_MAX_GC': right_arm_primer_max_gc,
            'PRIMER_PICK_ANYWAY':1,
            'PRIMER_PRODUCT_SIZE_RANGE': [seqlength-right_length,seqlength],
            'PRIMER_NUM_RETURN':1
    }
    primer3_result = primer3.bindings.designPrimers(seq_args, global_args)
    return primer3_result

#Primer design for first round of sequencing verification
def verify1PrimerDesign(seqId,seqTemplate,max_verify_1_up_ponit,min_verify_1_up_ponit,max_verify_1_down_ponit,min_verify_1_down_ponit,verify_1_primer_opt_tm,verify_1_primer_min_tm,verify_1_primer_max_tm,verify_1_primer_min_gc,verify_1_primer_max_gc):
    import primer3
    seqlength=len(seqTemplate)
    left_length=max_verify_1_up_ponit-min_verify_1_up_ponit
    right_length=max_verify_1_down_ponit-min_verify_1_down_ponit
    seq_args = {
            'SEQUENCE_ID': seqId,
            'SEQUENCE_TEMPLATE': seqTemplate,
            'SEQUENCE_PRIMER_PAIR_OK_REGION_LIST': [[0,left_length+18,seqlength-right_length,right_length]],
            'SEQUENCE_FORCE_RIGHT_START': seqlength-1
    }
    global_args = {
            'PRIMER_OPT_SIZE': 20,
            'PRIMER_MIN_SIZE': 18,
            'PRIMER_MAX_SIZE': 25,
            'PRIMER_OPT_TM': verify_1_primer_opt_tm,
            'PRIMER_MIN_TM': verify_1_primer_min_tm,
            'PRIMER_MAX_TM': verify_1_primer_max_tm,
            'PRIMER_MIN_GC': verify_1_primer_min_gc,
            'PRIMER_MAX_GC': verify_1_primer_max_gc,
            'PRIMER_PICK_ANYWAY':1,
            'PRIMER_PRODUCT_SIZE_RANGE': [seqlength-left_length-right_length+36,seqlength],
            'PRIMER_NUM_RETURN':1
    }
    primer3_result = primer3.bindings.designPrimers(seq_args, global_args)
    return primer3_result

#Primer design for second round of sequencing verification
def verify2PrimerDesign(seqId,seqTemplate,max_verify_2_down_ponit,min_verify_2_down_ponit,verify_2_primer_opt_tm,verify_2_primer_min_tm,verify_2_primer_max_tm,verify_2_primer_min_gc,verify_2_primer_max_gc):
    import primer3
    seqlength=len(seqTemplate)
    right_length=max_verify_2_down_ponit-min_verify_2_down_ponit
    seq_args = {
            'SEQUENCE_ID': seqId,
            'SEQUENCE_TEMPLATE': seqTemplate,
            'SEQUENCE_PRIMER_PAIR_OK_REGION_LIST': [[0,20,seqlength-right_length,right_length]],
            'SEQUENCE_FORCE_LEFT_START': 0
    }
    global_args = {
            'PRIMER_OPT_SIZE': 20,
            'PRIMER_MIN_SIZE': 20,
            'PRIMER_MAX_SIZE': 25,
            'PRIMER_OPT_TM': verify_2_primer_opt_tm,
            'PRIMER_MIN_TM': verify_2_primer_min_tm,
            'PRIMER_MAX_TM': verify_2_primer_max_tm,
            'PRIMER_MIN_GC': verify_2_primer_min_gc,
            'PRIMER_MAX_GC': verify_2_primer_max_gc,
            'PRIMER_PICK_ANYWAY':1,
            'PRIMER_PRODUCT_SIZE_RANGE': [seqlength-right_length+20,seqlength],
            'PRIMER_NUM_RETURN':1
    }
    primer3_result = primer3.bindings.designPrimers(seq_args, global_args)
    return primer3_result               

#Get the result file
#Get the result dataframe for UHA and DHA
def dataframe_output_udha(dictxx):
    import pandas as pd
    listtitle=['PRIMER_LEFT_WHOLE_SEQUENCE','PRIMER_RIGHT_WHOLE_SEQUENCE','PRODUCT_SEQUENCE','PRODUCT_WHOLE_LENGTH']
    dict_column_filtered={}
    for key1 in dictxx:
        dict_column_filtered_one={}
        for key2 in dictxx[key1]:
            if key2 in listtitle:
                dict_column_filtered_one[key2]=dictxx[key1][key2]
        dict_column_filtered[key1]=dict_column_filtered_one
    dataframe=pd.DataFrame(dict_column_filtered).T
    return dataframe

#Get the result dataframe for FRV and SRV
def dataframe_output_fsrv(dictxx):
    import pandas as pd
    listtitle=['PRIMER_LEFT_0_SEQUENCE','PRIMER_RIGHT_0_SEQUENCE','PRIMER_LEFT_0_TM','PRIMER_RIGHT_0_TM','PRIMER_PAIR_0_PRODUCT_SIZE','PRODUCT_SEQUENCE','PRODUCT_LENGTH']
    dict_column_filtered={}
    for key1 in dictxx:
        dict_column_filtered_one={}
        for key2 in dictxx[key1]:
            if key2 in listtitle:
                dict_column_filtered_one[key2]=dictxx[key1][key2]
        dict_column_filtered[key1]=dict_column_filtered_one
    dataframe=pd.DataFrame(dict_column_filtered).T
    return dataframe
    
#Get result dataframe of the failed design 
def dataframe_failed(dictxx):
    import pandas as pd
    listtitle=['PRIMER_LEFT_EXPLAIN','PRIMER_RIGHT_EXPLAIN','PRIMER_PAIR_EXPLAIN','PRIMER_LEFT_NUM_RETURNED','PRIMER_RIGHT_NUM_RETURNED','PRIMER_INTERNAL_NUM_RETURNED','PRIMER_PAIR_NUM_RETURNED']
    dict_column_filtered={}
    for key1 in dictxx:
        dict_column_filtered_one={}
        for key2 in dictxx[key1]:
            if key2 in listtitle:
                dict_column_filtered_one[key2]=dictxx[key1][key2]
        dict_column_filtered[key1]=dict_column_filtered_one
    dataframe=pd.DataFrame(dict_column_filtered).T
    return dataframe

#Get the file containing the primers submitted to the sequence synthesis company
def primers_submitted_output(dict_left,dict_right,dict_verify1,dict_verify2,output_dir):
    import pandas as pd
    with open(output_dir,"w") as ofile:
        ofile.write("Primer_name\tSequence"+'\n')
        for key1 in dict_verify2:
            ofile.write(key1 + '-1' + '\t' + dict_left[key1]['PRIMER_LEFT_WHOLE_SEQUENCE'] + '\n')
            ofile.write(key1 + '-2' + '\t'+ dict_left[key1]['PRIMER_RIGHT_WHOLE_SEQUENCE'] + '\n')
            ofile.write(key1 + '-3' + '\t'+ dict_right[key1]['PRIMER_LEFT_WHOLE_SEQUENCE'] + '\n')
            ofile.write(key1 + '-4' + '\t'+ dict_right[key1]['PRIMER_RIGHT_WHOLE_SEQUENCE'] + '\n')
            ofile.write('test-' + key1 + '-1' + '\t'+ dict_verify1[key1]['PRIMER_LEFT_0_SEQUENCE'] + '\n')
            ofile.write('test-' + key1 + '-2' + '\t'+ dict_verify1[key1]['PRIMER_RIGHT_0_SEQUENCE'] + '\n')
            ofile.write('test-' + key1 + '-3' + '\t'+ dict_verify2[key1]['PRIMER_RIGHT_0_SEQUENCE'] + '\n')
    primer_order_dir=output_dir.replace('.txt','.xlsx')
    pd.read_table(output_dir, index_col=0).to_excel(primer_order_dir)

#Map the target sequence to the reference genome by Blast
def blast_target_seq(ref_genome,workdir,blast_input_file_path):
    import os
    blast_output_file_path=workdir+'/blast_output.txt'
    ref_lib=ref_genome.split('/')[-1].split('.')[0]
    seq_length=0
    with open(blast_input_file_path,'r') as ifile:
        for line in ifile:
            if not line[0]=='>':
                seq_length += len(line)-1
                break
    if seq_length > 550:
        evalue='300'
    else:
        evalue=str(int((seq_length*0.5521-7.5856)*0.8))
    os.system("/opt/bin/makeblastdb -in "+ref_genome+" -dbtype nucl -parse_seqids -out "+ref_lib)
    os.system("/opt/bin/blastn -query "+blast_input_file_path+" -db "+ref_lib+" -outfmt 6 -out "+blast_output_file_path+" -evalue 1e-"+evalue+" -max_target_seqs 5 -num_threads 4")

#Evaluate the feasibility of design with the mapping of the homologous arm to the reference genome
# def blast_evaluate(dict_left,dict_right,workdir,ref_genome):
#     import pandas as pd
#     set_left_key=set(dict_left.keys())
#     set_right_key=set(dict_right.keys())
#     if dict_left=={} or dict_right=={}:
#         pass
#     elif set_left_key & set_right_key==set():
#         pass
#     else:
#         dict_homo_arm_seq={}
#         for id1 in dict_left:
#             left_homo_arm_seq=dict_left[id1]['PRODUCT_SEQUENCE']
#             for id2 in dict_right:
#                 if id2==id1:
#                     right_homo_arm_seq=dict_right[id1]['PRODUCT_SEQUENCE']
#                     homo_arm_seq=left_homo_arm_seq[20:]+right_homo_arm_seq[20:-20]
#                     dict_homo_arm_seq[id1]=homo_arm_seq
#         blast_input_file_path=workdir+'/blast_input.txt'
#         with open(blast_input_file_path,'w') as blast_input_file:
#             for key1 in dict_homo_arm_seq:
#                 blast_input_file.write('>'+key1+'\n')
#                 blast_input_file.write(dict_homo_arm_seq[key1]+'\n')
#         blast_target_seq(ref_genome,workdir,blast_input_file_path)
#     #print(dict_homo_arm_seq)
#     evaluate_output_file_path=workdir+'/Evaluation_result.txt'
#     with open(evaluate_output_file_path,'w') as evaluate_output:
#         evaluate_output.write("ID\tWarning\n")
#         with open(workdir+'/blast_output.txt','r') as evaluate_input:
#             list_result_id=[]
#             list_result_id_redun=[]
#             for line_result in evaluate_input:
#                 result_id=line_result.split('\t')[0]
#                 if result_id in list_result_id:
#                     if result_id in list_result_id_redun:
#                         continue
#                     else:
#                         evaluate_output.write(result_id+'\t'+'The target sequence can map to multiple positions in the reference genome. The genome editing may be mislocated.'+'\n')
#                         list_result_id_redun.append(result_id)
#                 else:
#                     list_result_id.append(result_id)
#             list_result_id_unmap=[]
#             for key2 in dict_homo_arm_seq:
#                 if not key2 in list_result_id:
#                     if key2 in list_result_id_unmap:
#                         continue
#                     else:
#                         evaluate_output.write(key2+'\t'+'The target sequence can not map to the reference genome. Please check them.'+'\n')
#                         list_result_id_unmap.append(key2)
#     evaluate_output_dir=evaluate_output_file_path.replace('.txt','.xlsx')
#     pd.read_table(evaluate_output_file_path, index_col=0).to_excel(evaluate_output_dir)
def blast_evaluate(dict_left,dict_right,workdir,ref_genome):
    import pandas as pd
    set_left_key=set(dict_left.keys())
    set_right_key=set(dict_right.keys())
    if dict_left=={} or dict_right=={}:
        pass
    elif set_left_key & set_right_key==set():
        pass
    else:
        dict_homo_arm_seq={}
        for id1 in dict_left:
            left_homo_arm_seq=dict_left[id1]['PRODUCT_SEQUENCE']
            for id2 in dict_right:
                if id2==id1:
                    right_homo_arm_seq=dict_right[id1]['PRODUCT_SEQUENCE']
                    homo_arm_seq=left_homo_arm_seq[20:]+right_homo_arm_seq[20:-20]
                    dict_homo_arm_seq[id1]=homo_arm_seq
        blast_input_file_path=workdir+'/blast_input.txt'
        with open(blast_input_file_path,'w') as blast_input_file:
            for key1 in dict_homo_arm_seq:
                blast_input_file.write('>'+key1+'\n')
                blast_input_file.write(dict_homo_arm_seq[key1]+'\n')
        blast_target_seq(ref_genome,workdir,blast_input_file_path)
    evaluate_output_file_path=workdir+'/Evaluation_result.txt'
    with open(evaluate_output_file_path,'w') as evaluate_output:
        evaluate_output.write("ID\tWarning\n")
        dict_evaluate_output={}
        with open(workdir+'/blast_output.txt','r') as evaluate_input:
            dict_result_id = {}
            for line_result in evaluate_input:
                result_id=line_result.split('\t')[0]
                dict_result_id[result_id] = dict_result_id.get(result_id,0) + 1
            list_result_id_unmap=[]
            for key2 in dict_homo_arm_seq:
                if key2 in dict_result_id:
                    if dict_result_id[key2]>1:
                        evaluate_output.write(key2+'\t'+'The target sequence can map to multiple positions in the reference genome. The genome editing may be mislocated.'+'\n')
                    else:
                        continue
                else:
                    if key2 in list_result_id_unmap:
                        continue
                    else:
                        evaluate_output.write(key2+'\t'+'The target sequence can not map to the reference genome. Please check them.'+'\n')
                        list_result_id_unmap.append(key2)
        for key3 in dict_evaluate_output:
            evaluate_output.write(key3+'\t'+dict_evaluate_output[key3]+'\n')
    evaluate_output_dir=evaluate_output_file_path.replace('.txt','.xlsx')
    pd.read_table(evaluate_output_file_path, index_col=0).to_excel(evaluate_output_dir)
#Design process
def design_process(input_file_path,plasmid_file_path,workdir,ref_genome,max_left_arm_seq_length,min_left_arm_seq_length,max_right_arm_seq_length,min_right_arm_seq_length,max_verify_1_up_ponit,min_verify_1_up_ponit,max_verify_1_down_ponit,min_verify_1_down_ponit,max_verify_2_down_ponit,min_verify_2_down_ponit,left_arm_primer_opt_tm,left_arm_primer_min_tm,left_arm_primer_max_tm,left_arm_primer_min_gc,left_arm_primer_max_gc,right_arm_primer_opt_tm,right_arm_primer_min_tm,right_arm_primer_max_tm,right_arm_primer_min_gc,right_arm_primer_max_gc,verify_1_primer_opt_tm,verify_1_primer_min_tm,verify_1_primer_max_tm,verify_1_primer_min_gc,verify_1_primer_max_gc,verify_2_primer_opt_tm,verify_2_primer_min_tm,verify_2_primer_max_tm,verify_2_primer_min_gc,verify_2_primer_max_gc):
    import os
    import pandas as pd
    dict_input_seq=input_to_primer_template(input_file_path,max_left_arm_seq_length,max_right_arm_seq_length,max_verify_1_up_ponit,max_verify_2_down_ponit)
    if isinstance(dict_input_seq,dict):
        pass
    else:
        return dict_input_seq
    dictleftprimerswhole={}
    dictleftprimersfailed={}
    for key1 in dict_input_seq:
        target_seq=dict_input_seq[key1][0]
        mutation_site1=int(dict_input_seq[key1][1])
        left_temp_seq=target_seq[mutation_site1-max_left_arm_seq_length:mutation_site1]
        dictleftprimers=leftPrimer1Design(key1,left_temp_seq,max_left_arm_seq_length,min_left_arm_seq_length,left_arm_primer_opt_tm,left_arm_primer_min_tm,left_arm_primer_max_tm,left_arm_primer_min_gc,left_arm_primer_max_gc)
        if len(dictleftprimers)<10:
            dictleftprimersfailed[key1]=dictleftprimers
        else:
            dictleftprimerswhole[key1]=dictleftprimers
    plasmidseq=plasmid_seq(plasmid_file_path)
    dictprimerrighttemp={}
    for key2 in dictleftprimerswhole:
        mutation_site2=int(dict_input_seq[key2][1])
        leftprimer=dictleftprimerswhole[key2]['PRIMER_LEFT_0_SEQUENCE']
        rightprimer=dictleftprimerswhole[key2]['PRIMER_RIGHT_0_SEQUENCE']
        rightprimerrev=revComp(rightprimer)
        strseqwild=dict_input_seq[key2][0]
        seqleftpoint=strseqwild.find(leftprimer)
        seqrightpoint=strseqwild.find(rightprimerrev)+len(rightprimer)-1
        leftprimeraddseq=plasmidseq[-20:]
        seqleftarm=leftprimeraddseq+strseqwild[seqleftpoint:seqrightpoint+21]
        dictleftprimerswhole[key2]['PRIMER_LEFT_WHOLE_SEQUENCE']=leftprimeraddseq+leftprimer
        revleftarmrightprimer=strseqwild[strseqwild.find(rightprimerrev):seqrightpoint+21]
        lenrevleftarmrightprimer=len(revleftarmrightprimer)
        leftarmrightprimer=revComp(revleftarmrightprimer)
        dictleftprimerswhole[key2]['PRIMER_RIGHT_WHOLE_SEQUENCE']=leftarmrightprimer
        dictleftprimerswhole[key2]['PRODUCT_SEQUENCE']=seqleftarm
        lenleftarm=len(seqleftarm)
        dictleftprimerswhole[key2]['PRODUCT_WHOLE_LENGTH']=lenleftarm
        righttempadd=strseqwild[mutation_site2-40:mutation_site2+max_right_arm_seq_length]
        rightarm5end=righttempadd.find(revleftarmrightprimer)+lenrevleftarmrightprimer-1
        dictprimerrighttemp[key2]=righttempadd[rightarm5end+1:]

    dictrightprimerswhole={}
    dictrightprimersfailed={}
    for key3 in dictprimerrighttemp:
        dictrightprimers=rightPrimer1Design(key3,dictprimerrighttemp[key3],max_right_arm_seq_length,min_right_arm_seq_length,right_arm_primer_opt_tm,right_arm_primer_min_tm,right_arm_primer_max_tm,right_arm_primer_min_gc,right_arm_primer_max_gc)
        if len(dictrightprimers)<10:
            dictrightprimersfailed[key3]=dictrightprimers
        else:
            dictrightprimerswhole[key3]=dictrightprimers

    dictprimerverify1temp={}
    for key4 in dictrightprimerswhole:
        rightleftprimer=dictrightprimerswhole[key4]['PRIMER_LEFT_0_SEQUENCE']
        rightrightprimer=dictrightprimerswhole[key4]['PRIMER_RIGHT_0_SEQUENCE']
        rightrightprimerrev=revComp(rightrightprimer)
        rightstrseqwild=dict_input_seq[key4][0]
        primerleftpoint=rightstrseqwild.find(rightleftprimer)
        lenrightarmleftprimer=len(rightleftprimer)
        rightseqleftpoint=primerleftpoint-20
        rightarmleftprimer=rightstrseqwild[rightseqleftpoint:primerleftpoint+lenrightarmleftprimer]
        rightseqrightpoint=rightstrseqwild.find(rightrightprimerrev)+len(rightrightprimer)-1
        # seqrightarm=rightstrseqwild[rightseqleftpoint:rightseqrightpoint+1]
        dictrightprimerswhole[key4]['PRIMER_LEFT_WHOLE_SEQUENCE']=rightarmleftprimer
        revrightprimeraddseq=plasmidseq[:20]
        rightprimeraddseq=revComp(revrightprimeraddseq)
        seqrightarm=rightstrseqwild[rightseqleftpoint:rightseqrightpoint+1]+revrightprimeraddseq
        dictrightprimerswhole[key4]['PRIMER_RIGHT_WHOLE_SEQUENCE']=rightprimeraddseq+rightrightprimer
        dictrightprimerswhole[key4]['PRODUCT_SEQUENCE']=seqrightarm
        lenrightarm=len(seqrightarm)
        dictrightprimerswhole[key4]['PRODUCT_WHOLE_LENGTH']=lenrightarm
        verify1leftprimer=dictleftprimerswhole[key4]['PRIMER_LEFT_0_SEQUENCE']
        verify1seqleftpoint=rightstrseqwild.find(verify1leftprimer)
        rightseqrightpoint=rightstrseqwild.find(rightrightprimerrev)+len(rightrightprimer)-1
        seqverify1arm=rightstrseqwild[verify1seqleftpoint-max_verify_1_up_ponit:rightseqrightpoint+1]
        seqplasmidadd=plasmidseq[:max_verify_1_down_ponit]
        seqverify1temp=seqverify1arm+seqplasmidadd
        dictprimerverify1temp[key4]=seqverify1temp
    dictverify1primerswhole={}
    dictverify1primersfailed={}
    for key5 in dictprimerverify1temp:
        dictverify1primers=verify1PrimerDesign(key5,dictprimerverify1temp[key5],max_verify_1_up_ponit,min_verify_1_up_ponit,max_verify_1_down_ponit,min_verify_1_down_ponit,verify_1_primer_opt_tm,verify_1_primer_min_tm,verify_1_primer_max_tm,verify_1_primer_min_gc,verify_1_primer_max_gc)
        if len(dictverify1primers)<10:
            dictverify1primersfailed[key5]=dictverify1primers
        else:
            dictverify1primerswhole[key5]=dictverify1primers
    #print(dictverify1primerswhole)
    dictprimerverify2temp={}
    for key6 in dictverify1primerswhole:
        verify1wholeleftprimer=dictverify1primerswhole[key6]['PRIMER_LEFT_0_SEQUENCE']
        verify1wholerightprimer=dictverify1primerswhole[key6]['PRIMER_RIGHT_0_SEQUENCE']
        verify1wholerightprimerrev=revComp(verify1wholerightprimer)
        verify1wholestrseqwild=dictprimerverify1temp[key6]
        verify1wholeseqleftpoint=verify1wholestrseqwild.find(verify1wholeleftprimer)
        verify1wholeseqrightpoint=verify1wholestrseqwild.find(verify1wholerightprimerrev)+len(verify1wholerightprimer)-1
        seqverify1=verify1wholestrseqwild[verify1wholeseqleftpoint:verify1wholeseqrightpoint+1]
        dictverify1primerswhole[key6]['PRODUCT_SEQUENCE']=seqverify1
        verify2leftprimer=verify1wholeleftprimer
        verify2rightprimer=dictrightprimerswhole[key6]['PRIMER_RIGHT_0_SEQUENCE']
        verify2rightprimerrev=revComp(verify2rightprimer)
        verify2strseqwild=dict_input_seq[key6][0]
        verify2seqleftpoint=verify2strseqwild.find(verify2leftprimer)
        verify2seqrightpoint=verify2strseqwild.find(verify2rightprimerrev)+len(verify2rightprimer)-1
        seqverify2temp=verify2strseqwild[verify2seqleftpoint:verify2seqrightpoint+max_verify_2_down_ponit+1]
        dictprimerverify2temp[key6]=seqverify2temp
    #print(dictprimerverify2temp)
    dictverify2primerswhole={}
    dictverify2primersfailed={}
    for key7 in dictprimerverify2temp:
        dictverify2primers=verify2PrimerDesign(key7,dictprimerverify2temp[key7],max_verify_2_down_ponit,min_verify_2_down_ponit,verify_2_primer_opt_tm,verify_2_primer_min_tm,verify_2_primer_max_tm,verify_2_primer_min_gc,verify_2_primer_max_gc)
        if len(dictverify2primers)<10:
            dictverify2primersfailed[key7]=dictverify2primers
        else:
            dictverify2primerswhole[key7]=dictverify2primers
    #print(dictverify2primerswhole)
    for key8 in dictverify2primerswhole:
        verify2wholeleftprimer=dictverify2primerswhole[key8]['PRIMER_LEFT_0_SEQUENCE']
        verify2wholerightprimer=dictverify2primerswhole[key8]['PRIMER_RIGHT_0_SEQUENCE']
        verify2wholerightprimerrev=revComp(verify2wholerightprimer)
        verify2wholestrseqwild=dictprimerverify2temp[key8]
        verify2wholeseqleftpoint=verify2wholestrseqwild.find(verify2wholeleftprimer)
        verify2wholeseqrightpoint=verify2wholestrseqwild.find(verify2wholerightprimerrev)+len(verify2wholerightprimer)-1
        seqverify2=verify2wholestrseqwild[verify2wholeseqleftpoint:verify2wholeseqrightpoint+1]
        dictverify2primerswhole[key8]['PRODUCT_SEQUENCE']=seqverify2
    #print(dictverify2primerswhole)
    blast_evaluate(dictleftprimerswhole,dictrightprimerswhole,workdir,ref_genome)
    dataframe_uha=dataframe_output_udha(dictleftprimerswhole)
    dataframe_dha=dataframe_output_udha(dictrightprimerswhole)
    dataframe_verify1=dataframe_output_fsrv(dictverify1primerswhole)
    dataframe_verify2=dataframe_output_fsrv(dictverify2primerswhole)
    primer_succceed_dir="./Design_results.xlsx"
    writer_succceed = pd.ExcelWriter(primer_succceed_dir)
    dataframe_uha.to_excel(writer_succceed, "Primers_for_UHA")
    dataframe_dha.to_excel(writer_succceed, "Primers_for_DHA")
    dataframe_verify1.to_excel(writer_succceed, "Primers_for_FRV")
    dataframe_verify2.to_excel(writer_succceed, "Primers_for_SRV")
    writer_succceed.save()
    dataframe_uha_failed=dataframe_failed(dictleftprimersfailed)
    dataframe_dha_failed=dataframe_failed(dictrightprimersfailed)
    dataframe_verify1_failed=dataframe_failed(dictverify1primersfailed)
    dataframe_verify2_failed=dataframe_failed(dictverify2primersfailed)
    primer_failed_dir="./Failed_task.xlsx"
    writer_failed = pd.ExcelWriter(primer_failed_dir)
    dataframe_uha_failed.to_excel(writer_failed, "Failed_task_for_UHA")
    dataframe_dha_failed.to_excel(writer_failed, "Failed_task_for_DHA")
    dataframe_verify1_failed.to_excel(writer_failed, "Failed_task_for_FRV")
    dataframe_verify2_failed.to_excel(writer_failed, "Failed_task_for_SRV")
    writer_failed.save()
    primers_submitted_output(dictleftprimerswhole,dictrightprimerswhole,dictverify1primerswhole,dictverify2primerswhole,'./Primer_order.txt')
    return "success"

def changeAcl(bucket,object_key,region):
    s3 = boto3.session.Session(region_name=region).resource('s3')
    s3.ObjectAcl(bucket,object_key).put(ACL="public-read")
    url = "https://"+bucket+".s3.amazonaws.com/%s" % object_key
    return url

def download_reference_from_s3(bucket,obj):
    """
        download reference and reference index to /tmp/
    """
    object_name = obj.split('/')[-1]
    local_reference = os.path.join('/tmp',object_name)
    s3.Object(bucket, obj).download_file(local_reference)
    for j in ['.nhr','.nin','.nog','.nsd','.nsi','.nsq']:
        s3.Object(bucket, obj+j).download_file(local_reference+j)
    return local_reference

def download_config_from_s3(bucket,obj):
    """
        download config to /tmp/
    """
    object_name = obj.split('/')[-1]
    local_config = os.path.join('/tmp',object_name)
    s3.Object(bucket, obj).download_file(local_config)
    return local_config


def lambda_handler(event,context):
    """



    """
    print(event)
    # workdir
    random_uuid = str(uuid.uuid4())
    workdir = os.path.join('/tmp',random_uuid)
    os.mkdir(workdir)
    os.chdir(workdir)

    # download file
    # sequence
    bucket = event["s3_sequence_file"].split('/')[2]
    key = '/'.join(event["s3_sequence_file"].split('/')[3:])
    object_name = key.split('/')[-1]
    input_file_path = os.path.join(workdir, object_name)
    s3.Object(bucket, key).download_file(input_file_path)

    # plasmid
    bucket = event["s3_plasmid_file"].split('/')[2]
    key = '/'.join(event["s3_plasmid_file"].split('/')[3:])
    object_name = key.split('/')[-1]
    plasmid_file_path = os.path.join(workdir, object_name)
    s3.Object(bucket, key).download_file(plasmid_file_path)

    # reference
    database = event["database"]
    user_upload_database = event["user_upload_database"]
    if database:
        # download config
        if not os.path.exists('/tmp/config.json'):
            local_config = download_config_from_s3(result_bucket,'config.json')
            # print(111111111)
        with open('/tmp/config.json','r') as conf:
            conf_dict = json.load(conf)
        print(conf_dict)
        
        # download genome database
        print(conf_dict[database])
        if not os.path.exists(os.path.join('/tmp',conf_dict[database].split("/")[-1])):
            genome = download_reference_from_s3(result_bucket,conf_dict[database])
            print(genome)
        else:
            genome = os.path.join('/tmp',conf_dict[database].split("/")[-1])
            print('local reference exists',genome)
    elif user_upload_database:
        bucket = event["user_upload_database"].split('/')[2]
        key = '/'.join(event["user_upload_database"].split('/')[3:])
        object_name = key.split('/')[-1]
        genome = os.path.join("/tmp", object_name)
        s3.Object(bucket, key).download_file(genome)
    
    # arguments
    max_left_arm_seq_length=int(event["max_left_arm_seq_length"])
    min_left_arm_seq_length=int(event["min_left_arm_seq_length"])
    max_right_arm_seq_length=int(event["max_right_arm_seq_length"])
    min_right_arm_seq_length=int(event["min_right_arm_seq_length"])
    max_verify_1_up_ponit=int(event["max_verify_1_up_ponit"])
    min_verify_1_up_ponit=int(event["min_verify_1_up_ponit"])
    max_verify_1_down_ponit=int(event["max_verify_1_down_ponit"])
    min_verify_1_down_ponit=int(event["min_verify_1_down_ponit"])
    max_verify_2_down_ponit=int(event["max_verify_2_down_ponit"])
    min_verify_2_down_ponit=int(event["min_verify_2_down_ponit"])
    left_arm_primer_opt_tm=int(event["left_arm_primer_opt_tm"])
    left_arm_primer_min_tm=int(event["left_arm_primer_min_tm"])
    left_arm_primer_max_tm=int(event["left_arm_primer_max_tm"])
    left_arm_primer_min_gc=int(event["left_arm_primer_min_gc"])
    left_arm_primer_max_gc=int(event["left_arm_primer_max_gc"])
    right_arm_primer_opt_tm=int(event["right_arm_primer_opt_tm"])
    right_arm_primer_min_tm=int(event["right_arm_primer_min_tm"])
    right_arm_primer_max_tm=int(event["right_arm_primer_max_tm"])
    right_arm_primer_min_gc=int(event["right_arm_primer_min_gc"])
    right_arm_primer_max_gc=int(event["right_arm_primer_max_gc"])
    verify_1_primer_opt_tm=int(event["verify_1_primer_opt_tm"])
    verify_1_primer_min_tm=int(event["verify_1_primer_min_tm"])
    verify_1_primer_max_tm=int(event["verify_1_primer_max_tm"])
    verify_1_primer_min_gc=int(event["verify_1_primer_min_gc"])
    verify_1_primer_max_gc=int(event["verify_1_primer_max_gc"])
    verify_2_primer_opt_tm=int(event["verify_2_primer_opt_tm"])
    verify_2_primer_min_tm=int(event["verify_2_primer_min_tm"])
    verify_2_primer_max_tm=int(event["verify_2_primer_max_tm"])
    verify_2_primer_min_gc=int(event["verify_2_primer_min_gc"])
    verify_2_primer_max_gc=int(event["verify_2_primer_max_gc"])
    # main
    try:
        response = design_process(input_file_path,plasmid_file_path,workdir,genome,max_left_arm_seq_length,min_left_arm_seq_length,max_right_arm_seq_length,min_right_arm_seq_length,max_verify_1_up_ponit,min_verify_1_up_ponit,max_verify_1_down_ponit,min_verify_1_down_ponit,max_verify_2_down_ponit,min_verify_2_down_ponit,left_arm_primer_opt_tm,left_arm_primer_min_tm,left_arm_primer_max_tm,left_arm_primer_min_gc,left_arm_primer_max_gc,right_arm_primer_opt_tm,right_arm_primer_min_tm,right_arm_primer_max_tm,right_arm_primer_min_gc,right_arm_primer_max_gc,verify_1_primer_opt_tm,verify_1_primer_min_tm,verify_1_primer_max_tm,verify_1_primer_min_gc,verify_1_primer_max_gc,verify_2_primer_opt_tm,verify_2_primer_min_tm,verify_2_primer_max_tm,verify_2_primer_min_gc,verify_2_primer_max_gc)
        if response =="success":
            # zip
            # cmd = 'zip -r ./result.zip ./*_1.txt  ./*_1.csv ./evaluate_result.txt'
            cmd = 'zip -r ./result.zip ./*.xlsx'
            os.system(cmd)
            # upload result files
            files=[
                'result.zip',
                'Design_results.xlsx',
                'Failed_task.xlsx',
                'Primer_order.xlsx',
                "Evaluation_result.xlsx"
            ]
            for i in files:
                result_s3_key = 'output/%s/%s' % (event["ID"],i)
                s3.meta.client.upload_file("./"+i,result_bucket,result_s3_key)
                # change acl
                changeAcl(result_bucket,result_s3_key,region)
            # update table  result attribute
            output_table.update_item(
                Key = {
                    "PK":event["ID"]
                },
                ReturnValues="UPDATED_NEW",
                UpdateExpression="SET #ts1  = :val1,#ts2  = :val2",
                ExpressionAttributeValues={
                    ':val1': "finished",
                    ':val2': "output/"+event["ID"]+"/result.zip"
                },
                ExpressionAttributeNames={
                    "#ts1":"Status",
                    "#ts2":"Result"
                }
            )

        else:
            # update table error attribute
            output_table.update_item(
                Key = {
                    "PK":event["ID"]
                },
                ReturnValues="UPDATED_NEW",
                UpdateExpression="SET #ts1  = :val1,#ts2  = :val2",
                ExpressionAttributeValues={
                    ':val1': "finished",
                    ':val2': response
                },
                ExpressionAttributeNames={
                    "#ts1":"Status",
                    "#ts2":"Error"
                }
            )
            return response
    except Exception as e:
        print(str(e))
        # update table error attribute
        output_table.update_item(
            Key = {
                "PK":event["ID"]
            },
            ReturnValues="UPDATED_NEW",
            UpdateExpression="SET #ts1  = :val1,#ts2  = :val2",
            ExpressionAttributeValues={
                ':val1': "finished",
                ':val2': "The input file does not meet the standard, please refer to the 'Example' file to modify it."
            },
            ExpressionAttributeNames={
                "#ts1":"Status",
                "#ts2":"Error"
            }
        )
        return {
            "statusCode":500
        }
