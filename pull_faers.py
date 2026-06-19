"""
FAERS Data Pull — OpenFDA API
Loopwork System, LLC

Pulls adverse event reports from the FDA Adverse Event Reporting System
for a specified drug. Saves raw JSON for analysis.

Usage:
    python3 pull_faers.py --drug "ozempic" --limit 100
    python3 pull_faers.py --drug "keytruda" --serious --limit 50
"""

import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime

def pull_faers(drug_name, limit=100, serious_only=False):
    """Pull adverse event reports from OpenFDA for a given drug."""
    
    # Build the search query
    search = f'patient.drug.openfda.brand_name:"{drug_name}"'
    if serious_only:
        search += '+AND+serious:1'
    
    url = f'https://api.fda.gov/drug/event.json?search={urllib.parse.quote(search, safe="+:")}&limit={limit}'
    
    print(f"Pulling FAERS data for: {drug_name}")
    print(f"Serious only: {serious_only}")
    print(f"Limit: {limit}")
    print(f"URL: {url}")
    print()
    
    # Make the request
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
    
    total = data['meta']['results']['total']
    retrieved = len(data['results'])
    print(f"Total reports available: {total:,}")
    print(f"Retrieved: {retrieved}")
    print()
    
    # Save raw JSON
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{output_dir}/{drug_name.lower().replace(' ', '_')}_{timestamp}_raw.json"
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Raw data saved to: {filename}")
    
    # Save a readable summary
    summary_file = f"{output_dir}/{drug_name.lower().replace(' ', '_')}_{timestamp}_summary.txt"
    with open(summary_file, 'w') as f:
        f.write(f"FAERS Data Pull Summary\n")
        f.write(f"Drug: {drug_name}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"Total reports available: {total:,}\n")
        f.write(f"Retrieved: {retrieved}\n")
        f.write(f"Serious only: {serious_only}\n")
        f.write(f"Source: OpenFDA API (last updated {data['meta']['last_updated']})\n")
        f.write(f"\n{'='*60}\n\n")
        
        for i, report in enumerate(data['results']):
            patient = report.get('patient', {})
            age = patient.get('patientonsetage', 'unknown')
            sex = {'1': 'Male', '2': 'Female'}.get(patient.get('patientsex', ''), 'Unknown')
            country = report.get('occurcountry', 'Unknown')
            date = report.get('receivedate', 'unknown')
            
            reactions = [r['reactionmeddrapt'] for r in patient.get('reaction', [])]
            drugs = list(set([d.get('medicinalproduct', 'unknown') for d in patient.get('drug', [])]))
            
            hosp = report.get('seriousnesshospitalization') == '1'
            death = report.get('seriousnessdeath') == '1'
            
            f.write(f"--- Report {i+1} (ID: {report.get('safetyreportid', 'N/A')}) ---\n")
            f.write(f"Date: {date}\n")
            f.write(f"Patient: {age}yo {sex}, {country}\n")
            f.write(f"Hospitalized: {hosp} | Death: {death}\n")
            f.write(f"Drugs: {', '.join(drugs)}\n")
            f.write(f"Reactions ({len(reactions)}): {', '.join(reactions)}\n")
            f.write(f"\n")
    
    print(f"Summary saved to: {summary_file}")
    return data

if __name__ == "__main__":
    # Default values
    drug = "ozempic"
    limit = 100
    serious = False
    
    # Parse command line arguments
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--drug' and i + 1 < len(args):
            drug = args[i + 1]
            i += 2
        elif args[i] == '--limit' and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
        elif args[i] == '--serious':
            serious = True
            i += 1
        else:
            i += 1
    
    pull_faers(drug, limit=limit, serious_only=serious)
