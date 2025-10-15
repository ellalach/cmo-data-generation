#defines a library of scenario generators for CMO: PE, where each class creates differnet arrangements of a target, jet, and one or more SAM sites
#each generator can produce randomized scenarios, export them as Lua scripts for CMO, log metadata in CSV files, and organize them into train/test/validate splits

import numpy as np
import random
import csv
from pathlib import Path
import os
import shutil

class DefaultGen():
    """
    Generates Scenario 0 type maps for Command Modern Operations: PE. Scenario 0 includes only 1 target, 1 jet and 1 SAM site.
    This class defines a relationship between the SAM sites, the jet and target such that the jet and target spawn based on the location of the SAM site.
    The jet remains to the south of the SAM site, while the target remains to the north.
    Attributes:
        target_lat (float): Latitude of the target.
        target_long (float): Longitude of the target.
        target_dbid (int): Database ID of the target.
        jet_lat (float): Latitude of the jet.
        jet_long (float): Longitude of the jet.
        jet_dbid (int): Database ID of the jet.
        sam_lat (float): Latitude of the SAM site.
        sam_long (float): Longitude of the SAM site.
        sam_dbid (int): Database ID of the SAM site.
        csv_file_initiailized (Boolean): Flag for tracking metadata file.
        type_of_scenario (String): Scenario type.
        self.split (String): Allocation, Train, Test or Validate
    """

    def __init__(self, sam_dbid, jet_dbid, target_dbid, num_scens, zones: list, csv_file_initialized=False, split=None, seed: int=0):
        """
        Initializes attributes for Scenario Generator 0
        """

        # a boolean flag to help us see if we need to overwrite our csv file
        self.csv_file_initialized = False
        self.type_of_scenario = "Scenario_0"
        self.seed = seed
        self.split= None
        self.zones = zones
        self.sam_dbid=sam_dbid
        self.jet_dbid=jet_dbid
        self.target_dbid=target_dbid
        self.num_scens=num_scens


    def gen_sam(self):
        """
        Generates the location of SAM for generator 0
        The SAM is generated within the zone with a uniform probability within defined latitude and longitude coordinates.
        """

        self.zone_name, self.sam_zone=random.choice(list(self.zones.items()))

        self.sam_lat=np.random.uniform(self.sam_zone[0],self.sam_zone[1])
        self.sam_long=np.random.uniform(self.sam_zone[2],self.sam_zone[3])


    def gen_jet(self):
        """
        Generates location of fighter jet based on the SAM site for generator 0
        The jet is generated within 5 degrees of the SAM site, the jet remains south of the target
        """

        self.jet_lat=self.sam_lat+np.random.uniform(-5,-2.5) #keep the target south of the sam
        self.jet_long=self.sam_long+np.random.uniform(-5,5)


    def gen_target(self):
        """
        Generates location of target based on the SAM site for generator 0
        The target is generated within 5 degrees of the SAM site, the target remains north of the target
        """

        self.target_lat=self.sam_lat+np.random.uniform(2.5,5) #keep the target north of the sam
        self.target_long=self.sam_long+np.random.uniform(-5,5)


    def gen_lua_script(self):
        """
        Create a lua script that is readable by CMO and can be used for all generator types
        """

        # moved the scenario_data to be in their own folders where the python scripts are
        # if the directory doesnt exist, make it
        # removing hard-paths is important if we run the code on different computers
        # Would be interesting here if we did some probability, and based on that probability we assigned the scenario to eeither 1) train, 2) test or 3) validate
        # No clue if this is the right approach, due to the nature of randomness, there could be the same scenario within the test/validation/train sets
        choices = ['train', 'test', 'validate']
         # 60% train, 20% test, 20% validate
         
        weights = [0.6, 0.2, 0.2]
        self.split = random.choices(choices, weights=weights, k=1)[0]

        file_name=Path(f"scenario_data\\{self.split}\\{self.type_of_scenario}\\{self.type_of_scenario}_{self.seed}.lua")
               
        directory = os.path.dirname(file_name)
        if not os.path.exists(directory):
            os.makedirs(directory)

        if self.type_of_scenario == "Scenario_0":
            self.sam_lat_list = [self.sam_lat]  
            self.sam_long_list = [self.sam_long]  
        else:
            self.sam_lat_list = self.sam_lats
            self.sam_long_list = self.sam_longs

        with open(file_name, "w") as lua_file:
            lua_file.write(f"""
Tool_BuildBlankScenario()
ScenEdit_SetTime({{Date= "1.1.2030", Time= "00.00.00", StartDate = "1.1.2030", StartTime = "00.00.00", Duration = "0:02:00"}})
local endTime = os.date('%d/%m/%Y %H:%M:%S', ScenEdit_CurrentTime() + ((2*60)-1)*60)
print(endTime)
local file_path = "C:/Users/Brayden/Desktop/pycmo_recent/afrl_pycmo/pycmo/configs/scen_has_ended.txt"
-- function here is meant to write false when the scenario starts, but for some reason it never hits this, so we worked
-- with the semaphore idea instead, and write False to scen_has_ended through reset() in cmo_env.py
-- no current trigger exists to use this function
function mark_scenario_started()  
    local file = io.open(file_path, "w")
    if file then
        file:write("False")
        file:close()
    else
        error("Failed to open file: " .. file_path)
    end
end
mark_scenario_started()

ScenEdit_AddSide({{side = "attacker_side"}})
ScenEdit_AddSide({{side = "target_side"}})
ScenEdit_SetSideOptions({{side = "attacker_side", awareness = 3}})
ScenEdit_SetSidePosture("attacker_side", "target_side", "H")
ScenEdit_SetSidePosture("target_side", "attacker_side", "H")
ScenEdit_AddUnit({{type ='Aircraft', unitname ="shooter", dbid ={self.jet_dbid}, side = "attacker_side", Latitude ={self.jet_lat}, Longitude ={self.jet_long}, Altitude = "4000 ft", LoadoutID = 33070}})
ScenEdit_AddUnit({{type ='Facility', unitname ="target_ammo", dbid ={self.target_dbid}, side = "target_side", Latitude ={self.target_lat}, Longitude ={self.target_long} }})""")

        for i in range(len(self.sam_long_list)):
            with open(file_name,"a") as lua_file:
                lua_file.write(f"""
ScenEdit_AddUnit({{type ='Facility', unitname ='sam', dbid ={self.sam_dbid}, side = 'target_side', Latitude = {self.sam_lat_list[i]}, Longitude = {self.sam_long_list[i]} }})""")

        with open(file_name, "a") as lua_file:
            lua_file.write(f"""
ScenEdit_SetTrigger({{
    name = 'Trigger_Target_Ammo_Destroyed_Points',
    mode = 'add',
    type = 'UnitDestroyed',
    targetfilter = {{
        SpecificUnitID = 'target_ammo',
        TargetSide = 'target_side'
    }}
}})
ScenEdit_SetTrigger({{
    name = 'Trigger_Target_Ammo_Destroyed_End',
    mode = 'add',
    type = 'UnitDestroyed',
    targetfilter = {{
        SpecificUnitID = 'target_ammo',
        TargetSide = 'target_side'
    }}
}})

ScenEdit_SetTrigger({{
    name = "End_Scenario_Timelimit",
    mode = 'add',
    type = 'Time',
    Time = endTime
}})

ScenEdit_SetEvent('Scenario_Reached_Timelimit', {{mode = 'add'}})
ScenEdit_SetEvent('Target_Ammo_Destroyed_GivePoints', {{mode = 'add'}})
ScenEdit_SetEvent('Target_Ammo_Destroyed_EndScenario', {{mode = 'add'}})

ScenEdit_SetEventTrigger('Scenario_Reached_Timelimit', {{
    mode = 'add',
    description = 'End_Scenario_Timelimit'
}})

ScenEdit_SetEventTrigger('Target_Ammo_Destroyed_GivePoints', {{
    mode = 'add',
    description = 'Trigger_Target_Ammo_Destroyed_Points'
}})
ScenEdit_SetEventTrigger('Target_Ammo_Destroyed_EndScenario', {{
    mode = 'add',
    description = 'Trigger_Target_Ammo_Destroyed_End'
}})

ScenEdit_SetAction({{
    mode = 'add',
    description = 'give_points',
    type = 'Points',
    SideID = 'attacker_side',
    PointChange = 1
}})

ScenEdit_SetAction({{
    mode = 'add',
    description = 'end_with_script',
    type = 'LuaScript',
    ScriptText = 'ScenEdit_EndScenario()'
}})

ScenEdit_SetEventAction('Scenario_Reached_Timelimit', {{
    mode = 'add',
    description = 'end_with_script'
}})
-- Give points and end the scenario (if we destroy the target)
ScenEdit_SetEventAction('Target_Ammo_Destroyed_GivePoints', {{
    mode = 'add',
    description = 'give_points'
}})

ScenEdit_SetEventAction('Target_Ammo_Destroyed_EndScenario', {{
    mode = 'add',
    description = 'end_with_script'
}})

Command_SaveScen("C:/Users/Brayden/Desktop/pycmo_recent/afrl_pycmo/scen/example_0.save")
-- this function works and runs everytime because of the trigger on line 55
function mark_scenario_ended()
    local file = io.open(file_path, "w")
    if file then
        file:write("True")
        file:close()
    else
        error("Failed to open file: " .. file_path)
    end
end

ScenEdit_SetTrigger({{name = 'Game_Ended_trigger', mode = 'add', type="ScenEnded"}})
ScenEdit_SetEvent('Game_ended_event',{{mode = 'add'}})
ScenEdit_SetEventTrigger('Game_ended_event',{{mode = 'add', description = 'Game_Ended_trigger'}})
ScenEdit_SetAction({{mode='add', name="end_game_act", type="LuaScript", ScriptText = "mark_scenario_ended()"}})
ScenEdit_SetEventAction('Game_ended_event', {{mode = 'add', description = 'end_game_act'}})""")


    def gen_csv_file(self):
        """
        Generate a csv file for any generator type that contains the latitutde and longitude of the sam, jet, and target along with other data such as dbids, seed, split, zone, scenario type
        """

        # scenario 0 is the only one with an int instead of a list for the sam locations
        # check if we are within scenario_0 and if we are cast the ints to a list so we can use the same zip method


        # test to see if this will work when we have more than 1 sam_site (seems to work now, our seperate is a ;)
        #for i in range(10):
           # sam_lat_list.append(self.sam_lat)
           # sam_long_list.append(self.sam_long)

        sam_coords = list(zip(self.sam_lat_list, self.sam_long_list))
        sam_coords_str = ", ".join([f"({lat}, {long})" for lat, long in sam_coords])

        # placing the meta data within its own directory & check if we need to create the directory (saves new users a headache from file not found errors)
        csv_file=Path(f"scenario_data\\metadata\\{self.type_of_scenario}.csv")
       
        directory = os.path.dirname(csv_file)
        if not os.path.exists(directory):
            os.makedirs(directory)

        headers = ["scen_type", "seed", "split", "zone", "target_location", "target_dbid", "jet_location", "jet_dbid", "sam_locations", "sam_dbid"]

        row = [self.type_of_scenario, self.seed, self.split, self.zone_name, f"({self.target_lat}, {self.target_long})", f"{self.target_dbid}", f"({self.jet_lat}, {self.jet_long})", f"{self.jet_dbid}",  sam_coords_str, f"{self.sam_dbid}"]
        if not self.csv_file_initialized:
            with open(csv_file, "w", newline="") as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(headers)
            self.csv_file_initialized = True

        with open(csv_file, "a", newline="") as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(row)


    def clear_files_in_directories(self):
        """
        Cleans all scenarios previously generated within the scenario_data folder
        """

        dirs_to_clean = [
            'scenario_data\\train',
            'scenario_data\\test',
            'scenario_data\\validate'
        ]

        for parent_dir in dirs_to_clean:
            if not os.path.isdir(parent_dir):
                continue

            for item in os.listdir(parent_dir):
                item_path = os.path.join(parent_dir, item)
                if os.path.isdir(item_path):
                    try:
                        shutil.rmtree(item_path)
                    except Exception as e:
                        print(f"Error removing '{item_path}': {e}")
            print(f"Cleaned subdirectories in: {parent_dir}")


    def generate_scenario(self):
        """
        Generate a given scenario using the functions of the given generator class
        """

        print(f"Generating {self.num_scens} scenarios!")
        for i in range(self.num_scens): #determine how many scenarios are produced by changing range
            np.random.seed(i)
            self.seed=i
           
            if self.type_of_scenario=="Scenario_3":

                #generate target
                self.gen_target()
               
                #generate sam
                self.gen_sam()

                #generate jet
                self.gen_jet()

                #generate the lua script
                self.gen_lua_script()
               
                #generate csv file
                self.gen_csv_file()

            else:

                #generate sam
                self.gen_sam()

                #generate jet
                self.gen_jet()

                #generate target
                self.gen_target()

                #generate the lua script
                self.gen_lua_script()
               
                #generate csv file
                self.gen_csv_file()

        print("Completed Generating Scenarios!")


