"""Module pour modifier et calculer des données
Contient des fonctions liées au spectro mais ne s'appliquant pas directement"""

import numpy as np
#import matplotlib.pyplot as plt
import math
import time

#retourne la moyenne de l'ensemble des spectres
def average_spectra(spectra): 
    sp = np.array(spectra)
    a=np.mean(sp,0)
    avg_spectra=a.tolist()
    #print(avg_spectra)
    return avg_spectra

#intensité maximale de plusieurs spectres
def max_intensity(spectra):
    l=np.zeros(1)
    for s in spectra:
        arr=np.array(s)
        m=max(arr)
        l=np.append(l,m)
    Imax=max(l)
    print("Intensité maximale sur l'ensemble des spectres (unit counts) :", Imax)
    return Imax

def get_optimal_integration_time(spectra,int_time_us):
    Imax= max_intensity(spectra)
    optimal_int_time_us = 1000*int(int_time_us*15/Imax) #15000 unit count correspond au ST. 
    #Le capteur a une résolution de 14bit = 16300... unit count
    #ça doit être un multiple de 1000 pour être entier en millisecondes. 
    return optimal_int_time_us

#Les spectres entrés sont supposés corrigés du bruit d'obscurité et de la non linéarité du capteur
def intensity2absorbance(spectrum, ref_spec, dark=None):
    t0=time.time()
    N=len(spectrum)
    abs_spectrum=[0 for k in range(N)]
    for k in range(N):#pour éviter une division par zéro ou un log(0)
        if dark!=None:
            if ref_spec[k]-dark[k]!=0 and spectrum[k]-dark[k]!=0:
                abs_spectrum[k] = math.log10(abs((ref_spec[k]-dark[k])/(spectrum[k]-dark[k])))
        else:
            if ref_spec[k]!=0 and spectrum[k]!=0:
                abs_spectrum[k] = math.log10(abs(ref_spec[k]/spectrum[k]))
    abs_spectrum_round = [round(a,5) for a in abs_spectrum]
    t1=time.time()
    dt=t1-t0
    return abs_spectrum_round, dt

def correct_spectrum_from_dilution(spec,dil):
    """spec is a spectrum : list of float, dil is a float
    returns a list of float"""
    #N=len(spec)
    #cs=[spec[k]*dil for k in range(N)]
    cs=[s*dil for s in spec]
    return cs

def correct_spectra_from_dilution(spec,dil):
    #spec[list] spectres d'absorbance
    #dil[list float] facteurs de dilution
    #print(spec,dil)
    N=len(spec)
    print(N,dil)
    if N!=len(dil):
        raise IndexError
    elif N>=1:
        cs=[[0 for i in range(len(spec[0]))] for k in range(N)]
        for k in range(N): #nb of measures
            for i in range(len(spec[0])):
                #print(i,k)
                cs[k][i]=spec[k][i]*dil[k] #from beer-lambert law
        return cs

def plot_spectrum(wl, spectrum):
    sp = np.array(spectrum)#tracé
    plt.plot(wl,sp)
    plt.ylabel("Spectre d'intensité (unit counts)")
    plt.xlabel("Longueur d'onde (nm)")
    #print("isinteractive=",plt.isinteractive())
    plt.plot(block=False)
    return 1

"""
#modélise le pH en fonction de la concentration en soude d'une solution de 50mL eau + 0.050mL de HCl à 0.1M
# x = [NaOH]+[Na-] (mol/L)

#fonction sigmoïde
def func(x, a, b, l, x0):
    return a + b/(1+10**(-l*(x-x0)))

def func_acid(x, a, b, x0):
    #for x<2x0
    return a-b*np.log10((2*x0-x)/x0)

def func_base(x, a, b, x0, l): #, x0):
    #for x>x0-l
    return a+b*np.log10(1+(x-x0)/l)

#def get_equivalence_point(xdata,ydata):
    #xdata et ydata sont des np.array

#fonction en 2 parties
def pH(x, a, b, x0):


if __name__ == "__main__":
     
    from scipy.optimize import curve_fit
    
    #Define the data to be fit
    xdata = np.array([0,0.000218,0.000396,0.000559,0.000722,0.000813,0.000931,0.001156,0.001466,0.001822,0.001822,0.002696,0.002696,0.005389,0.005389])
    ydata=np.array([4.1,4.22,4.42,4.75,5.42,6,6.45,6.95,7.55,8,8,8.4,8.4,8.8,8.8])
    plt.plot(xdata, ydata, 'bo', label='data')
    xacid=np.array(xdata[0:5]);xbase=np.array(xdata[5:14]) #0...4 et 5...11
    yacid=np.array(ydata[0:5]);ybase=np.array(ydata[5:14])

    print(xacid,yacid,xbase,ybase)
    
    #Constrain
    popt_acid, pcov =curve_fit(func_acid, xacid, yacid, p0=[4.5,2.5,0.001], bounds=([0,0,0.000001], [10, 10, 0.001]))
    popt_base, pcov =curve_fit(func_base, xbase, ybase, p0=[6,1,0.001,1], bounds=([-100,0,0.0005,0.0001], [100, 10, 0.0015, 1]))
    print("popt_acid=",popt_acid)
    print("popt_base=",popt_base)
    print("function base=",func_base(xbase, *popt_base))
    plt.plot(xacid, func_acid(xacid, *popt_acid), 'g--', label='fit: a=%5.3f, b=%5.3f, x0=%5.5f' % tuple(popt_acid))
    plt.plot(xbase, func_base(xbase, *popt_base), 'r--', label='fit: a=%5.3f, b=%5.3f, x0==%5.5f, l=%5.5f' % tuple(popt_base))
    plt.xlabel('[NaOH]+[Na-] (mol/L)')
    plt.ylabel('pH')
    plt.legend()
    plt.title("évolution du pH en fonction de la concentration de titrant NaOH")
    plt.show()

    #résultat du fit 
    #acid : x0=3.90*10**-4

    #à reprendre plus tard
    #Il faut faire un seul fit pour les deux parties du graphe
    #1. Déterminer un point d'équivalence
    #2. construire une fonction en 2 parties de part à d'autres de ce point d'équivalence. """