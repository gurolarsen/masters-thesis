import pandas as pd
import copy
import math
import numpy.random as rnd 
import random 

import os
import sys
sys.path.append( os.path.join(os.path.split(__file__)[0],'..','..','..'))  # Include subfolders

from helpfunctions import checkCandidateBetterThanCurrent
from objects.distances import *
from config.construction_config import *
from heuristic.improvement.operator.repair_generator import RepairGenerator
from heuristic.improvement.operator.insertor import Insertor

class Operators:
    def __init__(self, alns):
        self.destruction_degree = alns.destruction_degree # TODO: Skal vi ha dette?
        self.constructor = alns.constructor
        self.repair_generator = RepairGenerator(self.constructor)

    # Uses destruction degree to set max cap for removal
    def activities_to_remove(self, activities_remove):
        return activities_remove
    
#---------- REMOVE OPERATORS ----------
    """
   
    def random_route_removal(self, current_route_plan):
        destroyed_route_plan = copy.deepcopy(current_route_plan)
        routes = destroyed_route_plan.routes

        if destroyed_route_plan:
            index_list = list(range(len(routes)))
            selected_index = rnd.choice(index_list)
            removed_route = routes[selected_index]
            destroyed_route_plan.remove(removed_route)
       
        removed_activities = []
        for act in removed_route:
            removed_activities.add(act)
     
        return destroyed_route_plan, removed_activities, True
    
    def worst_route_removal(self, current_route_plan):
        destroyed_route_plan = copy.deepcopy(current_route_plan)
        routes = destroyed_route_plan.routes
        worst_route = None
        current_worst_objective = current_route_plan.objective

        for route in routes:
            route_plan_holder = copy.deepcopy(current_route_plan)
            removed_route = route_plan_holder.routes.pop(route)
            objective_removed_route = route_plan_holder.objective
            
            # If current worst objective is better than candidate, then candidate is the new current worst
            if checkCandidateBetterThanCurrent(current_worst_objective, objective_removed_route):
                worst_route = removed_route
                current_worst_objective = objective_removed_route
                destroyed_route_plan = route_plan_holder
            
        removed_activities = []
        for act in worst_route:
            removed_activities.add(act)

        return destroyed_route_plan, removed_activities, True
         """
    def random_treatment_removal(self, current_route_plan):
        destroyed_route_plan = copy.deepcopy(current_route_plan)
        selected_treatment = 5 #rnd.choice(list(destroyed_route_plan.treatments.keys())) #dette er samme som aktivtet 17 
        removed_activities = []
        
        for visit in destroyed_route_plan.treatments[selected_treatment]:
            removed_activities += destroyed_route_plan.visits[visit]
            del destroyed_route_plan.visits[visit]
        for day in range(1, destroyed_route_plan.days +1): 
            for route in destroyed_route_plan.routes[day]: 
                for act in route.route: 
                    if act.id in removed_activities:
                        route.removeActivityID(act.id)
        print("removed_activities", removed_activities)
        
        del destroyed_route_plan.treatments[selected_treatment]
        for key, value in list(destroyed_route_plan.allocatedPatients.items()):
         
            if value == [selected_treatment]:
              
                del destroyed_route_plan.allocatedPatients[key]
                destroyed_route_plan.notAllocatedPatients.append(key)
                break
            if selected_treatment in value: 
                destroyed_route_plan.illegalNotAllocatedTreatments += value
                break
        destroyed_route_plan.updateObjective()
        return destroyed_route_plan, removed_activities, True
    

    
    
#---------- REPAIR OPERATORS ----------
    def greedy_repair(self, destroyed_route_plan):
        #Tar bort removed acktivitites, de trenger vi ikk e
        repaired_route_plan = copy.deepcopy(destroyed_route_plan)
        
        # Må sjekke om aktiviteter i removed_activities har samme pasient som noen aktiviteter i route plan.allocatedpatients (hvis denne hadde flere treatments). 
        # I så fall må alle aktiviteter i hele treatmentet som ble fjernet prioriteres til å legges inn.
        # Vil kjøre insertion på treatment-nivå (TreatmentInsertions-klasse kanskje? Agnes er usikker) for å legge inn disse som har denne sammenhengen
        # Så kjøre vanlig grådig PatientInsertion

        #Forsøker å legge til de aktivitetene vi har tatt ut
        insertor = Insertor(self.constructor, repaired_route_plan)
        for treatment in repaired_route_plan.illegalNotAllocatedTreatments: 
            insertor.insert_treatment(treatment)


        #Forsøker å legge til alle pasientne som ikke ligger inne 
        
        #TODO: Prøve å shuffle på hvem som settes inn 
        insertor.insertPatients(repaired_route_plan.notAllocatedPatients)
        repaired_route_plan.updateObjective()
        '''
        route_plan, new_objective = self.repair_generator.generate_insertions(
            route_plan=route_plan, activity=activity, rid=rid, infeasible_set=infeasible_set, initial_route_plan=current_route_plan, index_removed=index_removal, objectives=0)

        # update current objective
        current_objective = new_objective
        '''

        '''
        Konseptet: 
        Vi har ulike lister med aktiviteter 
        '''
        return repaired_route_plan

