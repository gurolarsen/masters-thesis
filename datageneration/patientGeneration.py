import os
import pandas as pd
import numpy as np
import random 

import sys
sys.path.append(os.path.join(os.path.split(__file__)[0],'..') )  #include subfolders

from config import construction_config
from datageneration import employeeGeneration

import random
import numpy as np

def locationGenerator(locations, radius_km, num_points):
    """Forklaring fra chatten:
    For å generere et bestemt antall punkter innenfor arealet av en sirkel, kan vi tilpasse tilnærmingen ved 
    å bruke en metode som lar oss plassere punkter tilfeldig, men innenfor grensene av sirkelens radius. 
    Denne metoden involverer å generere tilfeldige vinkler og radiuser for hvert punkt, slik at de faller innenfor 
    den definerte sirkelen. Dette sikrer at punktene er jevnt fordelt over hele området, ikke bare langs kanten.
    Vi kan bruke polar koordinatsystemet hvor et punkt er definert av en radius fra sentrum og en vinkel i forhold 
    til en referanseakse. For å oppnå dette, genererer vi tilfeldige vinkler (i radianer) og tilfeldige radiuser 
    (som en brøkdel av den totale radiusen), og konverterer deretter disse polar koordinatene til kartesiske 
    koordinater (latitude og longitude) for å passe inn i vår geografiske kontekst"""

    points = []
    for _ in range(num_points):
        # Velger en tilfeldig lokasjon fra listen
        lat, lon = random.choice(locations)

        # Genererer en tilfeldig vinkel og radius
        angle = random.uniform(0, 2 * np.pi)
        r = radius_km * np.sqrt(random.uniform(0, 1))
        
        # Konverterer radius til radianer basert på jordens radius
        r_in_radians = r / 6371
        
        # Beregner delta for latitude og longitude
        dlat = np.sin(angle) * r_in_radians
        dlon = np.cos(angle) * r_in_radians / np.cos(np.radians(lat))
        
        # Legger til de nye punktene ved å justere fra sentralpunktet
        new_lat = round(lat + np.degrees(dlat),4)
        new_lon = round(lon + np.degrees(dlon),4)
        
        points.append((new_lat, new_lon))
        
    return points

def patientGenerator(df_employees):
    df_patients = pd.DataFrame(columns=['patientId', 'nTreatments', 'utility','employeeRestriction', 'continuityGroup', 'employeeHistory', 'heaviness', 'location'])
     
    patientId = []
    nTreatments = []
    utility = []
    continuityGroup = []
    heaviness = []

    #Generate random location for each patient
    locations = locationGenerator(construction_config.refLoc, construction_config.area, construction_config.P_num)

    for i in range(construction_config.P_num):
        patientId.append(i+1)
        
        #Distribution of number of treatments per patient
        T_numMax = construction_config.maxTreatmentsPerPatient                                          # Max number of activities per visit
        prob = construction_config.V_numProb                                                            # The probability of the number of activities per visit
        nTreatments = np.random.choice(range(1,T_numMax+1), size=construction_config.P_num, p=prob)      # Distribution of the number of activities per visit
        
        #Distribution of utility, continuity group and heaviness for patients
        utility.append(np.random.choice([j+1 for j in range(5)]))
        continuityGroup.append(np.random.choice([j+1 for j in range(3)], p=construction_config.continuityDistribution))
        heaviness.append(np.random.choice([i+1 for i in range(5)], p=construction_config.heavinessDistribution))

        df_patients = df_patients._append({
                'patientId': i+1,
                'nTreatments': nTreatments[i],
                'utility': utility[i],
                'continuityGroup': continuityGroup[i],
                'heaviness': heaviness[i],
                'location' : locations[i]
            }, ignore_index=True)
    
    # Employee Restrictions
    num_restricted_patients = int(len(df_patients) * 0.05)      # 5 % of the patients have a restriction against an employee
    restricted_patient_indices = np.random.choice(df_patients.index, size=num_restricted_patients, replace=False) # Random patients get employee restrictions
    
    for index in restricted_patient_indices:
        random_employee_id = np.random.choice(df_employees['employeeId'])   # Random employees 
        list = []
        list.append(random_employee_id)
        df_patients.at[index, 'employeeRestriction'] = list

    # Employee history  TODO: Må potensielt oppdatere format på dette
    num_history_patients = int(len(df_patients) * 0.9)          # 90 % of the patients have a treatment history with some employees
    history_patient_indices = np.random.choice(df_patients.index, size=num_history_patients, replace=False) # Random patients get employee history

    for index in history_patient_indices:
        num_employees = np.random.randint(1, 6)             # Allowing for between 1 and 6 employees in the employee history
        random_employee_ids = np.random.choice(df_employees['employeeId'], size=num_employees, replace=False).tolist()      # Random employees
        df_patients.at[index, 'employeeHistory'] = random_employee_ids

    file_path = os.path.join(os.getcwd(), 'data', 'patients.csv')
    df_patients.to_csv(file_path, index=False)

    return df_patients

