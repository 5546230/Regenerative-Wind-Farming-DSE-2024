# this program will calculate thrust power and torque

import numpy as np

import circlesinsqure as c
def CTfunction(a, glauert = False):
    """
    This function calculates the thrust coefficient as a function of induction factor 'a'
    'glauert' defines if the Glauert correction for heavily loaded rotors should be used; default value is false
    """
    CT = np.zeros(np.shape(a))
    CT = 4*a*(1-a)  
    # if glauert:
    #     CT1=1.816;
    #     a1=1-np.sqrt(CT1)/2;
    #     CT[a>a1] = CT1-4*(np.sqrt(CT1)-1)*(1-a[a>a1])
    
    return CT
  
    
def ainduction(CT):
    """
    This function calculates the induction factor 'a' as a function of thrust coefficient CT 
    including Glauert's correction
    """
    a = np.zeros(np.shape(CT))
    CT1=1.816;
    CT2=2*np.sqrt(CT1)-CT1
    a[CT>=CT2] = 1 + (CT[CT>=CT2]-CT1)/(4*(np.sqrt(CT1)-1))
    a[CT<CT2] = 0.5-0.5*np.sqrt(1-CT[CT<CT2])
    return a

rho = 1.225 #SI units
radius = c.radius1 #si units
nrotors = c.n
Uinf = 9 #si units
Power = 0.631145 *10**6 #Watts
assumed_a = 0.5
Area = np.pi*radius**2*nrotors
CT = CTfunction(assumed_a)
thrust1 = CT*0.5*rho*Uinf**2*Area
thrust2 = Power/Uinf/(1-assumed_a)
print(thrust1, thrust2)

TSR = 8
omega =  Uinf*TSR/radius
Torque = Power / omega
print("Torque is ", Torque)