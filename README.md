This code defines a library of scenario generators for the game Command Modern Operations: PE
Each class creates different spatial arrangements of a target, a jet, and one or more SAM sites (single SAM, line of SAMs, line with a gap, or circle)
Each generator can produce randomized scenarios, export them as Lua scripts for the game, log metadata in CSV files, and organize them into train/test/validate splits.
The data logged inteh CSV file is able to be plotted to ensure that each scenario is spawning correctly on the globe
