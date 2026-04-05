#!/bin/bash
# =============================================================================
# BIT 4644 CAPSTONE - PROFESSOR EVIDENCE PREPARATION SCRIPT
# Run this on your SIFT Workstation to complete the steganographic evidence files
# =============================================================================
# INSTRUCTIONS:
#   1. Copy the entire evidence_sources/ folder to your SIFT desktop
#   2. cd ~/Desktop/evidence_sources
#   3. chmod +x PROFESSOR_SETUP.sh
#   4. ./PROFESSOR_SETUP.sh
#   5. Upload each <LABEL>/ folder to GitHub as a zip file
# =============================================================================

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "================================================================="
echo "  BIT 4644 Capstone Evidence Preparation"
echo "  Working directory: $SCRIPT_DIR"
echo "================================================================="

check_steghide() {
    if ! command -v steghide &>/dev/null; then
        echo "ERROR: steghide not found. On SIFT run: sudo apt-get install steghide"
        exit 1
    fi
    echo "steghide: $(steghide --version 2>&1 | head -1)"
}
check_steghide

embed() {
    local LABEL="$1"
    local CARRIER="$2"
    local PAYLOAD="$3"
    local PASSPHRASE="$4"

    local DIR="$SCRIPT_DIR/$LABEL"
    local CARRIER_PATH="$DIR/$CARRIER"
    local PAYLOAD_PATH="$DIR/$PAYLOAD"

    if [ ! -f "$CARRIER_PATH" ]; then
        echo "  [SKIP] $CARRIER not found in $DIR/"
        return
    fi
    if [ ! -f "$PAYLOAD_PATH" ]; then
        echo "  [SKIP] $PAYLOAD not found in $DIR/"
        return
    fi

    echo "  Embedding $PAYLOAD -> $CARRIER  (passphrase: $PASSPHRASE)"
    steghide embed -cf "$CARRIER_PATH" \
                   -sf "$PAYLOAD_PATH" \
                   -p "$PASSPHRASE" \
                   -f -q
    echo "  Done: $CARRIER now contains hidden $PAYLOAD"
}

# =============================================================================
# CASE 1: HEALTHCARE - Meridian Regional Medical Center
# =============================================================================
echo ""
echo "[CASE 1 - HEALTHCARE]"

echo "  Variant A: James Caldwell"
embed "HC_A" "backup_image_A.jpg"  "stolen_records_A.csv"  "M3ridian_2024!"

echo "  Variant B: Sarah Meyers"
embed "HC_B" "backup_image_B.jpg"  "patient_data_B.csv"    "H1paaV@ult_99"

echo "  Variant C: Robert Tran"
embed "HC_C" "backup_image_C.jpg"  "phi_extract_C.csv"     "P@tient_Trove7"

# =============================================================================
# CASE 2: FINTECH - Apex Capital Management
# =============================================================================
echo ""
echo "[CASE 2 - FINTECH]"

echo "  Variant A: Marcus Webb"
embed "FT_A" "server_backup_A.jpg" "delta7_algorithm.txt"  "Qu@ntAlpha_21"

echo "  Variant B: Diana Park"
embed "FT_B" "server_backup_B.jpg" "client_portfolio_B.csv" "T3rminal_Risk!"

echo "  Variant C: Kevin Osei"
embed "FT_C" "server_backup_C.jpg" "risk_model_C.txt"       "C@pital_F10w_X"

# =============================================================================
# CASE 3: MANUFACTURING - Wolverine Precision Components
# =============================================================================
echo ""
echo "[CASE 3 - MANUFACTURING]"

echo "  Variant A: Tyler Holt"
embed "MFG_A" "design_image_A.jpg" "cnc_specs_A.txt"        "W0lver1ne_Steal!"

echo "  Variant B: Angela Russo"
embed "MFG_B" "design_image_B.jpg" "alloy_formula_B.txt"    "C@dV@ult_Mfg22"

echo "  Variant C: Priya Nair"
embed "MFG_C" "design_image_C.jpg" "process_blueprint_C.txt" "Pr0cess_Secr3t!"

# =============================================================================
# CASE 4: E-COMMERCE - ShopSphere Inc.
# =============================================================================
echo ""
echo "[CASE 4 - E-COMMERCE]"

echo "  Variant A: Connor Walsh"
embed "ECOM_A" "product_backup_A.jpg" "card_dump_A.csv"     "Sph3re_Sk1m!"

echo "  Variant B: Lily Zhang"
embed "ECOM_B" "product_backup_B.jpg" "card_export_B.csv"   "D@tabase_L00t_22"

# =============================================================================
# CASE 5: LEGAL SERVICES - Hartwell & Associates LLP
# =============================================================================
echo ""
echo "[CASE 5 - LEGAL SERVICES]"

echo "  Variant A: Nathan Keller"
embed "LEGAL_A" "legal_backup_A.jpg"  "merger_docs_A.txt"   "H@rtw3ll_Vault!"

echo "  Variant B: Monica Cruz"
embed "LEGAL_B" "legal_backup_B.jpg"  "litigation_strategy_B.txt" "L3gal_L3ak_23"

# =============================================================================
# PACKAGE INTO ZIP FILES FOR GITHUB UPLOAD
# =============================================================================
echo ""
echo "================================================================="
echo "Packaging evidence bundles for GitHub upload..."
echo "================================================================="

for LABEL in HC_A HC_B HC_C FT_A FT_B FT_C MFG_A MFG_B MFG_C ECOM_A ECOM_B LEGAL_A LEGAL_B; do
    DIR="$SCRIPT_DIR/$LABEL"
    ZIP_NAME="${LABEL}_Evidence.zip"
    ZIP_PATH="$SCRIPT_DIR/$ZIP_NAME"

    # Only include files students need (NOT the hidden content plaintext)
    FILES_TO_ZIP=()
    cd "$DIR"
    for f in *.jpg *.raw; do
        [ -f "$f" ] && FILES_TO_ZIP+=("$f")
    done

    if [ ${#FILES_TO_ZIP[@]} -gt 0 ]; then
        zip -j "$ZIP_PATH" "${FILES_TO_ZIP[@]}" -q
        SIZE=$(du -sh "$ZIP_PATH" | cut -f1)
        echo "  Created: $ZIP_NAME  ($SIZE)"
    fi
    cd "$SCRIPT_DIR"
done

echo ""
echo "================================================================="
echo "UPLOAD CHECKLIST:"
echo "Upload each zip file to your GitHub repo:"
echo "  https://github.com/rajiraman1224/BIT4644-DFIR/tree/main/Capstone/"
echo ""
echo "Students will download with (example for HC_A):"
echo "  wget https://raw.githubusercontent.com/rajiraman1224/BIT4644-DFIR/main/Capstone/HC_A_Evidence.zip"
echo ""
echo "IMPORTANT: Do NOT upload the raw hidden content text files."
echo "The steghide-embedded JPEGs and memory .raw files are what students get."
echo "================================================================="
echo ""
echo "All done! Verify one embed worked:"
echo "  steghide info $SCRIPT_DIR/HC_A/backup_image_A.jpg"