class LineGen(DefaultGen):

    """
    Generates Scenario 1 type maps for Command Modern Operations: PE. Scenario 1 includes only 1 target, 1 jet and a mutable number of SAM site. This creates a solid line of SAMs.
    This class defines a relationship between the SAM sites, the jet and the target such that the jet and target spawn based on the location and direction of the SAM sites.
    The jet remains to the left of the line of SAMs while the target remains to the right, whether they are above or below depends on the SAM sites.
    Attributes:
        target_lat (float): Latitude of the target.
        target_long (float): Longitude of the target.
        target_dbid (int): Database ID of the target.
        jet_lat (float): Latitude of the jet.
        jet_long (float): Longitude of the jet.
        jet_dbid (int): Database ID of the jet.
        sam_lat (float): Latitude of the SAM site.
        sam_long (float): Longitude of the SAM site.
        sam_dbid (int): Database ID of the SAM site.
        csv_file_initiailized (Boolean): Flag for tracking metadata file.
        type_of_scenario (String): Scenario type.
        self.split (String): Allocation, Train, Test or Validate
    """
    def __init__(self, num_sams, sam_dbid, jet_dbid, target_dbid, num_scens, zones: list, csv_file_initialized=False, split=None, seed: int=0):
        """
        Initialize attributes for Scenario Generator 1
        """
        super().__init__(sam_dbid, jet_dbid, target_dbid, num_scens, zones, csv_file_initialized, split, seed)
        self.num_sams=num_sams
        self.type_of_scenario = "Scenario_1"


    def gen_sam(self):
        """
        Generates the location of the line of SAMs for generator 1
        The initial SAM is generated within the zone with a uniform probability within defined latitude and longitude coordinates
        The adjacent sams are generated based on the position of the last, the direction is controlled by a randomly generated angle
        """
        self.sam_lats=[]
        self.sam_longs=[]

        #initial sam
        self.zone_name, self.sam_zone=random.choice(list(self.zones.items()))

        self.sam0_lat=np.random.uniform(self.sam_zone[0],self.sam_zone[1])
        self.sam0_long=np.random.uniform(self.sam_zone[2],self.sam_zone[3])

        self.sam_lats.append(self.sam0_lat)
        self.sam_longs.append(self.sam0_long)

        #second sam (controls direction of the line of sams)
        self.sam1_angle_degrees=np.random.randint(0,360)
        sam1_angle=np.radians(self.sam1_angle_degrees)
        sam1_lat_dis=(2*np.sin(sam1_angle))
        sam1_lat=self.sam0_lat+sam1_lat_dis
        self.sam_lats.append(sam1_lat)
        sam1_long_dis=(2*np.cos(sam1_angle))
        sam1_long=self.sam0_long+sam1_long_dis
        self.sam_longs.append(sam1_long)

        #generate the adjacent sams
        for i in range(self.num_sams-2):
            sam2_angle=np.random.randint(10,60)
            sam2_angle=np.radians(sam2_angle)
            sam2_lat_dis=(2*np.sin(sam2_angle))
            if sam1_lat_dis>0:
                sam2_lat=self.sam_lats[-1]+sam2_lat_dis
                self.sam_lats.append(sam2_lat)
            else:
                sam2_lat=self.sam_lats[-1]-sam2_lat_dis
                self.sam_lats.append(sam2_lat)

            sam2_long_dis=(2*np.cos(sam2_angle))
            if sam1_long_dis>0:
                sam2_long=self.sam_longs[-1]+sam2_long_dis
                self.sam_longs.append(sam2_long)
            else:
                sam2_long=self.sam_longs[-1]-sam2_long_dis
                self.sam_longs.append(sam2_long)

        #sorts lat and long into a new list to use for jet and target locations
        self.sorted_sam_latitudes=sorted(self.sam_lats)
        self.sorted_sam_longitudes=sorted(self.sam_longs)
       
        self.sam_cords=zip(self.sam_lats, self.sam_longs)


    def gen_target(self):
        """
        Generates the location of the target for generator 1
        The target accounts for the direction of the line of SAMs and will always spawn to the right of the line.
        """
        #the sams will generate in a certain direction based on the second sam's angle, if we think of it like quadrants we can create spawn areas for the target
        if self.sam1_angle_degrees in range(0,90) or range(180,270): #quad 1 and 3
            self.target_long=np.random.uniform(self.sorted_sam_longitudes[-2]+2.5, self.sorted_sam_longitudes[-1]+2.5)
            self.target_lat=np.random.uniform(self.sorted_sam_latitudes[0]-2.5,self.sorted_sam_latitudes[-1]-2.5)

        elif self.sam1_angle_degrees in range(90,180) or range(270,360): #quad 2 and 4
            self.target_long=np.random.uniform(self.sorted_sam_longitudes[-2]+2.5, self.sorted_sam_longitudes[-1]+2.5)
            self.target_lat=np.random.uniform(self.sorted_sam_latitudes[0]+2.5,self.sorted_sam_latitudes[-1]+2.5)


    def gen_jet(self):
        """
        Generates the location of the fighter jet for generator 1
        The jet accounts for the direction of the line of SAMs and will always spawn to the left of the line.
        """
        #the sams will generate in a certain direction based on the second sam's angle, if we think of it like quadrants we can create spawn areas for the jet
        if self.sam1_angle_degrees in range(0,90) or range(270,360): #quad 1 and 3
            self.jet_long=np.random.uniform(self.sorted_sam_longitudes[0]-4, self.sorted_sam_longitudes[0]-2.5)
            self.jet_lat=np.random.uniform(self.sorted_sam_latitudes[-1]+2.5,self.sorted_sam_latitudes[0]-2.5)

        elif self.sam1_angle_degrees in range(90,180) or range(270,360): #quad 2 and 4
            self.jet_long=np.random.uniform(self.sorted_sam_longitudes[0]-4,self.sorted_sam_longitudes[0]-2.5)
            self.jet_lat=np.random.uniform(self.sorted_sam_latitudes[0]-2.5, self.sorted_sam_latitudes[-1]+2.5)


