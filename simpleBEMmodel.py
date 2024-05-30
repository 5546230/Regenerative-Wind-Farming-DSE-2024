# import necessary libraries
import matplotlib.pyplot as plt
import numpy as np  
import inputs_BEM_powerCurve as inps
#inputs : change chord, twist, airfoils, Uinf, TSR, 


root_boundary_R = 0.4
mid_boundary_R = 0.75

iteration = inps.iteration 


def CTfunction(a, glauert = False):
    """
    This function calculates the thrust coefficient as a function of induction factor 'a'
    'glauert' defines if the Glauert correction for heavily loaded rotors should be used; default value is false
    """
    CT = np.zeros(np.shape(a))
    CT = 4*a*(1-a)  
    if glauert:
        CT1=1.816
        a1=1-np.sqrt(CT1)/2
        CT[a>a1] = CT1-4*(np.sqrt(CT1)-1)*(1-a[a>a1])
    
    return CT
  
    
def ainduction(CT):
    """
    This function calculates the induction factor 'a' as a function of thrust coefficient CT 
    including Glauert's correction
    """
    a = np.zeros(np.shape(CT))
    CT1=1.816
    CT2=2*np.sqrt(CT1)-CT1
    a[CT>=CT2] = 1 + (CT[CT>=CT2]-CT1)/(4*(np.sqrt(CT1)-1))
    a[CT<CT2] = 0.5-0.5*np.sqrt(1-CT[CT<CT2])
    return a





def PrandtlTipRootCorrection(r_R, rootradius_R, tipradius_R, TSR, NBlades, axial_induction):
    """
    This function calcualte steh combined tip and root Prandtl correction at agiven radial position 'r_R' (non-dimensioned by rotor radius), 
    given a root and tip radius (also non-dimensioned), a tip speed ratio TSR, the number lf blades NBlades and the axial induction factor
    """
    # if axial_induction > 1:
        #print("invalid induction")
        
    
    temp1 = -NBlades/2*(tipradius_R-r_R)/r_R*np.sqrt( 1+ ((TSR*r_R)**2)/((1-np.clip(axial_induction, 0, 0.999))**2))
    Ftip = np.array(2/np.pi*np.arccos(np.exp(temp1)))
    Ftip[np.isnan(Ftip)] = 0
    temp1 = NBlades/2*(rootradius_R-r_R)/r_R*np.sqrt( 1+ ((TSR*r_R)**2)/((1-np.clip(axial_induction, 0, 0.999))**2))
    Froot = np.array(2/np.pi*np.arccos(np.exp(temp1)))
    Froot[np.isnan(Froot)] = 0
    return Froot*Ftip, Ftip, Froot




# import polar

import pandas as pd


def import_polar_data(airfoil_file):
    data = pd.read_csv(airfoil_file, header=0, names=["alfa", "cl", "cd", "cm"], sep=',')
    return data['alfa'], data['cl'], data['cd']

# Define polar data for root, mid, and tip
polar_alpha_root, polar_cl_root, polar_cd_root = import_polar_data('s818.csv')
polar_alpha_mid, polar_cl_mid, polar_cd_mid = import_polar_data('s816.csv')
polar_alpha_tip, polar_cl_tip, polar_cd_tip = import_polar_data('s817.csv')


def loadBladeElement(vnorm, vtan, r_R, chord, twist):
    """
    calculates the load in the blade element
    """
    # Select the appropriate airfoil data based on radial position. This is the added code
    if r_R <= root_boundary_R:
        polar_alpha, polar_cl, polar_cd = polar_alpha_root, polar_cl_root, polar_cd_root
    elif root_boundary_R < r_R <= mid_boundary_R:
        polar_alpha, polar_cl, polar_cd = polar_alpha_mid, polar_cl_mid, polar_cd_mid
    else:
        polar_alpha, polar_cl, polar_cd = polar_alpha_tip, polar_cl_tip, polar_cd_tip

    vmag2 = vnorm**2 + vtan**2
    inflowangle = np.arctan2(vnorm,vtan)
    alpha = twist + inflowangle*180/np.pi
    cl = np.interp(alpha, polar_alpha, polar_cl)
    cd = np.interp(alpha, polar_alpha, polar_cd)
    lift = 0.5*vmag2*cl*chord
    drag = 0.5*vmag2*cd*chord
    fnorm = lift*np.cos(inflowangle)+drag*np.sin(inflowangle)
    ftan = lift*np.sin(inflowangle)-drag*np.cos(inflowangle)
    gamma = 0.5*np.sqrt(vmag2)*cl*chord
    return fnorm , ftan, gamma