def treatmentGenerator(df_patients):
    df_treatments = pd.DataFrame(columns=['treatmentId', 'patientId', 'patternType','pattern','visits', 'location'])

    # Generate rows for each treatment with the patientId
    expanded_rows = df_patients.loc[df_patients.index.repeat(df_patients['nTreatments'])].reset_index(drop=False)
    expanded_rows['treatmentId'] = range(1, len(expanded_rows) + 1)
    # Generate pattern type for each treatment. Will decide the number of visits per treatment.
    patternType = np.random.choice([i+1 for i in range(len(construction_config.patternTypes))], len(expanded_rows), p=construction_config.patternTypes)
    
    df_treatments['treatmentId'] = expanded_rows['treatmentId']
    df_treatments['patientId'] = expanded_rows['patientId']
    df_treatments['patternType'] = patternType
    df_treatments['location'] = expanded_rows['location']
    df_treatments['employeeRestriction'] = expanded_rows['employeeRestriction']
    df_treatments['heaviness'] = expanded_rows['heaviness']

    for index, row in df_treatments.iterrows():
        #Fill rows with possible patterns
        if row['patternType'] == 1:
            df_treatments.at[index, 'pattern'] = construction_config.patterns_5days
            df_treatments.at[index, 'visits'] = 5
        elif row['patternType'] == 2:
            df_treatments.at[index, 'pattern'] = construction_config.patterns_4days
            df_treatments.at[index, 'visits'] = 4
        elif row['patternType'] == 3:
            df_treatments.at[index, 'pattern'] = construction_config.patterns_3days
            df_treatments.at[index, 'visits'] = 3
        elif row['patternType'] == 4:
            df_treatments.at[index, 'pattern'] = construction_config.pattern_2daysspread
            df_treatments.at[index, 'visits'] = 2
        elif row['patternType'] == 5:
            df_treatments.at[index, 'pattern'] = construction_config.patterns_2daysfollowing
            df_treatments.at[index, 'visits'] = 2
        else:
            df_treatments.at[index, 'pattern'] = construction_config.patterns_1day
            df_treatments.at[index, 'visits'] = 1

    file_path = os.path.join(os.getcwd(), 'data', 'treatments.csv')
    df_treatments.to_csv(file_path, index=False)

    return df_treatments

