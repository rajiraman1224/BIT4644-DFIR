#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# BIT 4644 — Full Evidence Validation (All 13 Cases)
# Tests EVERY command students are given in the assignment document, phase by phase.
#
# Phases tested:
#   Phase 0  — Download from GitHub, extract, ls -lh, sha256sum
#   Phase 1  — strings: find passphrase + steghide invocation in memory
#   Phase 2  — ent: entropy baseline (photo) vs elevated (carrier)
#   Phase 3  — steghide info, steghide extract, ls -lh, cat hidden file
#   Phase 4  — exiftool GPS, Date, Make/Model
#   Phase 5  — strings: HTTP, IP, Bearer, cloud exfil, industry-specific
#
# Usage:
#   bash test_all_cases.sh                  # download from GitHub then test
#   bash test_all_cases.sh --skip-download  # test already-extracted local files
#
# Evidence is extracted to: ~/professor_evidence_package/{LABEL}/
# ─────────────────────────────────────────────────────────────────────────────

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; GRAY='\033[0;37m'; NC='\033[0m'

TOTAL_PASS=0; TOTAL_FAIL=0; TOTAL_WARN=0
declare -A CASE_RESULTS

ok()   { echo -e "    ${GREEN}✓${NC} $1"; TOTAL_PASS=$((TOTAL_PASS+1)); }
fail() { echo -e "    ${RED}✗${NC} $1"; TOTAL_FAIL=$((TOTAL_FAIL+1)); CASE_FAIL=$((CASE_FAIL+1)); }
warn() { echo -e "    ${YELLOW}⚠${NC} $1"; TOTAL_WARN=$((TOTAL_WARN+1)); }
info() { echo -e "    ${GRAY}→${NC} $1"; }

# ── GitHub base URL ───────────────────────────────────────────────────────────
GITHUB_BASE="https://raw.githubusercontent.com/rajiraman1224/BIT4644-DFIR/main/Capstone"

# ── Parse flags ───────────────────────────────────────────────────────────────
SKIP_DOWNLOAD=0
[[ "$1" == "--skip-download" ]] && SKIP_DOWNLOAD=1

# ── Evidence root ─────────────────────────────────────────────────────────────
EVIDENCE_ROOT="$HOME/professor_evidence_package"
mkdir -p "$EVIDENCE_ROOT"

echo ""
echo -e "${BOLD}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  BIT 4644 — Evidence Validation (All 13 Cases, All Phases)${NC}"
if [[ $SKIP_DOWNLOAD -eq 0 ]]; then
  echo -e "${BOLD}  Mode: Download from GitHub + Validate${NC}"
else
  echo -e "${BOLD}  Mode: Validate local files only (--skip-download)${NC}"
fi
echo -e "${BOLD}  Evidence root: $EVIDENCE_ROOT${NC}"
echo -e "${BOLD}════════════════════════════════════════════════════════════════${NC}"

# ── Pre-flight: required tools ────────────────────────────────────────────────
echo ""
echo -e "${CYAN}── Pre-flight: Tool Check ──────────────────────────────────────${NC}"
MISSING=0
for tool in wget unzip exiftool steghide strings sha256sum ent; do
  if command -v "$tool" &>/dev/null; then
    VER=$(($tool --version 2>/dev/null || $tool -ver 2>/dev/null || echo "ok") | head -1)
    echo -e "    ${GREEN}✓${NC} $tool"
  else
    echo -e "    ${RED}✗${NC} $tool — NOT FOUND"
    MISSING=$((MISSING+1))
  fi
done
if [[ $MISSING -gt 0 ]]; then
  echo ""
  echo -e "  ${RED}$MISSING tool(s) missing. Install with:${NC}"
  echo -e "  ${GRAY}sudo apt-get install ent steghide libimage-exiftool-perl${NC}"
  exit 1
fi