# Set radial boundaries for different airfoils

# define function to determine load in the blade element

induction_factors = []
def solveStreamtube(Uinf, r1_R, r2_R, rootradius_R, tipradius_R , Omega, Radius, NBlades, chord, twist, polar_alpha, polar_cl, polar_cd ):
    """
    solve balance of momentum between blade element load and loading in the streamtube
    input variables:
    Uinf - wind speed at infinity
    r1_R,r2_R - edges of blade element, in fraction of Radius ;
    rootradius_R, tipradius_R - location of blade root and tip, in fraction of Radius ;
    Radius is the rotor radius
    Omega -rotational velocity
    NBlades - number of blades in rotor
    """
    Area = np.pi*((r2_R*Radius)**2-(r1_R*Radius)**2) #  area streamtube
    r_R = (r1_R+r2_R)/2 # centroide
    # print(r_R)
    # initiatlize variables
    a = 0.0 # axial induction
    aline = 0.0 # tangential induction factor
    
    Niterations = 100
    Erroriterations =0.00001 # error limit for iteration rpocess, in absolute value of induction
    
    for i in range(Niterations):
        # ///////////////////////////////////////////////////////////////////////
        # // this is the block "Calculate velocity and loads at blade element"
        # ///////////////////////////////////////////////////////////////////////
        Urotor = Uinf*(1-a) # axial velocity at rotor
        Utan = (1+aline)*Omega*r_R*Radius # tangential velocity at rotor
        # calculate loads in blade segment in 2D (N/m)
        fnorm, ftan, gamma = loadBladeElement(Urotor, Utan, r_R,chord, twist)
        load3Daxial =fnorm*Radius*(r2_R-r1_R)*NBlades # 3D force in axial direction
        # load3Dtan =loads[1]*Radius*(r2_R-r1_R)*NBlades # 3D force in azimuthal/tangential direction (not used here)
      
        # ///////////////////////////////////////////////////////////////////////
        # //the block "Calculate velocity and loads at blade element" is done
        # ///////////////////////////////////////////////////////////////////////

        # ///////////////////////////////////////////////////////////////////////
        # // this is the block "Calculate new estimate of axial and azimuthal induction"
        # ///////////////////////////////////////////////////////////////////////
        # // calculate thrust coefficient at the streamtube 
        CT = load3Daxial/(0.5*Area*Uinf**2)
        
        # calculate new axial induction, accounting for Glauert's correction
        anew =  ainduction(CT)
        
        # correct new axial induction with Prandtl's correction
        Prandtl, Prandtltip, Prandtlroot = PrandtlTipRootCorrection(r_R, rootradius_R, tipradius_R, Omega*Radius/Uinf, NBlades, anew)
        if (Prandtl < 0.0001): 
            Prandtl = 0.0001 # avoid divide by zero
        anew = anew/Prandtl # correct estimate of axial induction
        a = 0.75*a+0.25*anew # for improving convergence, weigh current and previous iteration of axial induction
        #a = np.min(a,1)
        # calculate aximuthal induction
        aline = ftan*NBlades/(2*np.pi*Uinf*(1-a)*Omega*2*(r_R*Radius)**2)
        aline =aline/Prandtl # correct estimate of azimuthal induction with Prandtl's correction
        # ///////////////////////////////////////////////////////////////////////////
        # // end of the block "Calculate new estimate of axial and azimuthal induction"
        # ///////////////////////////////////////////////////////////////////////
        
        #// test convergence of solution, by checking convergence of axial induction
        if (np.abs(a-anew) < Erroriterations): 
            
            break

    return [a , aline, r_R, fnorm , ftan, gamma]



# define the blade geometry
delta_r_R = .01
r_R = np.arange(0.2, 1+delta_r_R/2, delta_r_R)
pitch = inps.pitch # degrees
tip_chord = inps.tip_chord
root_chord  = inps.root_chord
root_twist = inps.root_twist
chord_distribution = root_chord*(1-r_R)+tip_chord # meters
twist_distribution = root_twist*(1-r_R)+pitch # degrees
Uinf = inps.V_RATED # unperturbed wind speed in m/s
TSR = inps.TSR # tip speed ratio
Radius = inps.init_Radius
Omega = Uinf*TSR/Radius
NBlades = 3

