# -*- coding: utf-8 -*-
"""
Created on Mon Sep 25 12:48:19 2017
 
@author: permyakov.aleksandr
"""
 
 
import math
import sys
 
def todB(x):
    """
    Convert numeric value x to dB.
    Input: float x > 0
    Output: returns 10 * log(x), log - 10-based.
    """
    return 10.0 * math.log(x, 10)
 
def fromdB(x):
    """
    Convert numeric value x from dB.
    Input: float x.
    Outupt: returns 10 ** (x / 10)
    """
    return 10.0 ** (x / 10.0)
 
def sumPower(lambdaPowers):
     
    """
    Function sums powers of signals given in dBm. It converts them to mWt for addition and then converts the result to dBm back.
    Input: lambdaPowers - dictionary of powers of sources of signal, in dBm: keys - strings of wavelengths, like "1531.12nm", values - powers of signals of corresponding wavelengths, in dBm.
    Output: returns total power of signals, in dBm.
    """
    totalPower = 0
    for lmbda in lambdaPowers.keys():
        totalPower += fromdB(lambdaPowers[lmbda])
    return todB(totalPower)
 
def divPower(inPower, lambdaPowers):
    """
    Function divides input Power of DWDM MUX on the receive side to powers of separate signals proportionally to the powers of signals on the transmit side.
    Input:
        inPower - summarized signal power;
        lambdaPowers - dictionary of powers of sources of signal, in dBm: keys - strings of wavelengths, like "1531.12nm", values - powers of signals of corresponding wavelengths, in dBm.
    Output: returns a dictionary: keys - strings of wavelengths, like "1531.12nm", values - powers of signals of corresponding wavelengths, in dBm.
    """
    
    # Total power of the signal on the transmit side.
    totalPower = fromdB(sumPower(lambdaPowers))
    rxPowers = {}
    inPowerMw = fromdB(inPower)
    for lmbda in lambdaPowers.keys():
        rxPowers[lmbda] = todB(inPowerMw * fromdB(lambdaPowers[lmbda]) / totalPower)
    return rxPowers
 
def OSNR(pdB=0, nfdB=5.5):
    """
    Function calculates OSNR ratio for one EDFA amplifier.
    Input: pdB = power on the EDFA input, in dBm, nfdB = noise figure of the EDFA, in dBm.
    Output: returns OSNR in dB.
    """
 
    c = 3 * 10.0 ** 8 # The speed of light in the vacuum.
    l = 1550 * 10.0 ** (-9) # A wavelength of the signal.
    h = 6.26 * 10.0 ** (-34) # The Plank's constant.
    n = c / l # A frequency of the signal.
    dn = 12.5 * 10.0 ** 9 # The reference frequency of measurement of the noise on the EDFA.
    # For OSNR calculation all values must be converted from dB to numeric values.
    NF = fromdB(nfdB)
    pmW = fromdB(pdB)
    pW = pmW / 1000.0 # Convert from mWatts to Watts.
    OSNR = pW / (NF * h * n * dn) # Formula for OSNR calculation.
    OSNRdB = todB(OSNR)
    return OSNRdB
 
def addOSNR(OSNR1dB, OSNR2dB):
    """
    Function calculates the total OSNR of two OSNR ratios (on two EDFA amplifiers).
    The formula is: 1 / OSNR = 1 / OSNR1 + 1 / OSNR2.
    Input: OSNR1, OSNR2, in dB.
    Output: A total OSNR, in dB.
    """
     
    # Convert OSNR from dB to a numeric value.
    OSNR1 = fromdB(OSNR1dB)
    OSNR2 = fromdB(OSNR2dB)
    OSNR = OSNR1 * OSNR2 / (OSNR1 + OSNR2)
    return todB(OSNR) 
 
def totalOSNR(EDFAlist):
    """
    Function calculates OSNR ratio for the link with several EDFA amplifiers.
    Input: EDFAlist - list of tuples of parameters (Input Power in dBm, Noise Factor in dB) of EDFA amplifiers.
    Output: returns total OSNR of the link, in dB.
    """
     
    OSNRtotal = OSNR(EDFAlist[0][0], EDFAlist[0][1])
     
    if len(EDFAlist) == 1:
        return OSNRtotal
    else:
        for i in range(1, len(EDFAlist)):
            OSNRnext = OSNR(EDFAlist[i][0], EDFAlist[i][1])
            OSNRtotal = addOSNR(OSNRtotal, OSNRnext)
             
        return OSNRtotal
     