def visitsGenerator(df_treatments):
    df_visits = pd.DataFrame(columns=['visitId', 'treatmentId', 'patientId', 'activities', 'location'])

    # Generate rows for each visit with the treatmentId and patientId
    expanded_rows = df_treatments.loc[df_treatments.index.repeat(df_treatments['visits'])].reset_index(drop=False)
    expanded_rows['visitId'] = range(1, len(expanded_rows) + 1)

    df_visits['visitId'] = expanded_rows['visitId']
    df_visits['treatmentId'] = expanded_rows['treatmentId']
    df_visits['patientId'] = expanded_rows['patientId']
    df_visits['location'] = expanded_rows['location']
    df_visits['employeeRestriction'] = expanded_rows['employeeRestriction']
    df_visits['heaviness'] = expanded_rows['heaviness']

    # Distribution of number of activities per visit
    A_numMax = construction_config.maxActivitiesPerVisit                        # Max number of activities per visit
    prob = construction_config.A_numProb                                        # The probability of the number of activities per visit
    V_num = df_visits.shape[0]
    activities = np.random.choice(range(1,A_numMax+1), size=V_num, p=prob)      # Distribution of the number of activities per visit
    #activities = np.random.poisson(lam=construction_config.activitiesPerVisit, size=V_num)
    # A minimum of 1 and maximum of 6 activities per visit. 
    #activities = np.maximum(activities, 1) #gjør at ingen visits har 0 aktiviteter, MEN det gjør at snittet på antall aktivititeter per visit blir mye høyere enn planlagt.
    #activities = np.minimum(activities, 6) 

    df_visits['activities'] = activities

    file_path = os.path.join(os.getcwd(), 'data', 'visits.csv')
    df_visits.to_csv(file_path, index=False)

    return df_visits

