from MaxPowerControl import MaxPowerControl


MPC= MaxPowerControl()
#Carico tutte le case
prova=MPC.loadLastPowerDataHouse("H2")
# prova1=MPC.computeTotalPower("H1")
# prova2=MPC.loadHousePowerLimit("H1")
# prova3=MPC.controlLastUpdateModule("H1")
# prova4=MPC.controlPower("H1")
#prova5=MPC.updateModule("H1")
prova6=MPC.updateAllHouses()





ciao=1
