#!/usr/bin/env python3
import json
import urllib.request

# Constants
AREA_AUS = 7.687e12
NUM_REGIONS = 40

# Get the FSDF ids
#url = "http://envirohack.research.nicta.com.au/fsdf-topology/units/?unitType=STAT&statType=SA3"
#result = urllib.request.urlopen(url)
url = "ids.json"
result = open(url) 

ids = json.loads(result.read())
#print("Loaded FSDF ids")

# Get the area and name data
#url = "http://envirohack.research.nicta.com.au/admin_bnds_abs/ows?service=WFS&request=GetFeature&bbox=-43.74050960205765,96.816941408,-9.142175976703609,159.109219008&typeName=admin_bnds:SA3_2011_AUST&outputFormat=json&version=2.0.0&propertyName=SA3_CODE11,SA3_NAME11,STE_CODE11,STE_NAME11,ALBERS_SQM"
#result = urllib.request.urlopen(url)
url = "attributes.json"
result = open(url)

attributes = json.loads(result.read())['features']
#print("Loaded ABS attributes")

# Form a list of boundaries containing all boundary information, ie: name, area, neighbours
boundaries = []
for id in ids:
	for attrs in attributes:
		if attrs['properties']['SA3_CODE11'] == id['absId']:
			boundary = {
				'id': id['id'],
				'absId': id['absId'],
				'area': attrs['properties']['ALBERS_SQM'],
				'name': attrs['properties']['SA3_NAME11'],
				'code': attrs['properties']['SA3_CODE11'],
				'state': attrs['properties']['STE_CODE11'],
			}
			boundaries.append(boundary)
#print("Created boundary objects")


# Sort boundaries from smallest to largest
boundaries.sort(key=lambda b: b['area'])



# Create the set of regions
regions = []

# Turn all of the boundaries into regions
while boundaries:
	# Using smallest boundary area in sorted list
	boundary = boundaries.pop()

	# Create a set containing  boundary
	region = {
		'boundaries': [boundary],
		'area': boundary['area'],
		'name': boundary['name'],
		'state': boundary['state'],
	}
	regions.append(region)

	# Get this boundary's neighbours
	url = "http://envirohack.research.nicta.com.au/fsdf-topology/units/"+str(boundary['id'])+"/adjacent/"
	request = urllib.request.urlopen(url)
	boundary['neighbours'] = json.loads(request.read().decode('utf-8'))


	min_area = AREA_AUS/(NUM_REGIONS/2)
	max_area = AREA_AUS/(NUM_REGIONS*2)
	# While the area of the set is less that aprroixmatly the area of australia/40:


	while region['area'] < (AREA_AUS/NUM_REGIONS) and (region['area'] < min_area):
		# Select an adjacent boundary within same state with the smallest area
		smallest_boundary, index = None, None

		for neighbour in boundary['neighbours']:
			# Check we haven't add this boundary to another region
			neighbour_is_regionless = False
			for b, bound in enumerate(boundaries):
				if neighbour['id'] == bound['id']:
					neighbour_is_regionless, index = True, b
					neighbour = bound

			# If not in another region, check if it is the smallest
			if neighbour_is_regionless:
				if not smallest_boundary or neighbour['area'] < smallest_boundary['area']:
					smallest_boundary = neighbour

		# If total area of set + new boundary is < approximately australia_area/40:
		if smallest_boundary:
			# Add the new boundary to the set
			region['boundaries'].append(smallest_boundary)
			region['area'] += smallest_boundary['area']
			# Remove from the set of boundaries
			boundaries.pop(index)
		else:
			break

# Format regions sensibly
final_regions = {}

for id, region in enumerate(regions):
	final_regions[id] = {
		'name': region['name'],
		'absIds': [boundary['absId'] for boundary in region['boundaries']],
		#'neighbours': list(set(sum([], [neighbour['id'] for neighbour in boundary['neighbours']] for boundary in region['boundaries']))
		'state': region['state'],
	}

#print("Created regions")

print(json.dumps(final_regions))