def activitiesGenerator(df_visits):
    df_activities = pd.DataFrame(columns=['activityId', 'patientId', 'activityType','numActivitiesInVisit','earliestStartTime', 'latestStartTime', 
                                          'duration', 'synchronisation', 'skillRequirement', 'nextPrece', 'prevPrece', 
                                          'sameEmployeeActivityId', 'visitId', 'treatmentId', 'location'])

    # Generate rows for each activity with the visitId, treatmentId and patientId
    expanded_rows = df_visits.loc[df_visits.index.repeat(df_visits['activities'])].reset_index(drop=False)
    expanded_rows['activityId'] = range(1, len(expanded_rows) + 1)

    df_activities['activityId'] = expanded_rows['activityId']
    df_activities['visitId'] = expanded_rows['visitId']
    df_activities['treatmentId'] = expanded_rows['treatmentId']
    df_activities['patientId'] = expanded_rows['patientId']
    df_activities['numActivitiesInVisit'] = expanded_rows['activities']
    df_activities['location'] = expanded_rows['location']
    df_activities['employeeRestriction'] = expanded_rows['employeeRestriction']
    df_activities['heaviness'] = expanded_rows['heaviness']
           
    # Distribute activities between healthcare activities 'H' and equipment activities 'E'
    # Generate precedence, same employee requirements and change location for pick-up and delivery at the hospital
    # Generate synchronised activities (for visits with 4 or 6 activities)     
    for visitId, group in df_activities.groupby('visitId'):
        if group['numActivitiesInVisit'].iloc[0] < 3:
            # For 1 to 2 activities: 60 % for Healthcare and 40 % for Equipment
            df_activities.loc[group.index, 'activityType'] = np.random.choice(['H', 'E'], size=len(group), p=[0.6, 0.4])
        elif group['numActivitiesInVisit'].iloc[0] >= 3 and group['numActivitiesInVisit'].iloc[0] <= 4:
            # For 3 to 4 activities
            if np.random.rand() < 0.5:
                # 50 % chance: The two first activities in the visit is a pick-up and delivery
                sorted_indices = group.sort_values(by='activityId').index[:2]  # The two activities with the lowest id
                df_activities.loc[sorted_indices, 'activityType'] = 'E'
                remaining_indices = group.index.difference(sorted_indices)
                df_activities.loc[remaining_indices, 'activityType'] = 'H'

                # Precedence and time limit for pick-up and delivery at the start of the visit
                activity_ids = group['activityId'].tolist()
                mu = (construction_config.pd_min + construction_config.pd_max) / 2
                sigma = (construction_config.pd_max - construction_config.pd_min) / 6
                pd_time = int(np.random.normal(mu, sigma))
                df_activities.loc[df_activities['activityId'] == activity_ids[1], 'prevPrece'] = activity_ids[0]
                df_activities.loc[df_activities['activityId'] == activity_ids[2], 'prevPrece'] = f"{activity_ids[1]}, {activity_ids[0]}: {pd_time}"
                df_activities.loc[df_activities['activityId'] == activity_ids[-2], 'nextPrece'] = activity_ids[-1]
                df_activities.loc[df_activities['activityId'] == activity_ids[0], 'nextPrece'] = f"{activity_ids[-2]}, {activity_ids[-1]}: {pd_time}"
                
                # Same Employee Requirement for pick-up and delivery activities
                df_activities.loc[df_activities['activityId'] == activity_ids[0], 'sameEmployeeActivityId'] = activity_ids[1]          # Start of the visit
                df_activities.loc[df_activities['activityId'] == activity_ids[1], 'sameEmployeeActivityId'] = activity_ids[0]          # Start of the visit

                # Overwrite location of the first activity (pick-up at the hospital)
                df_activities.loc[df_activities['activityId'] == activity_ids[0], 'location'] = f'{construction_config.depot}' 

                # Synchronise the two last activities if there are four activities in the visit
                if group['numActivitiesInVisit'].iloc[0] == 4:
                    activity_ids = group['activityId'].tolist()
                    df_activities.loc[df_activities['activityId'] == activity_ids[-1], 'synchronisation'] = activity_ids[-2]
                    df_activities.loc[df_activities['activityId'] == activity_ids[-2], 'synchronisation'] = activity_ids[-1]

            else:
                # 50 % chance: The two last activities in the visit is a pick-up and delivery
                sorted_indices = group.sort_values(by='activityId', ascending=False).index[:2]   # The two activities with the highest id
                df_activities.loc[sorted_indices, 'activityType'] = 'E'
                remaining_indices = group.index.difference(sorted_indices)
                df_activities.loc[remaining_indices, 'activityType'] = 'H'

                # Precedence and time limit for pick-up and delivery at the end of the visit
                activity_ids = group['activityId'].tolist()
                mu = (construction_config.pd_min + construction_config.pd_max) / 2
                sigma = (construction_config.pd_max - construction_config.pd_min) / 6
                pd_time = int(np.random.normal(mu, sigma))
                df_activities.loc[df_activities['activityId'] == activity_ids[1], 'prevPrece'] = activity_ids[0]
                df_activities.loc[df_activities['activityId'] == activity_ids[2], 'prevPrece'] = f"{activity_ids[1]}, {activity_ids[0]}: {pd_time}"
                df_activities.loc[df_activities['activityId'] == activity_ids[-2], 'nextPrece'] = activity_ids[-1]
                df_activities.loc[df_activities['activityId'] == activity_ids[0], 'nextPrece'] = f"{activity_ids[-2]}, {activity_ids[-1]}: {pd_time}"

                # Same Employee Requirement for pick-up and delivery activities
                df_activities.loc[df_activities['activityId'] == activity_ids[-1], 'sameEmployeeActivityId'] = activity_ids[-2]         # End of the visit
                df_activities.loc[df_activities['activityId'] == activity_ids[-2], 'sameEmployeeActivityId'] = activity_ids[-1]         # End of the visit

                # Overwrite location of the last activity (delivery at the hospital)
                df_activities.loc[df_activities['activityId'] == activity_ids[-1], 'location'] = f'{construction_config.depot}' 
                
                # Synchronise the two first activities if there are four activities in the visit
                if group['numActivitiesInVisit'].iloc[0] == 4:
                    activity_ids = group['activityId'].tolist()
                    df_activities.loc[df_activities['activityId'] == activity_ids[0], 'synchronisation'] = activity_ids[1]
                    df_activities.loc[df_activities['activityId'] == activity_ids[1], 'synchronisation'] = activity_ids[0]

        else:
            # For more than 5 activities - 'E' to the two last and two first activities (pick-up and delivery)
            lowest_indices = group.sort_values(by='activityId').index[:2]                       # The two activities with the lowest id
            highest_indices = group.sort_values(by='activityId', ascending=False).index[:2]     # The two activities with the highest id
            df_activities.loc[lowest_indices, 'activityType'] = 'E'
            df_activities.loc[highest_indices, 'activityType'] = 'E'
            remaining_indices = group.index.difference(lowest_indices.union(highest_indices))
            df_activities.loc[remaining_indices, 'activityType'] = 'H'  
            
            # Precedence and time limits for pick-up and delivery
            activity_ids = group['activityId'].tolist()
            mu = (construction_config.pd_min + construction_config.pd_max) / 2
            sigma = (construction_config.pd_max - construction_config.pd_min) / 6
            pd_time1 = int(np.random.normal(mu, sigma))
            pd_time2 = int(np.random.normal(mu, sigma))
            df_activities.loc[df_activities['activityId'] == activity_ids[1], 'prevPrece'] = activity_ids[0]                                           # Pick-up and delivery at the start
            df_activities.loc[df_activities['activityId'] == activity_ids[2], 'prevPrece'] = f"{activity_ids[1]}, {activity_ids[0]}: {pd_time1}"       # Pick-up and delivery at the start
            df_activities.loc[df_activities['activityId'] == activity_ids[-2], 'prevPrece'] = activity_ids[-3]                                         # Pick-up and delivery at the end
            df_activities.loc[df_activities['activityId'] == activity_ids[-1], 'prevPrece'] = f"{activity_ids[-2]}, {activity_ids[-3]}: {pd_time2}"    # Pick-up and delivery at the end
            df_activities.loc[df_activities['activityId'] == activity_ids[1], 'nextPrece'] = activity_ids[2]                                           # Pick-up and delivery at the start
            df_activities.loc[df_activities['activityId'] == activity_ids[0], 'nextPrece'] = f"{activity_ids[1]}, {activity_ids[2]}: {pd_time1}"       # Pick-up and delivery at the start
            df_activities.loc[df_activities['activityId'] == activity_ids[-2], 'nextPrece'] = activity_ids[-1]                                         # Pick-up and delivery at the end
            df_activities.loc[df_activities['activityId'] == activity_ids[-3], 'nextPrece'] = f"{activity_ids[-2]}, {activity_ids[-1]}: {pd_time2}"    # Pick-up and delivery at the end

            # Same Employee Requirement for åick-up and delivery activities 
            df_activities.loc[df_activities['activityId'] == activity_ids[0], 'sameEmployeeActivityId'] = activity_ids[1]      # The two first activities 
            df_activities.loc[df_activities['activityId'] == activity_ids[1], 'sameEmployeeActivityId'] = activity_ids[0]
            df_activities.loc[df_activities['activityId'] == activity_ids[-1], 'sameEmployeeActivityId'] = activity_ids[-2]    # The two last activities
            df_activities.loc[df_activities['activityId'] == activity_ids[-2], 'sameEmployeeActivityId'] = activity_ids[-1]
            
            # Overwrite location of the first and last activity (pick-up and delivery at the hospital)
            df_activities.loc[df_activities['activityId'] == activity_ids[0], 'location'] = f'{construction_config.depot}'     # Pick-up
            df_activities.loc[df_activities['activityId'] == activity_ids[-1], 'location'] = f'{construction_config.depot}'    # Delivery
        
            # Synchronise the two activities in the middle if there are six activities in the visit
            if group['numActivitiesInVisit'].iloc[0] == 6:
                activity_ids = group['activityId'].tolist()
                df_activities.loc[df_activities['activityId'] == activity_ids[2], 'synchronisation'] = activity_ids[3]
                df_activities.loc[df_activities['activityId'] == activity_ids[3], 'synchronisation'] = activity_ids[2]

    # Generate duration of activities
    for activityType, group in df_activities.groupby('activityType'):
        if activityType == 'E':
            # Normal distribution for equipment activities
            mu = (construction_config.minDurationEquip + construction_config.maxDurationEquip) / 2
            sigma = (construction_config.maxDurationEquip - construction_config.minDurationEquip) / 6
            duration = np.random.normal(mu, sigma, len(group))
        else:
            # Normal distribution for healthcare activities
            mu = (construction_config.minDurationHealth + construction_config.maxDurationHealth) / 2
            sigma = (construction_config.maxDurationHealth - construction_config.minDurationHealth) / 6
            duration = np.random.normal(mu, sigma, len(group))
        
        # Integers and clipping to ensure duration within limits from config files
        duration_clipped = np.clip(np.round(duration), construction_config.minDurationEquip, construction_config.maxDurationEquip) if activityType == 'E' else np.clip(np.round(duration), construction_config.minDurationHealth, construction_config.maxDurationHealth)
        df_activities.loc[group.index, 'duration'] = duration_clipped
        
    #Generate earliest and latest start times of activities
    for visitId, group in df_activities.groupby('visitId'):
        # Total duration of all activities for a given visitId
        visit_duration = int(group['duration'].sum())

        #Earliest and latest possible starting times within a day
        startDay = 0
        endDay = 1400
        latestPossible = 1440 - visit_duration
        latestStartTime = np.random.randint(visit_duration, latestPossible)
    
        if np.random.rand() < 0.7:  # 70% sjanse for å velge et tall innenfor 480 og 960 (08:00-16:00)
            latestStartTime = np.random.randint(480, min(1200, latestPossible))
        
        earliestStartTime = np.random.randint(0, latestStartTime-visit_duration)
                  

        df_activities.loc[df_activities['visitId'] == visitId, 'earliestStartTime'] = earliestStartTime #0
        df_activities.loc[df_activities['visitId'] == visitId, 'latestStartTime'] = latestStartTime #1440

       
    # Generate Skill Requirement for activities. Remember to divide between Equipment and Healthcare activities        
    for activityType, group in df_activities.groupby('activityType'):
        if activityType == 'E':
            df_activities.loc[group.index, 'skillRequirement'] = 1
        else:
            # Healthcare activities - 50 % with Skill Requirement 2 and 50 % with Skill Requirement 3
            healthcare_indices = group.index
            shuffled_indices = np.random.permutation(healthcare_indices)
            half_point = len(shuffled_indices) // 2 
            df_activities.loc[shuffled_indices[:half_point], 'skillRequirement'] = 2
            df_activities.loc[shuffled_indices[half_point:], 'skillRequirement'] = 3            

    file_path = os.path.join(os.getcwd(), 'data', 'activities.csv')
    df_activities.to_csv(file_path, index=False)

    return df_activities

