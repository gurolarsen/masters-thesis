from tqdm import tqdm
import pandas as pd
import copy
from insertion_generator import InsertionGenerator
import sys
sys.path.append("C:\\Users\\agnesost\\masters-thesis")
from objects.route_plan import RoutePlan



class ConstructionHeuristic:
    def __init__(self, activities_df,  employees_df, patients_df, treatment_df, visit_df, days):
        
        self.activities_df = activities_df
        self.visit_df = visit_df
        self.treatment_df = treatment_df
        self.patients_df = patients_df
        self.employees_df = employees_df
        self.days = days
        self.route_plan = RoutePlan(days, employees_df) 
        self.current_objective = 0 
        self.listOfPatients = []
        self.unAssignedPatients = []
        
 
    def construct_initial(self): 
        '''
        Funksjonen iterer over alle paienter som kan allokeres til hjemmesykehuset. 
        Rekkefølgen bestemmes av hvor mye aggregert suitability pasienten vil tilføre ojektivet
        '''

        #Lager en liste med pasienter i prioritert rekkefølge. 
        unassigned_patients = df_patients.sort_values(by="aggSuit", ascending=False)
        print("unassigned_patients", unassigned_patients)
        #Iterer over hver pasient i lista. Pasienten vi ser på kalles videre pasient
        for i in tqdm(range(unassigned_patients.shape[0]), colour='#39ff14'):
            #Henter ut raden i pasient dataframes som tilhører pasienten
            patient = unassigned_patients.index[i] 
            patient_request = unassigned_patients.iloc[i]
            
            #Kopierer nåværende ruteplan for denne pasienten 
            route_plan_with_patient = copy.deepcopy(self.route_plan)
            #Oppretter et InsertionGenerator objekt, hvor pasient_requesten og kopien av dagens ruteplan sendes inn
            insertion_generator = InsertionGenerator(self, route_plan_with_patient, patient_request, self.treatment_df, self.visit_df, self.activities_df)
            #InsertionGenratoren forsøker å legge til pasienten, og returnerer True hvis velykket
            state = insertion_generator.generate_insertions()
            
           
            if state == True: 
                #Construksjonsheuristikkens ruteplan oppdateres til å inneholde pasienten
                self.route_plan = insertion_generator.route_plan
                #Objektivverdien oppdateres
                self.current_objective += patient_request["aggSuit"]
                #Pasienten legges til i 
                self.listOfPatients.append(patient)
                
            
            if state == False: 
                self.unAssignedPatients.append(patient)
        #Lage en insert generator som prøver å legge til pasient. 
        #Vil først få ny objektivverdi når en hel pasient er lagt til, så gir mening å kalle den her
        return self.route_plan, self.current_objective
    
    #IDE: Må lage en generate insertion, som kan ta inn en liste med aktiviteter. 
    #Forskjellen på vår og deres er at det blir veldig raskt ugylldig 
   
'''
Ruten oppdateres selv om pasienten ikke legges til. Construct iital henter ut ritkig state

Det er ikke gjensidig avhengighet. Fordi nå hentes alt fra contriction, og sendes inn
Problem state blir aldri sant for treatment 8, likevel så legges aktivitet 13 og 14 til. 
Den oppdaterte ruten med disse verdiene tar steget videre 
'''

#Disse skal ikk her men limer innforeløpig
df_activities  = pd.read_csv("data/NodesNY.csv").set_index(["id"]) 
df_employees = pd.read_csv("data/EmployeesNY.csv").set_index(["EmployeeID"])
df_patients = pd.read_csv("data/Patients.csv").set_index(["patient"])
df_treatments = pd.read_csv("data/Treatment.csv").set_index(["treatment"])
df_visits = pd.read_csv("data/Visit.csv").set_index(["visit"])

print(df_activities.index)
testConsHeur = ConstructionHeuristic(df_activities, df_employees, df_patients, df_treatments, df_visits, 5)
route_plan, obj = testConsHeur.construct_initial()
testConsHeur.route_plan.printSoultion()
print("Dette er objektivet", testConsHeur.current_objective)
print("Hjemmesykehuspasienter ", testConsHeur.listOfPatients)
print("Ikke allokert ", testConsHeur.unAssignedPatients)

#TODO: printe routeplan for å se om det ble noe 


#TODO: Fikse slik at pasienter enten er med eller ikkke. 
#Må få igang state variablene

'''
Arbeid: 

TODO: Usikker på om employeerestrictions slår inn eller ikke. Det må vi sjekke 

TODO: Tror vi ville fått feil i ruteobjektet hele det første visitet var mulig. 
Slik at det legger seg inn også få neste plass i et annet pattern. Da blir det duplisert,
MÅ sjekkes ut 


Tror derfor at route_objektet må være på hvert pattern, og ikke på hver 

Merk: Resultater av kjøring på første datasett tar ikke inn noen med presedens 
'''