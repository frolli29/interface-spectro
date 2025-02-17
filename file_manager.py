"Module qui gère la création des fichiers de données issues des expériences"

import os
from datetime import datetime

#from automatic_sequences import AutomaticSequence, CustomSequence, CLassicSequence, 

def readSequenceInstructions(file):  #file: sequence config file #chaine de caracteres
    import csv
    with open(str(file), newline='') as f:
        reader = csv.reader(f, delimiter=';')
        tab = []
        syringes_to_use=[0,0,0] #set of syringes to be used
        idx=0
        for line in reader:
            #print(idx)
            if idx==0:
                idx+=1
                continue    #On ne s'occupe pas de l'entête du fichier
            syringe_id=line[0]  #'A' or 'B'
            dispense_type=line[1]   #'DISP_ON_PH' or 'DISP_VOL_UL'
            value=float(line[2])   #50uL or pH4.5 ...
            mixing_time=int(line[3])  #around 30sec pump is stopped
            flow_time=int(line[4])   #eg 300sec time with pump running
            pump_speed=int(line[5])  #1, 2, ... , 5
            if syringe_id=='A':
                syringes_to_use[0]=1
            elif syringe_id=='B':
                syringes_to_use[1]=1
            elif syringe_id=='C':
                syringes_to_use[2]=1
            line=[syringe_id,dispense_type,value,mixing_time,flow_time,pump_speed]
            tab.append(line)
            idx+=1

    instruction_table=tab
    print("instruction table : ",instruction_table)
        
    return syringes_to_use, instruction_table  