TipLocation_R =  1
RootLocation_R =  0.2


# blade shape


# print(twist_distribution)


# define flow conditions



# solve BEM model

def BEMsolver(radius, chord_distribution, twist_distribution, omega):

    results =np.zeros([len(r_R)-1,6]) 

    for i in range(len(r_R)-1):
        r_avg = (r_R[i] + r_R[i+1]) / 2  # Midpoint of the radial segment
        
        # Interpolate chord and twist distribution
        chord = np.interp(r_avg, r_R, chord_distribution)
        twist = np.interp(r_avg, r_R, twist_distribution)

        # Select appropriate airfoil data based on radial position
        if r_avg <= root_boundary_R:
            polar_alpha = polar_alpha_root
            polar_cl = polar_cl_root
            polar_cd = polar_cd_root
        elif root_boundary_R < r_avg <= mid_boundary_R:
            polar_alpha = polar_alpha_mid
            polar_cl = polar_cl_mid
            polar_cd = polar_cd_mid
        else:
            polar_alpha = polar_alpha_tip
            polar_cl = polar_cl_tip
            polar_cd = polar_cd_tip

        # Call the solveStreamtube function with the selected airfoil data
        results[i, :] = solveStreamtube(Uinf, r_R[i], r_R[i+1], RootLocation_R, TipLocation_R, omega, radius, NBlades, chord, twist, polar_alpha, polar_cl, polar_cd)
    return results
Radiuss = Radius
if iteration:
    iterations = 1000
    
    for ix in range(iterations):
        Radiuss_init = Radiuss
        resultss = BEMsolver(Radiuss, chord_distribution, twist_distribution, Omega)
        areas = (r_R[1:]**2-r_R[:-1]**2)*np.pi*Radiuss**2
        dr = (r_R[1:]-r_R[:-1])*Radiuss
        CP = np.sum(dr*resultss[:,4]*resultss[:,2]*NBlades*Radiuss*Omega/(0.5*Uinf**3*np.pi*Radiuss**2))
        #CP = np.clip(CP,0.01, 0.999)
        AREA = inps.P_RATED/(CP*0.5*inps.rho*inps.V_RATED**3)
        Radiuss = np.sqrt(AREA/(np.pi*inps.n_rotors))
        if np.abs(Radiuss-Radiuss_init) < 0.01:
            break

results = BEMsolver(Radiuss, chord_distribution, twist_distribution, Omega)
Radius = Radiuss
print(f'{Radius=}')

# plot results


areas = (r_R[1:]**2-r_R[:-1]**2)*np.pi*Radius**2
dr = (r_R[1:]-r_R[:-1])*Radius
CT = np.sum(dr*results[:,3]*NBlades/(0.5*Uinf**2*np.pi*Radius**2))
CP = np.sum(dr*results[:,4]*results[:,2]*NBlades*Radius*Omega/(0.5*Uinf**3*np.pi*Radius**2))
a_total = ainduction(CT)
print(f'{a_total=}')
print("CT is ", CT)
print("CP is ", CP)



optimize = inps.optimize
def CPCT_function(root_chord, tip_chord, root_twist, pitch):
    areas = (r_R[1:]**2-r_R[:-1]**2)*np.pi*Radius**2
    dr = (r_R[1:]-r_R[:-1])*Radius
    chord_distribution = root_chord*(1-r_R)+tip_chord # meters
    twist_distribution = root_twist*(1-r_R)+pitch # degrees
    results = BEMsolver(Radius, chord_distribution, twist_distribution, Omega)
    CT = np.sum(dr*results[:,3]*NBlades/(0.5*Uinf**2*np.pi*Radius**2))
    CP = np.sum(dr*results[:,4]*results[:,2]*NBlades*Radius*Omega/(0.5*Uinf**3*np.pi*Radius**2))
    return CP, CT



def objective_function(inputs):
    root_chord, tip_chord, root_twist, pitch = inputs
    CP_o, CT_o = CPCT_function(root_chord, tip_chord, root_twist, pitch)
    return -CP_o+CT_o