def totalOSNRlambda(EDFAlist, lambdaPowers):
    """
    Function calculates OSNR ratio for the separate lambdas on the link with several EDFA amplifiers.
    Input:
        EDFAlist - list of tuples of parameters (Input Power in dBm, Noise Factor in dB) of EDFA amplifiers.
        lambdaPowers - dictionary of powers of sources of signal, in dBm: keys - strings of wavelengths, like "1531.12nm", values - powers of signals of corresponding wavelengths, in dBm.
    Output: returns a dictionary: keys - strings of wavelengths, like "1531.12nm", values - total OSNR of signal of corresponding wavelengths on the whole link, in dBm.
    """
     
    #Dictionary of EDFAlists for each lambda.
    lambdaEDFA = {}
    for lmbda in lambdaPowers.keys():
        lambdaEDFA[lmbda] = []
         
    # A dictionary for the result.
    lambdaOSNR ={}
     
    # Prepare EDFAlists for each lambda
    for EDFA in EDFAlist:
        inPowers = divPower(EDFA[0], lambdaPowers)
         
        for lmbda in inPowers.keys():
            lambdaEDFA[lmbda].append((inPowers[lmbda], EDFA[1],))
     

    # Calculate total OSNR for each lambda.
    for lmbda in lambdaEDFA.keys():  
        lambdaOSNR[lmbda] = totalOSNR(lambdaEDFA[lmbda])
     
    return lambdaOSNR