class Data():
    """contains all data of a sequence and deals with the writing in files"""

    def __init__(self, seq):
        self.seq=seq
        self.saving_folder = seq.saving_folder
        self.count = 0

        self.data=''
        self.formatted_data=''
        self.metadata=''

    def update_names(self,date):
        #filenames with start date (temporary until last measure)
        self.name_data = "seq_"+self.seq.experience_name+"_data_"+date
        self.name_formatted_data = "seq_"+self.seq.experience_name+"_formatted_data_"+date
        self.name_metadata = "seq_"+self.seq.experience_name+"_metadata_"+date
        #path (temporary until last measure)
        self.data_path = self.saving_folder+'/'+self.name_data+'.txt'
        self.formatted_data_path = self.saving_folder+'/'+self.name_formatted_data+'.txt'
        self.metadata_path = self.saving_folder+'/'+self.name_metadata+'.txt'
    
    def save_current_sequence_state(self):
        """At each measure this overwrites the 3 data files. 
        It allows to keep a backup of sequence data in case of disconnexion"""
        self.count+=1
        if self.count==1:
            dt=datetime.now()
            self.date_start=str(dt.strftime("%Y-%m-%d_%Hh%M"))
            self.update_names(self.date_start)  #names with start time
            self.createSequenceFiles(self.seq) #create 3 files
        else: #already a set of three files with the name of date_start
            self.createSequenceFiles(self.seq) #overwrites 3 files
        if self.count==self.seq.N_mes:
            self.update_name_full_sequence_data_files()

    def update_name_full_sequence_data_files(self):
        """Puts the end of experiment date in the file names"""
        dt=datetime.now()
        self.date_end=str(dt.strftime("%Y-%m-%d_%Hh%M"))

        old_data_path = self.data_path
        old_formatted_data_path = self.formatted_data_path
        old_metadata_path = self.metadata_path
        
        self.update_names(self.date_end)
        
        os.rename(old_data_path,self.data_path)
        os.rename(old_formatted_data_path,self.formatted_data_path)
        os.rename(old_metadata_path,self.metadata_path)

        self.count=0 #if another experiment is led this allows\
        #to create new files

    def createSequenceFiles(self, seq):
        #cette fonction s'adapte à une séquence terminée ou en cours (cas d'interruption de séquence)
        #création d'un fichier compatible avec le traitement de données
        #Ainsi que d'un fichier metadata qui contient toutes les informations annexes à propos de l'expérience

                                ### METADATA
        metadata = seq.infos+"\n\n"+seq.spectro.infos+"\n\n"+seq.phmeter.infos\
                    +"\n\n"+seq.pump.infos+"\n\n"+seq.dispenser.infos+"\n\n"
        if seq.spectro.state=='open':   #background and reference spectra
            bgd_and_ref=[seq.spectro.wavelengths,seq.spectro.active_background_spectrum,\
                         seq.spectro.active_ref_spectrum]
            metadata+="Wavelengths(nm)\tbackground (unit count)\treference ('')\n"
            for l in range(seq.spectro.N_lambda):
                for c in range(2):
                    metadata+=str(bgd_and_ref[c][l])+'\t'
                metadata+=str(bgd_and_ref[2][l])+'\n'
        
        f_metadata=open(self.metadata_path,'w')
        f_metadata.write(metadata)
        f_metadata.close()

        


                                        ### DATA AND FORMATTED DATA
        print("saving titration sequence data")
        data="measure n°\t"    #entête
        for k in range(seq.N_mes):
            data+=str(k+1)+'\t'

        #DISPENSER
        print(seq.dispense_mode)
        if seq.dispense_mode=='from file':
            data+="\nsyringe A (uL)\t"
            for k in range(seq.N_mes):
                data+=str(seq.added_volumes[k][0])+'\t'
            data+="\nsyringe B (uL)\t"
            for k in range(seq.N_mes):
                data+=str(seq.added_volumes[k][1])+'\t'
            data+="\nsyringe C (uL)\t"
            for k in range(seq.N_mes):
                data+=str(seq.added_volumes[k][2])+'\t'
            data+="\ncumulate (uL)\t"
            for k in range(len(seq.cumulate_volumes)):  #the list is filled during sequence
                data+=str(seq.cumulate_volumes[k])+'\t'
            data+="\nDilution\t"    #filled during sequence
            for k in range(len(seq.dilution_factors)):  #the list is filled during sequence
                data+=str(seq.dilution_factors[k])+'\t'
        else:
            data+='\ttotal\n'
            data+="added acid (uL)\t"+str(seq.added_acid_uL)+"\n"
            data+="dispensed base (uL)\t"                                                               
            for k in range(seq.N_mes):
                data+=str(seq.added_base_uL[k])+'\t'   
            data+='\t'+str(seq.total_added_volume)                                                                       
            data+='\ncumulate base (uL)\t'
            for k in range(seq.N_mes):
                data+=str(seq.cumulate_base_uL[k])+'\t'   
            data+='\ndilution factors\t'
            for k in range(seq.N_mes):
                data+=str(seq.dilution_factors[k])+'\t' 
            data+='\n' 

        processed_formatted_data=''

        #Times
        data+="\ntimes\t"   #heures de mesures
        for k in range(len(seq.measure_times)):
            data+=str(seq.measure_times[k].strftime("%H:%M:%S"))+'\t'   
        data+="\ndelay with previous measure\t"   #temps entre mesures
        for k in range(len(seq.measure_delays)):
            data+=str(seq.measure_delays[k].seconds//60)+":"+str(seq.measure_delays[k].seconds%60)+'\t' 

        #PHMETER
        if seq.phmeter.state=='open':    
            data+="\npH\t"
            for k in range(seq.N_mes):
                data+=seq.pH_mes[k]+'\t'
            data+="\nepsilon stab (pH unit)\t"
            for k in range(len(seq.stability_param)):
                data+=str(seq.stability_param[k][0])+'\t'
            data+="\ndt stab (seconds)\t"
            for k in range(len(seq.stability_param)):
                data+=str(seq.stability_param[k][1])+'\t'
            data+="\nInitial volume (uL)\t"+str(seq.V_init)+"\n"    #volume en uL
            data+="Pump mean voltage (Volt) : "+str(12*seq.pump.duty_cycle)+"\n\n"    #vitesse de pompe
            

        processed_formatted_data="\t"   #corrected from dilution
        for k in range(seq.N_mes):
            processed_formatted_data+=seq.pH_mes[k]+'\t'
        processed_formatted_data+="\n"

        #SPECTROMETER
        if seq.spectro.state=='open':           
            #absorbance measured
            data+="Wavelengths (nm)\tAbsorbance\n" 
            table = [seq.spectro.wavelengths]+seq.absorbance_spectra
            for l in range(seq.spectro.N_lambda):  #spectres
                for c in range(len(seq.absorbance_spectra_cd)):
                    #print(l,c)
                    data+=str(table[c][l])+'\t'
                data+=str(table[len(seq.absorbance_spectra_cd)][l])+'\n'

            table_formatted = [seq.spectro.wavelengths]+seq.absorbance_spectra_cd
            for l in range(seq.spectro.N_lambda):  #spectres
                for c in range(len(seq.absorbance_spectra_cd)):
                    processed_formatted_data+=str(table_formatted[c][l])+'\t'
                processed_formatted_data+=str(table_formatted[len(seq.absorbance_spectra_cd)][l])+'\n'

        f_formatted_data = open(self.formatted_data_path,'w')
        f_formatted_data.write(processed_formatted_data)
        f_formatted_data.close()

        f_data = open(self.data_path,'w') #création d'un fichier dans le répertoire
        f_data.write(data)
        f_data.close()