def autofillPatient(df_patients, df_treatments):
    #Treatment IDs
    treatments_grouped = df_treatments.groupby('patientId')['treatmentId'].apply(list).reset_index(name='treatmentsIds')

    # Beregner summen av 'visits' for hver 'patientID' i df_treatments
    visits_sum = df_treatments.groupby('patientId')['visits'].sum().reset_index(name='nVisits')

    # Slår sammen behandlings-IDer og totalt antall visits med df_patients
    df_patients_merged = pd.merge(df_patients, treatments_grouped, on='patientId', how='left')
    df_patients_merged = pd.merge(df_patients_merged, visits_sum, on='patientId', how='left')

    #Aggregated Utility - patient utility times the number of visits per patient
    df_patients_merged['aggUtility'] = df_patients_merged['nVisits'] * df_patients_merged['utility']
    
    file_path = os.path.join(os.getcwd(), 'data', 'patients.csv')
    df_patients_merged.to_csv(file_path, index=False)

    return df_patients_merged

def autofillTreatment(df_treatments, df_visits):
    visits_grouped = df_visits.groupby('treatmentId')['visitId'].apply(list).reset_index(name='visitsIds')
    df_treatments_merged = pd.merge(df_treatments, visits_grouped, on='treatmentId', how='left')
    file_path = os.path.join(os.getcwd(), 'data', 'treatments.csv')
    df_treatments_merged.to_csv(file_path, index=False)
    return df_treatments_merged