# ── Industry-specific grep pattern ───────────────────────────────────────────
industry_grep() {
  case ${1:0:2} in
    HC) echo "(patient|SSN|DOB|diagnosis|MRN|HIPAA|HL7|FHIR)" ;;
    FT) echo "(account|routing|SWIFT|IBAN|ticker|trade|portfolio|api.key|token)" ;;
    MF) echo "(\\.dwg|\\.cad|\\.step|\\.iges|blueprint|schematic|BOM|CNC)" ;;
    EC) echo "(card.number|CVV|expir|checkout|order.id|PAN|PCI)" ;;
    LE) echo "(attorney|counsel|privileged|confidential|litigation|docket|ACP)" ;;
  esac
}

# ── Case definitions ──────────────────────────────────────────────────────────
# Format: "LABEL|CARRIER|MEMFILE|HIDDEN|PASSPHRASE|PHOTO"
declare -a CASES=(
  "HC_A|backup_image_A.jpg|memory_fragment_A.raw|stolen_records_A.csv|M3ridian_2024!|meridian_photo_A.jpg"
  "HC_B|backup_image_B.jpg|memory_fragment_B.raw|patient_data_B.csv|H1paaV@ult_99|meridian_photo_B.jpg"
  "HC_C|backup_image_C.jpg|memory_fragment_C.raw|phi_extract_C.csv|P@tient_Trove7|meridian_photo_C.jpg"
  "FT_A|server_backup_A.jpg|server_memory_A.raw|delta7_algorithm.txt|Qu@ntAlpha_21|apex_photo_A.jpg"
  "FT_B|server_backup_B.jpg|server_memory_B.raw|client_portfolio_B.csv|T3rminal_Risk!|apex_photo_B.jpg"
  "FT_C|server_backup_C.jpg|server_memory_C.raw|risk_model_C.txt|C@pital_F10w_X|apex_photo_C.jpg"
  "MFG_A|design_image_A.jpg|workstation_memory_A.raw|cnc_specs_A.txt|W0lver1ne_Steal!|wolverine_photo_A.jpg"
  "MFG_B|design_image_B.jpg|workstation_memory_B.raw|alloy_formula_B.txt|C@dV@ult_Mfg22|wolverine_photo_B.jpg"
  "MFG_C|design_image_C.jpg|workstation_memory_C.raw|process_blueprint_C.txt|Pr0cess_Secr3t!|wolverine_photo_C.jpg"
  "ECOM_A|product_backup_A.jpg|server_mem_A.raw|card_dump_A.csv|Sph3re_Sk1m!|shopsphere_photo_A.jpg"
  "ECOM_B|product_backup_B.jpg|server_mem_B.raw|card_export_B.csv|D@tabase_L00t_22|shopsphere_photo_B.jpg"
  "LEGAL_A|legal_backup_A.jpg|attorney_mem_A.raw|merger_docs_A.txt|H@rtw3ll_Vault!|hartwell_photo_A.jpg"
  "LEGAL_B|legal_backup_B.jpg|attorney_mem_B.raw|litigation_strategy_B.txt|L3gal_L3ak_23|hartwell_photo_B.jpg"
)