class GapLineGen(DefaultGen):
    """
    Generates Scenario 2 type maps for Command Modern Operations: PE. Scenario 2 includes only 1 target, 1 jet and a mutable number of SAM site. There is a gap (missing SAM) in the line of SAMs.
    This class defines a relationship between the SAM sites, the jet and the target such that the jet and target spawn based on the location and direction of the SAM sites.
    The jet remains to the left of the line of SAMs while the target remains to the right, whether they are above or below depends on the SAM sites.
    Attributes:
        target_lat (float): Latitude of the target.
        target_long (float): Longitude of the target.
        target_dbid (int): Database ID of the target.
        jet_lat (float): Latitude of the jet.
        jet_long (float): Longitude of the jet.
        jet_dbid (int): Database ID of the jet.
        sam_lat (float): Latitude of the SAM site.
        sam_long (float): Longitude of the SAM site.
        sam_dbid (int): Database ID of the SAM site.
        csv_file_initiailized (Boolean): Flag for tracking metadata file.
        type_of_scenario (String): Scenario type.
        self.split (String): Allocation, Train, Test or Validate
    """
    def __init__(self, num_sams, sam_dbid, jet_dbid, target_dbid, num_scens, zones: list, csv_file_initialized=False, split=None, seed: int=0):
        """
        Initialize attributes for Scenario Generator 2
        """
        super().__init__(sam_dbid, jet_dbid, target_dbid, num_scens, zones, csv_file_initialized, split, seed)

        self.num_sams=num_sams
        self.type_of_scenario = "Scenario_2"


    def gen_sam(self):
        """
        Generates the location of the line of SAMs for generator 1
        The initial SAM is generated within the zone with a uniform probability within defined latitude and longitude coordinates
        The adjacent sams are generated based on the position of the last, the direction is controlled by a randomly generated angle
        A random SAM is then chosen, and removed from the line in order to create a gap.
        """
 
        self.sam_lats=[]
        self.sam_longs=[]

        #initial sam
        self.zone_name, self.sam_zone=random.choice(list(self.zones.items()))

        self.sam0_lat=np.random.uniform(self.sam_zone[0],self.sam_zone[1])
        self.sam0_long=np.random.uniform(self.sam_zone[2],self.sam_zone[3])

        self.sam_lats.append(self.sam0_lat)
        self.sam_longs.append(self.sam0_long)

        #second sam (controls direction of the line of sams)
        self.sam1_angle_degrees=np.random.randint(0,360)
        sam1_angle=np.radians(self.sam1_angle_degrees)
        sam1_lat_dis=(1.5*np.sin(sam1_angle))
        sam1_lat=self.sam0_lat+sam1_lat_dis
        self.sam_lats.append(sam1_lat)
        sam1_long_dis=(1.5*np.cos(sam1_angle))
        sam1_long=self.sam0_long+sam1_long_dis
        self.sam_longs.append(sam1_long)

        #generate the adjacent sams
        for i in range(self.num_sams-2):
            sam2_angle=np.random.randint(10,60)
            sam2_angle=np.radians(sam2_angle)
            sam2_lat_dis=(2*np.sin(sam2_angle))
            if sam1_lat_dis>0:
                sam2_lat=self.sam_lats[-1]+sam2_lat_dis
                self.sam_lats.append(sam2_lat)
            else:
                sam2_lat=self.sam_lats[-1]-sam2_lat_dis
                self.sam_lats.append(sam2_lat)

            sam2_long_dis=(2*np.cos(sam2_angle))
            if sam1_long_dis>0:
                sam2_long=self.sam_longs[-1]+sam2_long_dis
                self.sam_longs.append(sam2_long)
            else:
                sam2_long=self.sam_longs[-1]-sam2_long_dis
                self.sam_longs.append(sam2_long)

        #pop a random sam (thats not on the end) in order to create a gap
        removed_sam=np.random.randint(1, self.num_sams-1)

        self.sam_lats.pop(removed_sam)
        self.sam_longs.pop(removed_sam)

        #sorts lat and long into a new list to use for jet and target locations
        self.sorted_sam_latitudes=sorted(self.sam_lats)
        self.sorted_sam_longitudes=sorted(self.sam_longs)
       
        self.sam_cords=zip(self.sam_lats, self.sam_longs)


    def gen_target(self):
        """
        Generates the location of the target for generator 1
        The target accounts for the direction of the line of SAMs and will always spawn to the right of the line.
        """
        #the sams will generate in a certain direction based on the second sam's angle, if we think of it like quadrants we can create spawn areas for the target
        if self.sam1_angle_degrees in range(0,90) or range(180,270): #quad 1 and 3
            self.target_long=np.random.uniform(self.sorted_sam_longitudes[-2]+2.5, self.sorted_sam_longitudes[-1]+2.5)
            self.target_lat=np.random.uniform(self.sorted_sam_latitudes[0]-2.5,self.sorted_sam_latitudes[-1]-2.5)

        elif self.sam1_angle_degrees in range(90,180) or range(270,360): #quad 2 and 4
            self.target_long=np.random.uniform(self.sorted_sam_longitudes[-2]+2.5, self.sorted_sam_longitudes[-1]+2.5)
            self.target_lat=np.random.uniform(self.sorted_sam_latitudes[0]+2.5,self.sorted_sam_latitudes[-1]+2.5)


    def gen_jet(self):
        """
        Generates the location of the fighter jet for generator 1
        The jet accounts for the direction of the line of SAMs and will always spawn to the left of the line. the location of the jet for generator 2
        """
        #the sams will generate in a certain direction based on the second sam's angle, if we think of it like quadrants we can create spawn areas for the jet
        if self.sam1_angle_degrees in range(0,90) or range(270,360): #quad 1 and 3
            self.jet_long=np.random.uniform(self.sorted_sam_longitudes[0]-4, self.sorted_sam_longitudes[0]-2.5)
            self.jet_lat=np.random.uniform(self.sorted_sam_latitudes[-1]+2.5,self.sorted_sam_latitudes[0]-2.5)

        elif self.sam1_angle_degrees in range(90,180) or range(270,360): #quad 2 and 4
            self.jet_long=np.random.uniform(self.sorted_sam_longitudes[0]-4,self.sorted_sam_longitudes[0]-2.5)
            self.jet_lat=np.random.uniform(self.sorted_sam_latitudes[0]-2.5, self.sorted_sam_latitudes[-1]+2.5)


