详见 https://www.uscardforum.com/t/topic/451800

## Version History
v0.2.0 Major Update
### Functionalities
0. Include (almost) all civil aviation airports. Data credit to: ourairports.com.
1. Update code logic for better handling of transfer itinerary.

Now in tab2, for each segment, simply define origin and destination airport, carrier and cabin.

### Data
0. Updates all ffp award charts to incorporate the expanded regions support.
1. BA devaluation (Dec 2025): Add a 1.1X multiplier to the (already guessed/imperical) BA chart.
2. IB devaluation (Dec 2025) Noticed IB increased the award miles needed for short haul AA/BA again.
3. Adds Spirit program.
4. AC adds Air baltic as redeem partner. AS adds ITA as earn partner.


## Install

0. A local python 3.x env. No dependencies necessary

1. Clone this repo

2. python gui.py

## Data coverage

FFPs: Transfer partners of major banks in the US. (26) 

Carriers: Someone who is a redeem/earn partner of at least one of the FFP programs. (134)

POIs: (Almost) All civil aviation airports. 

Data last update on: 01/17/2026



## Usage

### Tab1

Purpose: Find which FFP(s) can (in theory) be used to redeem award ticket on a specific carrier.

### Tab2

Purpose: Find the miles needed for a desired itinerary. Currently, it is not designed to find the 'cheapest route' between your departure and destination. It is designed to find all the redeem options for your desired route. If for some reason (most likely due to availability) that issue your trip on one ticket is not applicable, the program also searches for options with subsegments. A few examples below



![Direct flight](/assets/readme/example1.png)
*Example 1: Domestic short haul.*

![Direct flight](/assets/readme/example2.png)
*Example 2: International long haul.*

![Transfer1](/assets/readme/example3.png)
*Example 3: Transfer (involving 1 carrier).*

![Transfer2](/assets/readme/example3.png)
*Example 3: Transfer involving multiple carriers.*

### Tab3

Purpose: Compare if it is worth it to use award ticket. Tax and fees for the award ticket and cash price for the same itinerary needs manual input. Mile evaluation can be changed by personal preference.



### Tab4

Purpose: Find which FFP can be used to collect miles when taking cash price tickets from a certain carrier. As a frequent flyer, I would assume you have a preferred program for each alliance. By displaying family pooling and expiration policy, the main purpose for this is to help you decide for your less frequent flying family members, which program is convenient for them and you to use the collected miles.