# ── Test each case ────────────────────────────────────────────────────────────
for case_def in "${CASES[@]}"; do
  IFS='|' read -r LABEL CARRIER MEMFILE HIDDEN PASSPHRASE PHOTO <<< "$case_def"
  CASE_DIR="$EVIDENCE_ROOT/$LABEL"
  CASE_FAIL=0

  echo ""
  echo -e "${CYAN}${BOLD}━━ $LABEL ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

  # ════════════════════════════════════════════════════════════════
  # PHASE 0 — Environment Setup (download, extract, hash)
  # Commands students run:
  #   mkdir -p ~/Desktop/Capstone_XX && cd ...
  #   wget {url}
  #   unzip {zip}
  #   ls -lh
  #   sha256sum *
  # ════════════════════════════════════════════════════════════════
  echo -e "  ${BOLD}Phase 0 — Download & Chain of Custody${NC}"

  if [[ $SKIP_DOWNLOAD -eq 0 ]]; then
    ZIP_URL="${GITHUB_BASE}/${LABEL}_Evidence.zip"
    ZIP_FILE="$EVIDENCE_ROOT/${LABEL}_Evidence.zip"

    info "wget $ZIP_URL"
    wget -q --timeout=60 "$ZIP_URL" -O "$ZIP_FILE" 2>/dev/null
    if [[ $? -ne 0 || ! -s "$ZIP_FILE" ]]; then
      fail "wget failed — ${LABEL}_Evidence.zip not found at GitHub URL"
      fail "  URL: $ZIP_URL"
      warn "  Upload this zip to GitHub before running this test."
      CASE_RESULTS[$LABEL]="FAIL(download)"
      continue
    fi
    SIZE=$(du -h "$ZIP_FILE" | cut -f1)
    ok "wget: downloaded ${LABEL}_Evidence.zip ($SIZE)"

    # unzip
    rm -rf "$CASE_DIR" && mkdir -p "$CASE_DIR"
    info "unzip ${LABEL}_Evidence.zip"
    unzip -q "$ZIP_FILE" -d "$CASE_DIR" 2>/dev/null
    # Flatten if zip created a subfolder
    if [[ ! -f "$CASE_DIR/$CARRIER" ]]; then
      SUBDIR=$(find "$CASE_DIR" -maxdepth 1 -mindepth 1 -type d | head -1)
      [[ -n "$SUBDIR" ]] && mv "$SUBDIR"/* "$CASE_DIR/" 2>/dev/null && rmdir "$SUBDIR" 2>/dev/null
    fi
    [[ -f "$CASE_DIR/$CARRIER" ]] && ok "unzip: extracted successfully" \
                                   || { fail "unzip: files not found after extraction"; CASE_RESULTS[$LABEL]="FAIL(unzip)"; continue; }
  fi

  # ls -lh: verify all 3 evidence files exist with non-zero size
  info "ls -lh (checking all 3 evidence files)"
  ALL_FILES=1
  for f in "$CARRIER" "$MEMFILE" "$PHOTO"; do
    if [[ -f "$CASE_DIR/$f" && -s "$CASE_DIR/$f" ]]; then
      SZ=$(du -h "$CASE_DIR/$f" | cut -f1)
      ok "  ls: $f  [$SZ]"
    else
      fail "  ls: $f — MISSING or empty"
      ALL_FILES=0
    fi
  done
  [[ $ALL_FILES -eq 0 ]] && { CASE_RESULTS[$LABEL]="FAIL(files)"; continue; }

  # sha256sum *  — record hashes (students must document these)
  info "sha256sum * (chain of custody hashes)"
  for f in "$CARRIER" "$MEMFILE" "$PHOTO"; do
    HASH=$(sha256sum "$CASE_DIR/$f" 2>/dev/null | awk '{print $1}')
    if [[ -n "$HASH" ]]; then
      ok "  sha256: $f = ${HASH:0:20}...${HASH: -8}"
    else
      fail "  sha256sum failed for $f"
    fi
  done

  # ════════════════════════════════════════════════════════════════
  # PHASE 1 — Memory String Analysis
  # Commands students run:
  #   strings {memfile} | grep -i "pass"
  #   strings {memfile} | grep -i "steg"
  #   strings {memfile} | grep -iE "(key|vault|archive)" | head -20
  # Expected: passphrase and "steghide.exe" are embedded in the .raw file
  # ════════════════════════════════════════════════════════════════
  echo ""
  echo -e "  ${BOLD}Phase 1 — Memory String Analysis (strings)${NC}"

  # strings | grep -i "steg"  →  must find "steghide.exe" embedded in memory
  info "strings $MEMFILE | grep -i \"steg\""
  STEG_LINES=$(strings "$CASE_DIR/$MEMFILE" | grep -i "steg")
  STEG_COUNT=$(echo "$STEG_LINES" | grep -c "steghide" 2>/dev/null || echo 0)
  if [[ $STEG_COUNT -gt 0 ]]; then
    SAMPLE=$(echo "$STEG_LINES" | grep "steghide" | head -1)
    ok "  grep steg: found \"$SAMPLE\""
  else
    fail "  grep steg: 'steghide' string not in $MEMFILE — students cannot complete Phase 1"
  fi

  # strings | grep -i "pass"  →  should surface the passphrase for most cases
  info "strings $MEMFILE | grep -i \"pass\""
  PASS_LINES=$(strings "$CASE_DIR/$MEMFILE" | grep -i "pass")
  if [[ -n "$PASS_LINES" ]]; then
    ok "  grep pass: found password-related strings"
    info "    $(echo "$PASS_LINES" | head -1)"
  else
    warn "  grep pass: no hits — students may need the broader grep (key|vault|archive)"
  fi

  # Ground truth: is the actual passphrase findable anywhere in the memory file?
  info "Verifying passphrase '$PASSPHRASE' is findable in memory"
  PASS_FOUND=$(strings "$CASE_DIR/$MEMFILE" | grep -cF "$PASSPHRASE" 2>/dev/null || echo 0)
  if [[ $PASS_FOUND -gt 0 ]]; then
    ok "  Passphrase found in memory strings ✓ (students CAN complete Phase 1)"
  else
    fail "  Passphrase '$PASSPHRASE' NOT found in $MEMFILE — Phase 3 is blocked"
  fi

  # ════════════════════════════════════════════════════════════════
  # PHASE 2 — Entropy Analysis (ent)
  # Commands students run:
  #   ent {photo}     →  baseline ~7.5-7.9 bits/byte (normal JPEG)
  #   ent {carrier}   →  elevated  ~7.9-8.0 bits/byte (steganography present)
  #   ls -lh {photo} {carrier}
  # ════════════════════════════════════════════════════════════════
  echo ""
  echo -e "  ${BOLD}Phase 2 — Entropy Analysis (ent)${NC}"

  # Photo entropy — should be normal JPEG range
  info "ent $PHOTO"
  ENT_PHOTO_RAW=$(ent "$CASE_DIR/$PHOTO" 2>/dev/null | grep "Entropy" | awk '{print $3}')
  if [[ -n "$ENT_PHOTO_RAW" ]]; then
    ENT_PHOTO_INT=$(echo "$ENT_PHOTO_RAW" | awk '{printf "%d", $1*10}')
    if [[ $ENT_PHOTO_INT -ge 70 && $ENT_PHOTO_INT -le 80 ]]; then
      ok "  ent $PHOTO = ${ENT_PHOTO_RAW} bits/byte (normal JPEG ✓)"
    else
      warn "  ent $PHOTO = ${ENT_PHOTO_RAW} bits/byte (expected 7.0-8.0)"
    fi
  else
    fail "  ent failed on $PHOTO"
  fi

  # Carrier entropy — should be elevated (steghide embeds encrypted data)
  info "ent $CARRIER"
  ENT_CARRIER_RAW=$(ent "$CASE_DIR/$CARRIER" 2>/dev/null | grep "Entropy" | awk '{print $3}')
  if [[ -n "$ENT_CARRIER_RAW" ]]; then
    ENT_CARRIER_INT=$(echo "$ENT_CARRIER_RAW" | awk '{printf "%d", $1*100}')
    if [[ $ENT_CARRIER_INT -ge 780 ]]; then
      ok "  ent $CARRIER = ${ENT_CARRIER_RAW} bits/byte (elevated — steganography present ✓)"
    else
      warn "  ent $CARRIER = ${ENT_CARRIER_RAW} bits/byte — may be low if steghide not yet run"
      warn "  Run embed_steganography.sh first, then re-test"
    fi
  else
    fail "  ent failed on $CARRIER"
  fi

  # ════════════════════════════════════════════════════════════════
  # PHASE 3 — Steganographic Data Extraction (steghide)
  # Commands students run:
  #   steghide info {carrier}
  #   steghide extract -sf {carrier} -p [passphrase]
  #   ls -lh {hidden}
  #   cat {hidden}
  # ════════════════════════════════════════════════════════════════
  echo ""
  echo -e "  ${BOLD}Phase 3 — Steganographic Extraction (steghide)${NC}"

  TMPDIR=$(mktemp -d)
  cp "$CASE_DIR/$CARRIER" "$TMPDIR/"

  # steghide info — confirms hidden data is present (no passphrase needed for detection)
  info "steghide info $CARRIER"
  STEG_INFO=$(steghide info "$TMPDIR/$CARRIER" -p "$PASSPHRASE" 2>&1)
  if echo "$STEG_INFO" | grep -qi "embedded"; then
    ok "  steghide info: hidden data confirmed in $CARRIER"
    CAPACITY=$(echo "$STEG_INFO" | grep -i "capacity\|size" | head -1 | xargs)
    [[ -n "$CAPACITY" ]] && info "    $CAPACITY"
  else
    fail "  steghide info: no embedded data reported — carrier not yet processed by steghide"
    warn "    Run embed_steganography.sh on SIFT first, then re-upload to GitHub"
  fi

  # steghide extract
  info "steghide extract -sf $CARRIER -p [passphrase]"
  cd "$TMPDIR"
  steghide extract -sf "$CARRIER" -p "$PASSPHRASE" -f 2>/dev/null
  EXTRACT_STATUS=$?
  if [[ $EXTRACT_STATUS -eq 0 && -f "$HIDDEN" ]]; then
    ok "  steghide extract: wrote \"$HIDDEN\""
  else
    fail "  steghide extract: FAILED (exit $EXTRACT_STATUS) — wrong passphrase or carrier not processed"
  fi

  # ls -lh {hidden}
  if [[ -f "$HIDDEN" ]]; then
    LS_SIZE=$(ls -lh "$HIDDEN" 2>/dev/null | awk '{print $5}')
    ok "  ls -lh $HIDDEN: $LS_SIZE"
  else
    fail "  ls -lh: $HIDDEN not produced by extraction"
  fi

  # cat {hidden} — first line must be non-empty
  info "cat $HIDDEN (first 2 lines)"
  if [[ -f "$HIDDEN" ]]; then
    LINE1=$(head -1 "$HIDDEN")
    LINE2=$(head -2 "$HIDDEN" | tail -1)
    LINECOUNT=$(wc -l < "$HIDDEN")
    if [[ -n "$LINE1" ]]; then
      ok "  cat: $LINECOUNT lines — first: \"${LINE1:0:60}...\""
    else
      fail "  cat: extracted file is empty"
    fi
  fi

  cd - > /dev/null
  rm -rf "$TMPDIR"

  # ════════════════════════════════════════════════════════════════
  # PHASE 4 — EXIF Metadata & GPS Location (exiftool)
  # Commands students run:
  #   exiftool {photo}
  #   exiftool {photo} | grep -i "GPS"
  #   exiftool {photo} | grep -i "Date"
  #   exiftool {photo} | grep -iE "(Make|Model)"
  # ════════════════════════════════════════════════════════════════
  echo ""
  echo -e "  ${BOLD}Phase 4 — EXIF & GPS Analysis (exiftool)${NC}"

  # exiftool | grep -i "GPS"
  info "exiftool $PHOTO | grep -i \"GPS\""
  GPS=$(exiftool "$CASE_DIR/$PHOTO" 2>/dev/null | grep -i "GPS Position" | head -1)
  GPS_LAT=$(exiftool "$CASE_DIR/$PHOTO" 2>/dev/null | grep -i "GPS Latitude " | grep -v "Ref" | head -1)
  if [[ -n "$GPS" ]]; then
    ok "  GPS Position: $(echo "$GPS" | cut -d: -f2- | xargs)"
  elif [[ -n "$GPS_LAT" ]]; then
    ok "  GPS Latitude: $(echo "$GPS_LAT" | cut -d: -f2- | xargs)"
  else
    fail "  exiftool: no GPS coordinates in $PHOTO — students cannot complete Phase 4"
  fi

  # exiftool | grep -i "Date"
  info "exiftool $PHOTO | grep -i \"Date\""
  DATE=$(exiftool "$CASE_DIR/$PHOTO" 2>/dev/null | grep -i "Date" | head -1)
  if [[ -n "$DATE" ]]; then
    ok "  Date: $(echo "$DATE" | cut -d: -f2- | xargs | cut -c1-40)"
  else
    fail "  exiftool: no Date metadata in $PHOTO"
  fi

  # exiftool | grep -iE "(Make|Model)"
  info "exiftool $PHOTO | grep -iE \"(Make|Model)\""
  MAKE=$(exiftool "$CASE_DIR/$PHOTO" 2>/dev/null | grep -iE "^Make|^Model|Software" | head -2)
  if [[ -n "$MAKE" ]]; then
    ok "  Device: $(echo "$MAKE" | head -1 | cut -d: -f2- | xargs)"
  else
    fail "  exiftool: no Make/Model/Software metadata in $PHOTO"
  fi

  # ════════════════════════════════════════════════════════════════
  # PHASE 5 — Network Artifact Analysis (strings)
  # Commands students run:
  #   strings {memfile} | grep -iE "(patient|SSN|...)"          ← industry
  #   strings {memfile} | grep -iE "(http|Content-Type|Authorization|Bearer|Transfer-Encoding)"
  #   strings {memfile} | grep -E "([0-9]{1,3}\.){3}[0-9]{1,3}"
  #   strings {memfile} | grep -iE "(dropbox|gdrive|onedrive|mega|upload|POST|PUT)"
  #   strings {memfile} | grep -iE "(http|Authorization|Content-Type|Transfer-Encoding|...)" | sort -u
  # ════════════════════════════════════════════════════════════════
  echo ""
  echo -e "  ${BOLD}Phase 5 — Network Artifact Analysis (strings)${NC}"

  # Industry-specific grep
  PAT=$(industry_grep "$LABEL")
  info "strings $MEMFILE | grep -iE \"$PAT\""
  IND_COUNT=$(strings "$CASE_DIR/$MEMFILE" | grep -ciE "$PAT" 2>/dev/null || echo 0)
  if [[ $IND_COUNT -gt 0 ]]; then
    SAMPLE=$(strings "$CASE_DIR/$MEMFILE" | grep -iE "$PAT" | head -1)
    ok "  Industry grep ($IND_COUNT hits): \"${SAMPLE:0:70}\""
  else
    warn "  Industry grep: 0 hits for pattern — check memory fragment content"
  fi

  # HTTP / network headers
  info "strings $MEMFILE | grep -iE \"(http|Content-Type|Authorization|Bearer|Transfer-Encoding)\""
  HTTP_COUNT=$(strings "$CASE_DIR/$MEMFILE" | grep -ciE "(http|Content-Type|Authorization|Bearer|Transfer-Encoding)" 2>/dev/null || echo 0)
  if [[ $HTTP_COUNT -gt 0 ]]; then
    ok "  HTTP/network strings: $HTTP_COUNT hits (Content-Type / Authorization / Transfer-Encoding present)"
  else
    fail "  HTTP strings: none found in $MEMFILE — check memory fragment"
  fi

  # IP addresses
  info "strings $MEMFILE | grep -E \"IP pattern\""
  IP_MATCH=$(strings "$CASE_DIR/$MEMFILE" | grep -oE "([0-9]{1,3}\.){3}[0-9]{1,3}" | head -1)
  if [[ -n "$IP_MATCH" ]]; then
    ok "  IP address found: $IP_MATCH  (X-Forwarded-For attacker IP)"
  else
    fail "  No IP address found in $MEMFILE"
  fi

  # JWT Bearer token
  info "strings $MEMFILE | grep -i \"Authorization: Bearer\""
  BEARER=$(strings "$CASE_DIR/$MEMFILE" | grep -i "Authorization: Bearer" | head -1)
  if [[ -n "$BEARER" ]]; then
    ok "  Bearer token: \"${BEARER:0:60}...\""
  else
    fail "  No Bearer/JWT token in $MEMFILE"
  fi

  # Cloud exfiltration strings (dropbox/gdrive/onedrive/mega)
  info "strings $MEMFILE | grep -iE \"(dropbox|gdrive|onedrive|mega|upload|POST|PUT)\""
  CLOUD_COUNT=$(strings "$CASE_DIR/$MEMFILE" | grep -ciE "(dropbox|gdrive|onedrive|mega|upload|POST|PUT)" 2>/dev/null || echo 0)
  if [[ $CLOUD_COUNT -gt 0 ]]; then
    SAMPLE=$(strings "$CASE_DIR/$MEMFILE" | grep -iE "(dropbox|gdrive|onedrive|mega|upload|POST|PUT)" | head -1)
    ok "  Cloud exfil strings: $CLOUD_COUNT hits — \"${SAMPLE:0:60}\""
  else
    warn "  Cloud exfil strings: 0 hits for dropbox/gdrive/onedrive/mega/upload/POST/PUT"
  fi

  # Comprehensive sort -u (Phase 5 final command)
  info "strings $MEMFILE | grep -iE \"(http|Authorization|Content-Type|Transfer-Encoding|IP)\" | sort -u"
  COMBINED=$(strings "$CASE_DIR/$MEMFILE" | grep -iE "(http|Authorization|Content-Type|Transfer-Encoding|([0-9]{1,3}\.){3})" | sort -u | wc -l)
  if [[ $COMBINED -gt 0 ]]; then
    ok "  Comprehensive sort -u: $COMBINED unique network artifact lines"
  else
    fail "  Comprehensive strings grep returned nothing"
  fi

  # ── Record result ────────────────────────────────────────────────────────────
  if [[ $CASE_FAIL -eq 0 ]]; then
    CASE_RESULTS[$LABEL]="PASS"
  else
    CASE_RESULTS[$LABEL]="FAIL($CASE_FAIL)"
  fi
done

# ── Cleanup downloaded zips ───────────────────────────────────────────────────
if [[ $SKIP_DOWNLOAD -eq 0 ]]; then
  echo ""
  info "Removing downloaded zip files (extracted folders kept in $EVIDENCE_ROOT/)"
  rm -f "$EVIDENCE_ROOT"/*_Evidence.zip
fi

# ── Final summary ─────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  FINAL SUMMARY — All 13 Cases, All 5 Phases${NC}"
echo -e "${BOLD}════════════════════════════════════════════════════════════════${NC}"
echo ""
printf "  %-12s  %-10s\n" "Case" "Result"
printf "  %-12s  %-10s\n" "────────────" "──────────"
for LABEL in HC_A HC_B HC_C FT_A FT_B FT_C MFG_A MFG_B MFG_C ECOM_A ECOM_B LEGAL_A LEGAL_B; do
  R=${CASE_RESULTS[$LABEL]:-"NOT RUN"}
  if   [[ "$R" == "PASS"     ]]; then printf "  %-12s  ${GREEN}✓ PASS${NC}\n"       "$LABEL"
  elif [[ "$R" == "NOT RUN"  ]]; then printf "  %-12s  ${YELLOW}⚠ SKIP${NC}\n"      "$LABEL"
  else                                printf "  %-12s  ${RED}✗ $R${NC}\n"           "$LABEL"
  fi
done
echo ""
TOTAL=$((TOTAL_PASS+TOTAL_FAIL))
echo -e "  Total individual checks : $TOTAL"
echo -e "  ${GREEN}Passed : $TOTAL_PASS${NC}"
echo -e "  ${RED}Failed : $TOTAL_FAIL${NC}"
[[ $TOTAL_WARN -gt 0 ]] && echo -e "  ${YELLOW}Warnings: $TOTAL_WARN${NC}"
echo ""
if [[ $TOTAL_FAIL -eq 0 ]]; then
  echo -e "  ${GREEN}${BOLD}✓ All phases validated. Evidence is ready for student distribution.${NC}"
else
  echo -e "  ${RED}${BOLD}✗ $TOTAL_FAIL check(s) failed. Review output above before distributing.${NC}"
  echo -e "  ${YELLOW}Most likely cause: steghide embedding not yet run (ent/info/extract will fail).${NC}"
  echo -e "  ${YELLOW}Run embed_steganography.sh on SIFT, re-zip, re-upload to GitHub, then re-test.${NC}"
fi
echo ""
echo -e "  Extracted evidence in: ${BOLD}$EVIDENCE_ROOT/${NC}"
echo ""