class CircleGen(DefaultGen):
    """
    Generates Scenario 3 type maps for Command Modern Operations: PE. Scenario 3 includes only 1 target, 1 jet and a mutable number of SAM sites. This Scenario creates a circle of SAMs around the target.
    This class defines a relationship between the target, the SAM sites, and the jet, such that the SAMs spawn in a circle around the target and the jet spawns outside of the circle of SAMs.
    Attributes:
        target_lat (float): Latitude of the target.
        target_long (float): Longitude of the target.
        target_dbid (int): Database ID of the target.
        jet_lat (float): Latitude of the jet.
        jet_long (float): Longitude of the jet.
        jet_dbid (int): Database ID of the jet.
        sam_lat (float): Latitude of the SAM site.
        sam_long (float): Longitude of the SAM site.
        sam_dbid (int): Database ID of the SAM site.
        csv_file_initiailized (Boolean): Flag for tracking metadata file.
        type_of_scenario (String): Scenario type.
        self.split (String): Allocation, Train, Test or Validate
    """
    def __init__(self, num_sams, desired_radius, sam_dbid, jet_dbid, target_dbid, num_scens, zones, csv_file_initialized=False, split=None, seed=0 ):
        """
        Initialize attributes for Scenrio Genrator 3
        """
        super().__init__(sam_dbid, jet_dbid, target_dbid, num_scens, zones, csv_file_initialized, split, seed)
       
        self.type_of_scenario = "Scenario_3"
        self.num_sams=num_sams
        self.radius=desired_radius


    def gen_target(self):
        """
        Generate the target for generator 3
        The target is generated within the zone with a uniform probability within defined latitude and longitude coordinates.
        """
        self.zone_name, self.sam_zone=random.choice(list(self.zones.items()))

        self.target_lat=np.random.uniform(self.sam_zone[0],self.sam_zone[1])
        self.target_long=np.random.uniform(self.sam_zone[2],self.sam_zone[3])


    def gen_sam(self):
        """
        Generate the circle of SAMs surrounding the target for generator 3
        The SAMs generate around the target based on the given radius and amount of SAMs desired.
        """
        theta=np.linspace(0,2*np.pi, self.num_sams, endpoint=False)

        sam_longs=self.target_long+self.radius*np.cos(theta) #longitudes of SAMs generated
        sam_lats=self.target_lat+self.radius*np.sin(theta) #latitudes of SAMs generated

        removed_sam=np.random.randint(0,self.num_sams-1) #randomly removed SAM in order to create an opening
        self.sam_lats=np.delete(sam_lats, removed_sam)
        self.sam_longs=np.delete(sam_longs, removed_sam)

        self.sam_lats=[float(x) for x in self.sam_lats]
        self.sam_longs=[float(x) for x  in self.sam_longs]
       
        self.sam_coordinates=zip(self.sam_lats, self.sam_longs)


    def gen_jet(self):
        """
        Generates the location of the jet outside of the circle of SAMs
        The jet uses the radius of the circle of SAMs and a randomly generated angle to determine where to generate.
        """
        jet_angle=np.random.randint(0,360)
        jet_radius=np.random.uniform(self.radius+3,self.radius+4)
        jet_lat_dis=jet_radius*np.sin(jet_angle)
        self.jet_lat=self.target_lat+jet_lat_dis
        jet_long_dis=jet_radius*np.cos(jet_angle)
        self.jet_long=self.target_long+jet_long_dis