def autofillVisit(df_visits, df_activities):
    activities_grouped = df_activities.groupby('visitId')['activityId'].apply(list).reset_index(name='activitiesIds')
    df_visits_merged = pd.merge(df_visits, activities_grouped, on='visitId', how='left')
    file_path = os.path.join(os.getcwd(), 'data', 'visits.csv')
    df_visits_merged.to_csv(file_path, index=False)
    return df_visits_merged

def TimeWindowsWithTravel(df_activities, T_ij):
    T_ij_max = round(max([max(row) for row in T_ij]))          # Max travel distance between two activities
    print(f'T_ij_max: {T_ij_max} minutes')
    T_ij_max_depot = round(max(row[0] for row in T_ij))        # Max travel distance from the depot to an activity
    print(f'T_ij_max_depot: {T_ij_max_depot} minutes') 
    
    for visitId, group in df_activities.groupby('visitId'):
        # Total duration of all activities for a given visitId
        visit_duration = int(group['duration'].sum())

        #Earliest and latest possible starting times within a day
        startDay = 0
        endDay = 1400
        latestPossible = 1440 - visit_duration

        #Generated values without travel distances
        earliestStartTime = df_activities.loc[df_activities['visitId'] == visitId, 'earliestStartTime'] 
        latestStartTime = df_activities.loc[df_activities['visitId'] == visitId, 'latestStartTime'] 
        # TODO: Se på hvor mye slingringsmonn det er ønsket på tidsvinduer - Hvor stramme tidsvinduer skal vi tillate
        if group['numActivitiesInVisit'].iloc[0] >= 3 and group['numActivitiesInVisit'].iloc[0] <= 4:
            if (latestStartTime - earliestStartTime < (visit_duration + T_ij_max_depot)*1.5).any():     # Krever noe slingringsmonn 
                print('case for lite tid, 3 aktiviteter', visitId)
                if (earliestStartTime > T_ij_max_depot).any() and (endDay - latestStartTime > T_ij_max_depot).any():
                    df_activities.loc[df_activities['visitId'] == visitId, 'earliestStartTime'] -= round(T_ij_max_depot/2)
                    df_activities.loc[df_activities['visitId'] == visitId, 'latestStartTime'] += round(T_ij_max_depot/2)
                elif (earliestStartTime < T_ij_max_depot).any():
                    df_activities.loc[df_activities['visitId'] == visitId, 'latestStartTime'] += T_ij_max_depot
                elif (endDay - latestStartTime < T_ij_max_depot).any():
                    df_activities.loc[df_activities['visitId'] == visitId, 'earliestStartTime'] -= T_ij_max_depot
        if group['numActivitiesInVisit'].iloc[0] >= 5:
            if (latestStartTime - earliestStartTime < (visit_duration + T_ij_max_depot*2)*1.5).any():   # Krever noe slingringsmonn 
                print('case for lite tid, 5 aktiviteter', visitId)
                if (earliestStartTime > T_ij_max_depot).any() and (endDay - latestStartTime > T_ij_max_depot).any():
                    df_activities.loc[df_activities['visitId'] == visitId, 'earliestStartTime'] -= T_ij_max_depot
                    df_activities.loc[df_activities['visitId'] == visitId, 'latestStartTime'] += T_ij_max_depot
                elif (earliestStartTime < T_ij_max_depot*2).any():
                    df_activities.loc[df_activities['visitId'] == visitId, 'latestStartTime'] += T_ij_max_depot*2
                elif (endDay - latestStartTime < T_ij_max_depot*2).any():
                    df_activities.loc[df_activities['visitId'] == visitId, 'earliestStartTime'] -= T_ij_max_depot*2
        
        file_path = os.path.join(os.getcwd(), 'data', 'activitiesNewTimeWindows.csv')
        (df_activities.reset_index()).to_csv(file_path, index=False)
    return df_activities

#TESTING

'''
df_employees = employeeGeneration.employeeGenerator()
df_patients = patientGenerator(df_employees)
df_treatments = treatmentGenerator(df_patients)
df_visits = visitsGenerator(df_treatments)
df_activities = activitiesGenerator(df_visits)
df_patients_filled = autofillPatient(df_patients, df_treatments)
df_treatments_filled = autofillTreatment(df_treatments, df_visits)
df_visits_filled = autofillVisit(df_visits, df_activities)
'''