def calculation(json):
    """
    Main function of the program.
     
    Getting input and output file names from the user.
    Reading an input file.
    Parsing input data.
    Calculation of the loss, dispersion and OSNR for each lambda.
    Printing results to an output file.
    """
    txPowers = {"lambda1": 0}
    attTxTrans = {"lambda1": 0}
    dwdmMUXilTx = 2.5
    attTx = 0
    edfaDBinP = -2.5
    edfaDBgain = 19.5
    edfaDBoutP = 17
    edfaDBnf = 5.5
    brFilterILTx = 1.5
    optFiberLength = {"span1": 100}
    optFiberLoss = {"span1": 0.3}
    optFiberDisp = {"span1": 18}
    brFilterILRx = 1.5
    edfaDAinP = -16.0
    edfaDAgain = 25.0
    edfaDAoutP = 9.0
    edfaDAnf = 5.5
    DCMil = 9.0
    DCMdisp = -1315
    dwdmMUXilRx = 2.5
    attRxTrans = {"lambda1": 5}
    outputText = [] # List of strings to write.
    lines = []
    for line in json:
        s=''
        if type(json[line]) == list:
            for item in json[line]:
                s += item.lstrip()+' '
        else:
            s = json[line].lstrip()
        outputText.append(line)
        indx = s.find(":")
        prfx = line
        if len(s) > indx+1:
            strparam = s[indx+1:]
            lstrparams = s.split()

            lparams = []
            for l in lstrparams:
                lparams.append(float(l))
        if prfx == "tx_power":
            for i in range(len(lparams)):
                txPowers["lambda" + str(i+1)] = lparams[i]
        elif prfx == "attenuators_tx":
            for i in range(len(lparams)):
                attTxTrans["lambda" + str(i+1)] = lparams[i]
        elif prfx == "dwdm_tx_loss":
            if len(lparams) > 0:
                dwdmMUXilTx = lparams[0]
        elif prfx == "attenuator_tx":
            if len(lparams) > 0:
                attTx = lparams[0]
        elif prfx == "edfa_db_input_power":
            if len(lparams) > 0:
                 edfaDBinP = lparams[0]
        elif prfx == "edfa_db_gain":
            if len(lparams) > 0:
                 edfaDBgain = lparams[0]
        elif prfx == "edfa_db_output_power":
            if len(lparams) > 0:
                 edfaDBoutP = lparams[0]
        elif prfx == "edfa_db_nf":
            if len(lparams) > 0:
                 edfaDBnf = lparams[0]
        elif prfx == "blue_red_tx_loss":
            if len(lparams) > 0:
                 brFilterILTx = lparams[0]
        elif prfx == "fiber_length":
            for i in range(len(lparams)):
                optFiberLength["span" + str(i+1)] = lparams[i]
        elif prfx == "fiber_loss":
            for i in range(len(lparams)):
                optFiberLoss["span" + str(i+1)] = lparams[i]
        elif prfx == "fiber_dispersion":
            for i in range(len(lparams)):
                optFiberDisp["span" + str(i+1)] = lparams[i]
        elif prfx == "blue_red_rx_loss":
            if len(lparams) > 0:
                 brFilterILRx = lparams[0]
        elif prfx == "edfa_da_input_power":
            if len(lparams) > 0:
                 edfaDAinP = lparams[0]
        elif prfx == "edfa_da_gain":
            if len(lparams) > 0:
                 edfaDAgain = lparams[0]
        elif prfx == "edfa_da_output_power":
            if len(lparams) > 0:
                 edfaDAoutP = lparams[0]
        elif prfx == "edfa_da_nf":
            if len(lparams) > 0:
                 edfaDAnf = lparams[0]
        elif prfx == "dcm_loss":
            if len(lparams) > 0:
                 DCMil = lparams[0]
        elif prfx == "dcm_dispersion":
            if len(lparams) > 0:
                 DCMdisp = lparams[0]
        elif prfx == "dwdm_rx_loss":
            if len(lparams) > 0:
                dwdmMUXilRx = lparams[0]
        elif prfx == "attenuators_rx":
            for i in range(len(lparams)):
                attRxTrans["lambda" + str(i+1)] = lparams[i]
    lambdaPowers = {}
    for lmbda in txPowers.keys():
        lambdaPowers[lmbda] = txPowers[lmbda] - attTxTrans.get(lmbda, 0)
    edfaDBinP = sumPower(lambdaPowers) - dwdmMUXilTx - attTx
    edfaDBoutP = edfaDBinP + edfaDBgain
    totalOptFiberLoss = 0
    totalOptFiberDisp = 0
    for span in optFiberLength.keys():
        totalOptFiberLoss += optFiberLength[span] * optFiberLoss.get(span, 0.3)
        totalOptFiberDisp += optFiberLength[span] * optFiberDisp.get(span, 18)
    edfaDAinP = edfaDBoutP - brFilterILTx - totalOptFiberLoss - brFilterILRx
    edfaDAoutP = edfaDAinP + edfaDAgain
    rxPowers = divPower(edfaDAoutP - DCMil - dwdmMUXilRx, lambdaPowers)
    for lmbda in rxPowers.keys():
        rxPowers[lmbda] -= attRxTrans.get(lmbda, 0)
    rxDispersion = {}
    for lmbda in rxPowers.keys():
        rxDispersion[lmbda] = totalOptFiberDisp + DCMdisp
    EDFAlist = [(edfaDBinP, edfaDBnf), (edfaDAinP, edfaDAnf)]
    rxOSNR = totalOSNRlambda(EDFAlist, lambdaPowers)
    output_dict = {}
    for count in json:
        if json.get(count) == -1:
            continue
        output_dict["Transceivers Tx Power"] = ' '.join(json['tx_power'])
        output_dict["Attenuators Tx Transceiver"] = json['attenuators_tx']
        output_dict["DWDM MUX Tx Internal Loss"] = json['dwdm_tx_loss']
        output_dict["Attenuator Tx"] = json['attenuator_tx']
        output_dict["EDFA-DB Input Power"] =  str(round(edfaDBinP,2))
        output_dict["EDFA-DB Gain"] = json['edfa_db_gain']
        output_dict["EDFA-DB Output Power"] = str(round(edfaDBoutP,2))
        output_dict["EDFA-DB NF"] = json['edfa_db_nf']
        output_dict["Blue/Red Tx Internal Loss"] = json['blue_red_tx_loss']
        output_dict["Optical Fiber Length"] = json['fiber_length']
        output_dict["Optical Fiber Loss"] = json['fiber_loss']
        output_dict["Optical Fiber Chromatic Dispersion"] = json['fiber_dispersion']
        output_dict["Blue/Red Rx Internal Loss"] = json['blue_red_rx_loss']
        output_dict["EDFA-DA Input Power"] = str(round(edfaDAinP,2))
        output_dict["EDFA-DA Gain"] = json['edfa_da_gain']
        output_dict["EDFA-DA Output Power"] = str(round(edfaDAoutP,2))
        output_dict["EDFA-DA NF"] = json['edfa_da_nf']
        output_dict["DCM Internal Loss"] = json['dcm_loss']
        output_dict["DCM Chromatic Dispersion"] = json['dcm_dispersion']
        output_dict["DWDM MUX Rx Internal Loss"] = json['dwdm_rx_loss']
        output_dict["Attenuators Rx Transceivers"] = json['attenuators_rx']
        output_dict["Transceivers Rx Power"] = ''
        output_dict["Transceivers Rx OSNR"] = ''
        output_dict["Transceivers Rx Chromatic Dispersion"] = ''
        for lmbda in rxPowers.keys():
            output_dict["Transceivers Rx Power"] += ' ' + str(round(rxPowers[lmbda],2))
        for lmbda in rxOSNR.keys():
            output_dict["Transceivers Rx OSNR"] += ' ' + str(round(rxOSNR[lmbda],2))
        for lmbda in rxDispersion.keys():
            output_dict["Transceivers Rx Chromatic Dispersion"] += ' ' + str(round(rxDispersion[lmbda],2))
    return output_dict