from scipy.optimize import minimize
if optimize:
    initial_guess = np.array([inps.root_chord, inps.tip_chord, inps.root_twist, inps.pitch])
    bounds = np.array([(2,6),(1,3),(-25,25),(-10,25)])
    result = minimize(objective_function, initial_guess,bounds = bounds, method='SLSQP')
    optimal_inputs = result.x
    optimal_CP, optimal_CT = CPCT_function(optimal_inputs[0], optimal_inputs[1], optimal_inputs[2], optimal_inputs[3])
    print(f'{optimal_inputs=},{optimal_CP=}, {optimal_CT=}')


def BEMsolver_ale(pitch_ale):
    radius = Radius
    omega = Omega
    
    twist_distribution = root_twist*(1-r_R)+pitch_ale # degrees
    results =np.zeros([len(r_R)-1,6]) 

    for i in range(len(r_R)-1):
        r_avg = (r_R[i] + r_R[i+1]) / 2  # Midpoint of the radial segment
        
        # Interpolate chord and twist distribution
        chord = np.interp(r_avg, r_R, chord_distribution)
        twist = np.interp(r_avg, r_R, twist_distribution)

        # Select appropriate airfoil data based on radial position
        if r_avg <= root_boundary_R:
            polar_alpha = polar_alpha_root
            polar_cl = polar_cl_root
            polar_cd = polar_cd_root
        elif root_boundary_R < r_avg <= mid_boundary_R:
            polar_alpha = polar_alpha_mid
            polar_cl = polar_cl_mid
            polar_cd = polar_cd_mid
        else:
            polar_alpha = polar_alpha_tip
            polar_cl = polar_cl_tip
            polar_cd = polar_cd_tip

        # Call the solveStreamtube function with the selected airfoil data
        results[i, :] = solveStreamtube(Uinf, r_R[i], r_R[i+1], RootLocation_R, TipLocation_R, omega, radius, NBlades, chord, twist, polar_alpha, polar_cl, polar_cd)
        dr_ale = (r_R[1:]-r_R[:-1])*Radius
        CT_ale = np.sum(dr_ale*results[:,3]*NBlades/(0.5*Uinf**2*np.pi*Radius**2))
    return CT_ale
from scipy.interpolate import RectBivariateSpline
from scipy.io import savemat
ale_shit = inps.ale_shit
if ale_shit:
    delta_r_R = .01
    r_R = np.arange(0.2, 1+delta_r_R/2, delta_r_R)
    pitch_ale = np.linspace(-6, 6, 10)
    TSR_ale = np.linspace(6, 9, 4)
    omega_ale = Uinf*TSR_ale/Radius
    
    results_ales = array = np.zeros((len(pitch_ale), len(omega_ale)))
    for x in range(len(pitch_ale)):
        for y in range(len(omega_ale)):
            resultss = BEMsolver_ale(Radius, chord_distribution,pitch_ale[x], omega_ale[y])
            CT_ale = np.sum(dr*resultss[:,3]*NBlades/(0.5*Uinf**2*np.pi*Radius**2))
            results_ales[x,y] = CT_ale

    interp_spline = RectBivariateSpline(pitch_ale, TSR_ale, results_ales)
    coefficients = interp_spline.get_coeffs()
    #print(coefficients)
    savemat('alemat.mat', {'coefficients': coefficients, 'pitch': pitch_ale, 'TSR': TSR_ale})
if np.max(results[:,0])>0.4:
    print("MODEL INVALID")

rotor_solidity = (3*(np.min(chord_distribution) + np.max(chord_distribution))/2*0.8*Radius)/(np.pi*Radius**2-np.pi*(0.2*Radius)**2)
print(chord_distribution)
print(f'{rotor_solidity=}')
if optimize:
    chord_distribution = optimal_inputs[0]*(1-r_R)+optimal_inputs[1] # meters
    print(chord_distribution)
    rotor_solidity = (3*(np.min(chord_distribution) + np.max(chord_distribution))/2*0.8*Radius)/(np.pi*Radius**2-np.pi*(0.2*Radius)**2)
    print(f'{rotor_solidity=}')



pitch_ales = np.arange(-10,25,1)
CT_ales = []
for i in range(len(pitch_ales)):
    CT_ales.append(BEMsolver_ale(pitch_ales[i]))

CT_ales = np.array(CT_ales)
print(CT_ales)
plt.plot(pitch_ales, CT_ales)
plt.show()
