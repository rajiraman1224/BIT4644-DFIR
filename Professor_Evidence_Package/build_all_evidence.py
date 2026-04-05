#!/usr/bin/env python3
"""
BIT 4644 Capstone - Full Evidence Builder
Generates memory fragments (.raw) and GPS JPEGs for all 15 case variants.
Carrier JPEGs (for steghide) and hidden content files are also created.
Run: python3 build_all_evidence.py
"""

import os, sys, random, json, zipfile
sys.path.insert(0, os.path.dirname(__file__))
from gps_jpeg_builder import create_jpeg_with_gps

BUILD_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR   = os.path.join(BUILD_DIR, "evidence_sources")
os.makedirs(OUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# VARIANT MASTER TABLE
# Keys: passphrase, mem_string (what strings finds), GPS DMS, hidden file content
# ─────────────────────────────────────────────────────────────────────────────
VARIANTS = [
  # ── CASE 1: HEALTHCARE ────────────────────────────────────────────────────
  { "label":"HC_A","case":1,
    "suspect":"James Caldwell","role":"IT Administrator",
    "org":"Meridian Regional Medical Center",
    "passphrase":"M3ridian_2024!","mem_string":"Passphrase=M3ridian_2024!",
    "lat":(37,13,46.56,"N"),"lon":(80,24,50.04,"W"),
    "gps_desc":"Meridian North Parking Deck, Level 3 - Blacksburg, VA",
    "records":847,"penalty_per":50000,
    "photo":"meridian_photo_A.jpg","carrier":"backup_image_A.jpg",
    "memfile":"memory_fragment_A.raw","hidden":"stolen_records_A.csv",
    "case5tool":"Volatility","case5proc":"rclone.exe",
    "case5detail":"rclone copy C:\\\\Users\\\\jcaldwell\\\\Documents dropbox:jcaldwell_backup",
    "hidden_content":
"""patient_id,last_name,first_name,dob,ssn_partial,diagnosis,insurance_id
MRC-10847,Thornton,Eleanor,1952-03-14,xxx-xx-8841,Type 2 Diabetes / CKD Stage 3,BCBS-44129
MRC-10848,Vasquez,Carlos,1978-11-02,xxx-xx-2317,Hypertension / CAD,AETNA-88231
MRC-10849,Nguyen,Kim-Linh,1965-07-29,xxx-xx-5509,Breast Cancer Stage II,UHC-99104
MRC-10850,Patterson,Gregory,1941-12-08,xxx-xx-0073,Alzheimers Disease,MEDICARE-77341
MRC-10851,Ibrahim,Fatima,1990-04-17,xxx-xx-6628,HIV Positive on ART therapy,MEDICAID-33812
-- 842 additional records truncated --
TOTAL RECORDS EXFILTRATED: 847 | DATE: 2024-03-07 | DEST: dropbox.com/jcaldwell_backup
"""},

  { "label":"HC_B","case":1,
    "suspect":"Sarah Meyers","role":"Billing Coordinator",
    "org":"Meridian Regional Medical Center",
    "passphrase":"H1paaV@ult_99","mem_string":"steghide_key=H1paaV@ult_99",
    "lat":(37,13,44.40,"N"),"lon":(80,24,52.20,"W"),
    "gps_desc":"Meridian Server Room, Building B - Blacksburg, VA",
    "records":1203,"penalty_per":50000,
    "photo":"meridian_photo_B.jpg","carrier":"backup_image_B.jpg",
    "memfile":"memory_fragment_B.raw","hidden":"patient_data_B.csv",
    "case5tool":"Volatility","case5proc":"winscp.exe",
    "case5detail":"winscp.exe /script=C:\\\\Users\\\\smeyers\\\\AppData\\\\Temp\\\\upload.txt",
    "hidden_content":
"""patient_id,last_name,first_name,dob,ssn_partial,balance_owed,insurer,claim_status
MRC-20101,Whitfield,Deborah,1955-06-30,xxx-xx-4421,1847.00,CIGNA-10283,DENIED
MRC-20102,Chen,Robert,1982-09-15,xxx-xx-7730,322.50,BCBS-58841,PAID
MRC-20103,Washington,Alicia,1970-01-22,xxx-xx-1198,9450.00,SELF-PAY,OUTSTANDING
MRC-20104,Patel,Rajiv,1948-11-04,xxx-xx-8863,0.00,MEDICARE-44221,PAID
MRC-20105,Torres,Miguel,1993-05-08,xxx-xx-5547,7200.00,MEDICAID-29910,PENDING
-- 1198 additional billing records truncated --
TOTAL RECORDS: 1203 | DEST: smeyers_personal@gmail.com | DATE: 2024-04-12
"""},

  { "label":"HC_C","case":1,
    "suspect":"Robert Tran","role":"Network Engineer",
    "org":"Meridian Regional Medical Center",
    "passphrase":"P@tient_Trove7","mem_string":"StegPass: P@tient_Trove7",
    "lat":(37,13,49.32,"N"),"lon":(80,24,47.88,"W"),
    "gps_desc":"Meridian HR Annex Rooftop - Blacksburg, VA",
    "records":412,"penalty_per":50000,
    "photo":"meridian_photo_C.jpg","carrier":"backup_image_C.jpg",
    "memfile":"memory_fragment_C.raw","hidden":"phi_extract_C.csv",
    "case5tool":"Volatility","case5proc":"megasync.exe",
    "case5detail":"megasync.exe --upload C:\\\\Users\\\\rtran\\\\phi_backup\\\\",
    "hidden_content":
"""patient_id,last_name,first_name,dob,ssn_partial,diagnosis,prescriptions
MRC-30441,Murphy,Shannon,1968-02-19,xxx-xx-3312,Opioid Use Disorder,Suboxone 8mg/2mg
MRC-30442,Johnson,Terrell,1975-08-03,xxx-xx-9901,Major Depressive Disorder,Zoloft 100mg
MRC-30443,Kowalski,Barbara,1960-10-27,xxx-xx-2278,Hepatitis C,Harvoni 90mg/400mg
MRC-30444,Ahmad,Yusuf,1988-04-14,xxx-xx-6643,PTSD and Anxiety,Prazosin 2mg
MRC-30445,Delgado,Rosa,1979-12-31,xxx-xx-8814,HIV Positive (undetectable),Biktarvy 200mg
-- 407 additional records truncated --
TOTAL: 412 records | EXFIL: USB thumb drive | DATE: 2024-05-03
"""},

  # ── CASE 2: FINTECH ───────────────────────────────────────────────────────
  { "label":"FT_A","case":2,
    "suspect":"Marcus Webb","role":"Quantitative Analyst",
    "org":"Apex Capital Management",
    "passphrase":"Qu@ntAlpha_21","mem_string":"archive_key=Qu@ntAlpha_21",
    "lat":(40,45,28.80,"N"),"lon":(73,59,7.80,"W"),
    "gps_desc":"One Times Square, 42nd Floor - New York, NY",
    "records":0,"penalty_per":0,
    "photo":"apex_photo_A.jpg","carrier":"server_backup_A.jpg",
    "memfile":"server_memory_A.raw","hidden":"delta7_algorithm.txt",
    "case5tool":"Wireshark/tshark","case5proc":"tshark network capture",
    "case5detail":"14.2 MB upload to 104.244.42.1 (Dropbox API) at 23:47 EST on port 443",
    "hidden_content":
"""APEX CAPITAL - PROPRIETARY TRADING ALGORITHM DELTA-7
CLASSIFICATION: TOP SECRET / TRADE SECRET
Author: Marcus Webb | Last Modified: 2024-02-14
UNAUTHORIZED POSSESSION = FEDERAL ECONOMIC ESPIONAGE ACT VIOLATION

ALPHA_SIGNAL_WEIGHTS = {
    momentum_12m: 0.342,
    mean_reversion_5d: -0.218,
    vol_adjusted_carry: 0.487,
    sector_rotation_score: 0.391,
    macro_sentiment_idx: 0.224,
}

RISK_LIMITS = {
    max_drawdown_pct: 0.08,
    var_95_daily: 2400000,
    gross_exposure_cap: 180000000,
}

STOLEN BY MARCUS WEBB ON 2024-02-14
DESTINATION: HorizonQuant LLC (competitor) via encrypted email
"""},

  { "label":"FT_B","case":2,
    "suspect":"Diana Park","role":"Portfolio Manager",
    "org":"Apex Capital Management",
    "passphrase":"T3rminal_Risk!","mem_string":"steg_pass=T3rminal_Risk!",
    "lat":(40,45,32.04,"N"),"lon":(73,59,9.96,"W"),
    "gps_desc":"Apex Capital, 44th Floor Conference Room - New York, NY",
    "records":0,"penalty_per":0,
    "photo":"apex_photo_B.jpg","carrier":"server_backup_B.jpg",
    "memfile":"server_memory_B.raw","hidden":"client_portfolio_B.csv",
    "case5tool":"Wireshark/tshark","case5proc":"Google Drive upload",
    "case5detail":"HTTPS POST to drive.google.com from dpark.personal@gmail.com at 18:32 EST",
    "hidden_content":
"""client_id,name,aum_millions,strategy,target_return_pct,risk_tier
APC-001,Blackstone Family Office,425.0,Long/Short Equity,14.2,HIGH
APC-002,Sullivan Pension Fund,1200.0,Market Neutral,8.5,MED
APC-003,Thornton Endowment,87.5,Global Macro,11.0,HIGH
APC-004,Meridian Sovereign Fund,3400.0,Multi-Strat,9.8,LOW
APC-005,Cascade Family Partners,210.0,Event Driven,16.3,HIGH
-- DATA STOLEN BY D.PARK ON 2024-03-22 --
-- DESTINATION: CompetitorHedge LLC (interview package) --
TOTAL AUM REPRESENTED: $5.32 BILLION
"""},

  { "label":"FT_C","case":2,
    "suspect":"Kevin Osei","role":"Systems Developer",
    "org":"Apex Capital Management",
    "passphrase":"C@pital_F10w_X","mem_string":"Passphrase: C@pital_F10w_X",
    "lat":(40,45,26.64,"N"),"lon":(73,59,5.28,"W"),
    "gps_desc":"Midtown Manhattan Hotel Lobby, 47th St - New York, NY",
    "records":0,"penalty_per":0,
    "photo":"apex_photo_C.jpg","carrier":"server_backup_C.jpg",
    "memfile":"server_memory_C.raw","hidden":"risk_model_C.txt",
    "case5tool":"Wireshark/tshark","case5proc":"Signal Desktop encrypted attachment",
    "case5detail":"Encrypted archive model_params.zip detected in Signal Desktop process memory at 21:15 EST",
    "hidden_content":
"""APEX CAPITAL - PROPRIETARY RISK MODEL PARAMETERS
CLASSIFICATION: CONFIDENTIAL TRADE SECRET
Stolen by: Kevin Osei | Date: 2024-01-30

VOLATILITY MODULE:
EWMA_LAMBDA = 0.94
GARCH_P = 1, GARCH_Q = 1
STRESS_SCENARIOS = 2008_GFC, 2020_COVID, 1987_BLACK_MONDAY

VAR CALCULATION:
CONFIDENCE_LEVEL = 0.99
HOLDING_PERIOD_DAYS = 10
LOOKBACK_DAYS = 504
MONTE_CARLO_SIMS = 50000

CORRELATION MATRIX SEED FACTORS:
EQUITY_BOND_CORR = -0.31
EQUITY_COMMODITY_CORR = 0.22
CROSS_CURRENCY_BETA = 0.78

RECIPIENT: DataSystems Analytics Group LLC
METHOD: Encrypted archive via Signal
"""},

  # ── CASE 3: MANUFACTURING ─────────────────────────────────────────────────
  { "label":"MFG_A","case":3,
    "suspect":"Tyler Holt","role":"Senior Design Engineer",
    "org":"Wolverine Precision Components",
    "passphrase":"W0lver1ne_Steal!","mem_string":"Passphrase=W0lver1ne_Steal!",
    "lat":(42,19,53.04,"N"),"lon":(83,2,44.88,"W"),
    "gps_desc":"Wolverine Precision R&D Building C - Dearborn, MI",
    "records":0,"penalty_per":0,
    "photo":"wolverine_photo_A.jpg","carrier":"design_image_A.jpg",
    "memfile":"workstation_memory_A.raw","hidden":"cnc_specs_A.txt",
    "case5tool":"Sleuth Kit (fls/icat)","case5proc":"deleted archive: specs_backup.zip",
    "case5detail":"inode 14872: specs_backup.zip (42 MB) deleted 2024-04-09 17:43 - recovered via icat",
    "hidden_content":
"""WOLVERINE PRECISION COMPONENTS - PROPRIETARY CNC SPECIFICATIONS
PART: WPC-7741-Alpha Aerospace Bracket
CLASSIFICATION: TRADE SECRET / ITAR CONTROLLED
STOLEN BY: Tyler Holt | DATE: 2024-04-09

MATERIAL: 7075-T6 Aluminum Billet 18x12x4 inches

MACHINING PARAMETERS:
Spindle Speed: 8400 RPM (roughing) / 12000 RPM (finishing)
Feed Rate: 120 IPM (roughing) / 45 IPM (finishing)
Depth of Cut: 0.150 in (roughing) / 0.005 in (finishing)
Coolant: Flood at 450 PSI

TOLERANCES:
Bore diameter: 2.1875 in +0.0005/-0.0000
Flatness: 0.0003 in per 6 inches
Surface finish: 32 Ra microinches

DEFENSE CONTRACT: USAF F-35 Program Support
CUSTOMER: Lockheed Martin Aeronautics
CONTRACT VALUE: $4.2M annually
DESTINATION: HuaLong Precision Manufacturing, Shanghai
"""},

  { "label":"MFG_B","case":3,
    "suspect":"Angela Russo","role":"CAD Designer",
    "org":"Wolverine Precision Components",
    "passphrase":"C@dV@ult_Mfg22","mem_string":"steg_key=C@dV@ult_Mfg22",
    "lat":(42,19,51.12,"N"),"lon":(83,2,42.36,"W"),
    "gps_desc":"Wolverine Precision Loading Dock - Dearborn, MI",
    "records":0,"penalty_per":0,
    "photo":"wolverine_photo_B.jpg","carrier":"design_image_B.jpg",
    "memfile":"workstation_memory_B.raw","hidden":"alloy_formula_B.txt",
    "case5tool":"Sleuth Kit (fls/icat)","case5proc":"deleted archive: formula_docs.rar",
    "case5detail":"inode 22341: formula_docs.rar (8.3 MB) deleted 2024-02-28 19:12 - recovered via icat",
    "hidden_content":
"""WOLVERINE PRECISION COMPONENTS - PROPRIETARY ALLOY FORMULA
DESIGNATION: WPC-MAX-9 Superalloy Blend
CLASSIFICATION: TRADE SECRET
STOLEN BY: Angela Russo | DATE: 2024-02-28

BASE COMPOSITION (weight percent):
Nickel (Ni): 57.2
Chromium (Cr): 19.1
Molybdenum (Mo): 9.8
Iron (Fe): 5.3
Cobalt (Co): 4.6
Niobium (Nb): 2.8
Titanium (Ti): 0.9
Aluminum (Al): 0.3

HEAT TREATMENT:
Stage 1: 1080C / 2h / Air Cool
Stage 2: 845C / 24h / Air Cool
Stage 3: 760C / 8h / Air Cool

MECHANICAL PROPERTIES:
UTS: 185000 PSI | Yield: 160000 PSI | Hardness: 38 HRC

R&D COST TO DEVELOP: $3.7 million over 6 years
DESTINATION: Meridian Metals International Inc (competitor)
"""},

  { "label":"MFG_C","case":3,
    "suspect":"Priya Nair","role":"Process Engineer",
    "org":"Wolverine Precision Components",
    "passphrase":"Pr0cess_Secr3t!","mem_string":"StegPass: Pr0cess_Secr3t!",
    "lat":(42,19,55.20,"N"),"lon":(83,2,47.04,"W"),
    "gps_desc":"Detroit Marriott Renaissance Center, Lobby - Detroit, MI",
    "records":0,"penalty_per":0,
    "photo":"wolverine_photo_C.jpg","carrier":"design_image_C.jpg",
    "memfile":"workstation_memory_C.raw","hidden":"process_blueprint_C.txt",
    "case5tool":"Sleuth Kit (fls/icat)","case5proc":"deleted archive: assembly_proc.7z",
    "case5detail":"inode 31089: assembly_proc.7z (31 MB) deleted 2024-03-15 21:04 - recovered via icat",
    "hidden_content":
"""WOLVERINE PRECISION COMPONENTS - ASSEMBLY PROCESS BLUEPRINT
PRODUCT: WPC-Series 900 Turbine Disk Assembly
CLASSIFICATION: PROPRIETARY / EXPORT CONTROLLED (EAR99)
STOLEN BY: Priya Nair | DATE: 2024-03-15

STAGE 1 - PRE-ASSEMBLY INSPECTION:
Dimensional check per WPC-QC-0041 CMM Protocol
Reject criteria: Any surface defect greater than 0.002 in depth
Required cert: AS9100D Level 3 inspector signature

STAGE 2 - PRECISION BALANCING:
Equipment: Schenck HM-14 Balancing Machine
Spec: Residual imbalance max 0.1 g-mm/kg (ISO 1940-1 Grade G1)
Procedure: 3-plane correction at 3600 RPM

STAGE 3 - INTERFERENCE FIT ASSEMBLY:
Disk bore temp: -196C (LN2 bath, 45 min minimum)
Housing temp: +175C (oven, 30 min minimum)
Assembly window: 90 seconds maximum

STAGE 4 - NDT INSPECTION:
Method: Fluorescent Penetrant Inspection (FPI) per ASTM E1417
Acceptance: Zero relevant indications greater than 0.020 in

COMPETITOR RECEIVING: AeroParts Global Ltd, Toronto
ECONOMIC VALUE: Process IP conservatively valued at $12M
"""},

  # ── CASE 4: E-COMMERCE ────────────────────────────────────────────────────
  { "label":"ECOM_A","case":4,
    "suspect":"Connor Walsh","role":"Web Developer",
    "org":"ShopSphere Inc.",
    "passphrase":"Sph3re_Sk1m!","mem_string":"archive_pass=Sph3re_Sk1m!",
    "lat":(47,36,22.32,"N"),"lon":(122,19,55.56,"W"),
    "gps_desc":"ShopSphere HQ, Developer Floor 3rd - Seattle, WA",
    "records":4832,"penalty_per":90,
    "photo":"shopsphere_photo_A.jpg","carrier":"product_backup_A.jpg",
    "memfile":"server_mem_A.raw","hidden":"card_dump_A.csv",
    "case5tool":"Foremost","case5proc":"checkout_skimmer.js (1.2 KB)",
    "case5detail":"Carved from unallocated space sector 2847331; JS card skimmer exfiltrating to 185.220.101.47:9443",
    "hidden_content":
"""card_number_masked,exp_date,cvv_present,billing_zip,transaction_date,amount
4532-xxxx-xxxx-7841,09/26,YES,98101,2024-04-01,$142.99
4716-xxxx-xxxx-3312,11/25,YES,10019,2024-04-01,$89.50
5425-xxxx-xxxx-9901,03/27,YES,60611,2024-04-01,$334.00
4929-xxxx-xxxx-2278,07/26,YES,94102,2024-04-01,$27.49
4539-xxxx-xxxx-6643,12/25,YES,30301,2024-04-01,$199.99
-- 4827 additional card records --
TOTAL CARDS COMPROMISED: 4832
SKIMMER ACTIVE: 2024-03-15 through 2024-04-01 (17 days)
EXFIL ENDPOINT: 185.220.101.47:9443 (TOR exit node Frankfurt)
DEVELOPER: Connor Walsh (resigned 2024-04-02)
"""},

  { "label":"ECOM_B","case":4,
    "suspect":"Lily Zhang","role":"Database Administrator",
    "org":"ShopSphere Inc.",
    "passphrase":"D@tabase_L00t_22","mem_string":"steg_passphrase=D@tabase_L00t_22",
    "lat":(47,36,25.20,"N"),"lon":(122,19,53.40,"W"),
    "gps_desc":"ShopSphere HQ, Database Server Room Basement - Seattle, WA",
    "records":11456,"penalty_per":90,
    "photo":"shopsphere_photo_B.jpg","carrier":"product_backup_B.jpg",
    "memfile":"server_mem_B.raw","hidden":"card_export_B.csv",
    "case5tool":"Foremost","case5proc":"export_query.sql (3.1 KB)",
    "case5detail":"Carved from /tmp slack space; contains SELECT * FROM payment_methods targeting all card data",
    "hidden_content":
"""card_number_masked,cardholder,exp_date,billing_state,email,total_spend_2024
5105-xxxx-xxxx-4100,Jennifer Morrison,04/27,GA,jmorrison@email.com,$4211.88
4111-xxxx-xxxx-1111,David Kowalski,08/26,IL,dkowalski@webmail.net,$891.22
5500-xxxx-xxxx-0004,Sandra Lee,02/28,CA,slee@fastmail.com,$12440.00
4222-xxxx-xxxx-2222,Antonio Rivera,11/25,NY,arivera@mail.net,$3108.75
3714-xxxx-xxxx-963,Patricia Dumont,06/27,MA,pdumont@emailbox.com,$6782.50
-- 11451 additional records --
TOTAL RECORDS EXPORTED: 11456
METHOD: mysqldump via DBA credentials piped to card_export.csv
EXFIL: Sent via encrypted email to lzhang@personalbox.io on 2024-05-20
"""},

  # ── CASE 5: LEGAL SERVICES ────────────────────────────────────────────────
  { "label":"LEGAL_A","case":5,
    "suspect":"Nathan Keller","role":"Associate Attorney",
    "org":"Hartwell and Associates LLP",
    "passphrase":"H@rtw3ll_Vault!","mem_string":"Passphrase=H@rtw3ll_Vault!",
    "lat":(38,54,25.92,"N"),"lon":(77,2,12.84,"W"),
    "gps_desc":"Hartwell and Associates LLP, 17th Floor - Washington, DC",
    "records":0,"penalty_per":0,
    "photo":"hartwell_photo_A.jpg","carrier":"legal_backup_A.jpg",
    "memfile":"attorney_mem_A.raw","hidden":"merger_docs_A.txt",
    "case5tool":"RegRipper","case5proc":"USBStor registry key",
    "case5detail":"SanDisk Cruzer 32GB Serial 4C530001240322116102 last connected 2024-06-03 14:22 - 2.1 GB transferred",
    "hidden_content":
"""HARTWELL AND ASSOCIATES LLP - PRIVILEGED AND CONFIDENTIAL
ATTORNEY-CLIENT PRIVILEGED COMMUNICATION
STOLEN BY: Nathan Keller (Associate, M&A Practice) | DATE: 2024-06-03

CLIENT: NovaBridge Technologies Inc.
MATTER: Project Halo - Proposed Acquisition of StellarAI Corp
DEAL VALUE: $2.3 BILLION

KEY DEAL TERMS (DRAFT):
Purchase Price: $2.3B cash plus $140M earnout (3-year)
HSR Filing Required: YES (FTC Second Request anticipated)
Exclusivity Period: 45 days (expires 2024-07-18)
Break-up Fee: $115M (5% of deal value)

VULNERABILITIES IDENTIFIED:
1. StellarAI pending patent challenge (PTAB IPR-2024-00441) - could reduce value by $400M
2. Two customer contracts have change-of-control clauses (Google, Microsoft)
3. Undisclosed data breach in Q3 2023 - potential SEC disclosure issue

DESTINATION: Keller shared with rival firm Meridian Capital Advisors to facilitate competing bid
"""},

  { "label":"LEGAL_B","case":5,
    "suspect":"Monica Cruz","role":"Legal Assistant",
    "org":"Hartwell and Associates LLP",
    "passphrase":"L3gal_L3ak_23","mem_string":"steg_key=L3gal_L3ak_23",
    "lat":(38,54,23.40,"N"),"lon":(77,2,15.00,"W"),
    "gps_desc":"Dupont Circle Coffee Shop, P Street NW - Washington, DC",
    "records":0,"penalty_per":0,
    "photo":"hartwell_photo_B.jpg","carrier":"legal_backup_B.jpg",
    "memfile":"attorney_mem_B.raw","hidden":"litigation_strategy_B.txt",
    "case5tool":"RegRipper","case5proc":"OneDrive sync registry artifacts",
    "case5detail":"mcruz.legal.docs@hotmail.com OneDrive sync - 847 MB uploaded - last sync 2024-07-11 19:43",
    "hidden_content":
"""HARTWELL AND ASSOCIATES LLP - PRIVILEGED AND CONFIDENTIAL
WORK PRODUCT DOCTRINE / ATTORNEY-CLIENT PRIVILEGE
STOLEN BY: Monica Cruz (Legal Assistant) | DATE: 2024-07-11

CLIENT: Redwood Pharmaceuticals Inc.
MATTER: Redwood v. GeneriCo LLC (Patent Infringement)
CASE NO.: 2:24-cv-04412-DLR (D. Ariz.)
TRIAL DATE: 2025-01-13
ESTIMATED DAMAGE CLAIM: $340 million

LITIGATION STRATEGY (CONFIDENTIAL WORK PRODUCT):
1. Lead expert: Dr. Amara Singh (MIT) - testifying re GeneriCo reverse engineering
2. KEY WEAKNESS: Chain of custody gap in Exhibit 17 (lab notebooks)
3. Motion for summary judgment planned by 2024-09-30
4. Settlement authority: Client authorized settlement down to $85M (DO NOT DISCLOSE)
5. Adverse expert Dr. Ben Fowler has contradictory testimony in MDL-2021-0882

SEVEN AFFECTED CLIENTS:
Redwood Pharma, Cascade Bio, Lumen Health, NorthStar Medical,
PineTree Diagnostics, Summit Surgical, Evergreen Labs

DESTINATION: GeneriCo law firm Davis and Harrington LLP for $45000 payment
"""},
]


# ─────────────────────────────────────────────────────────────────────────────
def create_memory_fragment(v, out_dir):
    """Create a realistic binary memory fragment with the passphrase embedded."""
    random.seed(hash(v["label"] + "_mem") % 2**31)

    def noise(n): return bytes([random.randint(0,255) for _ in range(n)])
    def string_block(s): return s.encode("utf-8") + b"\x00"

    buf = bytearray()
    buf += noise(1024)

    # Windows environment block strings
    uname = v["suspect"].split()[0].lower()
    for s in [
        f"COMPUTERNAME={uname.upper()[:8]}WS01",
        f"USERNAME={uname}",
        "USERDOMAIN=CORP",
        f"APPDATA=C:\\Users\\{uname}\\AppData\\Roaming",
        f"TEMP=C:\\Users\\{uname}\\AppData\\Local\\Temp",
        "PATH=C:\\Windows\\system32;C:\\Windows;C:\\Program Files\\Python311",
        "OS=Windows_NT", "PROCESSOR_ARCHITECTURE=AMD64",
        "SystemRoot=C:\\Windows",
    ]:
        buf += noise(random.randint(64, 256))
        buf += string_block(s)

    buf += noise(2048)

    # Command history
    for s in [
        "cmd.exe /c dir C:\\Users\\Documents\\",
        "powershell.exe -ExecutionPolicy Bypass",
        "7z.exe a -p archive.zip .",
        "xcopy /s /e C:\\Users\\Documents backup\\",
        f"steghide.exe -sf {v['carrier']} -p",
    ]:
        buf += noise(random.randint(128, 512))
        buf += string_block(s)

    buf += noise(4096)

    # THE KEY ARTIFACT: passphrase string students must find
    for s in [
        "steghide.exe",
        f"-sf {v['carrier']}",
        v["mem_string"],          # <-- this is what grep finds
        "--extract",
        f"wrote extracted data to {v['hidden']}",
    ]:
        buf += noise(random.randint(8, 32))
        buf += string_block(s)

    buf += noise(8192)

    # Registry-like strings
    for s in [
        "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
        "SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion",
        f"LastLogon={uname}",
        "MRUList=abcdefghijklmnop",
    ]:
        buf += noise(random.randint(64, 256))
        buf += string_block(s)

    buf += noise(16384)

    # Network strings
    for s in [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type: application/octet-stream",
        "Transfer-Encoding: chunked",
        f"X-Forwarded-For: 192.168.{random.randint(1,254)}.{random.randint(1,254)}",
        "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9",
    ]:
        buf += noise(random.randint(128, 512))
        buf += string_block(s)

    buf += noise(random.randint(4096, 8192))

    path = os.path.join(out_dir, v["memfile"])
    with open(path, "wb") as f:
        f.write(bytes(buf))
    return path


def create_carrier_jpeg(v, out_dir):
    """Create a plain JPEG that the professor will embed steghide content into."""
    from PIL import Image, ImageDraw
    random.seed(hash(v["label"] + "_carrier") % 2**31)

    palettes = {1:(180,200,220), 2:(200,180,155), 3:(155,175,155), 4:(195,160,200), 5:(178,172,192)}
    br, bg, bb = palettes.get(v["case"], (180,180,180))

    img = Image.new("RGB", (800, 600))
    px  = img.load()
    for y in range(600):
        for x in range(800):
            n = random.randint(-12, 12)
            px[x,y] = (
                max(0,min(255, br + int(x/800*30) - int(y/600*20) + n)),
                max(0,min(255, bg + int(x/800*25) - int(y/600*15) + n)),
                max(0,min(255, bb + int(x/800*20) - int(y/600*10) + n)),
            )
    draw = ImageDraw.Draw(img)
    for _ in range(6):
        x0 = random.randint(40,600); y0 = random.randint(40,400)
        shade = random.randint(25,60)
        draw.rectangle([x0,y0,x0+random.randint(80,200),y0+random.randint(60,150)],
                       fill=(max(0,br-shade), max(0,bg-shade), max(0,bb-shade)))

    path = os.path.join(out_dir, v["carrier"])
    img.save(path, "JPEG", quality=88)
    return path


def create_hidden_content(v, out_dir):
    path = os.path.join(out_dir, v["hidden"])
    with open(path, "w") as f:
        f.write(v["hidden_content"].strip() + "\n")
    return path


# ─────────────────────────────────────────────────────────────────────────────
def main():
    manifest = {}

    for v in VARIANTS:
        label = v["label"]
        vdir  = os.path.join(OUT_DIR, label)
        os.makedirs(vdir, exist_ok=True)
        print(f"\n[{label}] {v['suspect']} @ {v['org']}")

        # 1. GPS JPEG (photo with location evidence)
        ld,lm,ls,lr = v["lat"]
        od,om,os_,or_ = v["lon"]
        photo_path = os.path.join(vdir, v["photo"])
        create_jpeg_with_gps(photo_path, label, v["suspect"],
                             ld,lm,ls,lr, od,om,os_,or_,
                             seed=hash(label+"_photo") % 2**31)
        print(f"  GPS photo:    {v['photo']}  ({ld}deg{lm}'{ls:.2f}\" {lr})")

        # 2. Memory fragment
        mem_path = create_memory_fragment(v, vdir)
        print(f"  Memory raw:   {v['memfile']}  ({os.path.getsize(mem_path)//1024} KB)")

        # 3. Carrier JPEG (for steghide)
        carrier_path = create_carrier_jpeg(v, vdir)
        print(f"  Carrier JPEG: {v['carrier']}  (needs steghide embed on SIFT)")

        # 4. Hidden content text
        content_path = create_hidden_content(v, vdir)
        print(f"  Hidden file:  {v['hidden']}")

        manifest[label] = {
            "case": v["case"], "org": v["org"],
            "suspect": v["suspect"], "role": v["role"],
            "passphrase": v["passphrase"],
            "gps_desc": v["gps_desc"],
            "gps_lat_dms": f"{ld}d{lm}'{ls:.2f}\"{lr}",
            "gps_lon_dms": f"{od}d{om}'{os_:.2f}\"{or_}",
            "records": v["records"],
            "hidden_file": v["hidden"],
            "files_generated": [v["photo"], v["memfile"], v["carrier"], v["hidden"]],
            "steghide_needed": True,
        }

    # Write manifest
    mpath = os.path.join(OUT_DIR, "evidence_manifest.json")
    with open(mpath,"w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest: {mpath}")
    print(f"\nDone. {len(VARIANTS)} variants generated in {OUT_DIR}/")
    print("Next step: run embed_steganography.sh on SIFT workstation to embed hidden content.")


if __name__ == "__main__":
    main()
